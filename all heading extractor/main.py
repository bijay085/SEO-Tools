"""
Site Heading Extractor

A simple tool to extract all headings (H1-H6) from any website.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

def extract_headings(url, heading_levels=None):
    """
    Extract all headings from a webpage.
    
    Args:
        url (str): The URL of the webpage to extract headings from
        heading_levels (list, optional): List of heading levels to extract (e.g., ['h1', 'h2']). 
                                        If None, extracts all levels (h1-h6).
        
    Returns:
        tuple: (headings list, error message). headings is a list of dicts with 'tag' and 'text' keys,
               or None if error occurs. error is None if successful.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # Determine which heading tags to extract
        if heading_levels:
            tags_to_find = [level.lower() for level in heading_levels if level.lower() in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']]
            if not tags_to_find:
                return None, "Invalid heading levels specified. Use h1, h2, h3, h4, h5, or h6."
        else:
            tags_to_find = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        
        headings = []
        for h in soup.find_all(tags_to_find):
            text = ' '.join(h.get_text().split())
            if text:
                headings.append({'tag': h.name.upper(), 'text': text})
        return headings, None
        
    except requests.exceptions.Timeout:
        return None, f"Timeout error: Request to {url} timed out after 10 seconds."
    except requests.exceptions.ConnectionError:
        return None, f"Connection error: Could not connect to {url}. Check your internet connection or the URL."
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP error: {e.response.status_code} - {e.response.reason} for {url}"
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {str(e)} for {url}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)} for {url}"

def get_unique_filename(base_filename):
    """
    Generate a unique filename with timestamp if file already exists.
    
    Args:
        base_filename (str): The base filename
        
    Returns:
        str: A unique filename
    """
    if not os.path.exists(base_filename):
        return base_filename
    
    # Split filename and extension
    name, ext = os.path.splitext(base_filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"{name}_{timestamp}{ext}"
    
    return new_filename

def save_headings(headings, url, base_filename=None):
    """
    Save headings to a file with timestamp and prevent overwriting.
    
    Args:
        headings (list): List of heading dictionaries
        url (str): The URL that was processed
        base_filename (str, optional): Base filename. If None, generates from URL.
        
    Returns:
        str: The filename that was used
    """
    if base_filename is None:
        # Generate filename from URL
        domain = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_')
        domain = ''.join(c for c in domain if c.isalnum() or c in ('_', '-', '.'))[:50]
        base_filename = f"{domain}_headings.txt"
    
    # Ensure .txt extension
    if not base_filename.endswith('.txt'):
        base_filename += '.txt'
    
    # Get unique filename
    filename = get_unique_filename(base_filename)
    
    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Headings extracted from: {url}\n")
        f.write(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total headings: {len(headings)}\n")
        f.write("-" * 60 + "\n\n")
        for h in headings:
            f.write(f"[{h['tag']}] {h['text']}\n")
    
    return filename

def process_url(url, heading_levels=None):
    """
    Process a single URL and extract headings.
    
    Args:
        url (str): The URL to process
        heading_levels (list, optional): List of heading levels to filter
        
    Returns:
        tuple: (headings list, success bool)
    """
    # Normalize URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print(f"\nProcessing: {url}")
    headings, error = extract_headings(url, heading_levels)
    
    if error:
        print(f"❌ {error}")
        return None, False
    
    if not headings:
        print("⚠️  No headings found.")
        return None, False
    
    return headings, True

def main():
    """
    Main function to run the heading extractor tool.
    Prompts user for URLs, extracts headings, and optionally saves to file.
    """
    print("=" * 60)
    print("Site Heading Extractor")
    print("=" * 60)
    
    # Get URLs (support multiple URLs separated by commas)
    urls_input = input("\nEnter URL(s) (comma-separated for multiple): ").strip()
    if not urls_input:
        print("No URL provided.")
        return
    
    urls = [url.strip() for url in urls_input.split(',') if url.strip()]
    
    # Get heading level filter
    filter_input = input("Filter by heading levels? (e.g., h1,h2 or press Enter for all): ").strip()
    heading_levels = None
    if filter_input:
        heading_levels = [level.strip().upper() for level in filter_input.split(',')]
        print(f"Filtering for: {', '.join(heading_levels)}")
    
    # Process each URL
    all_results = []
    for url in urls:
        headings, success = process_url(url, heading_levels)
        if success:
            print(f"✓ Found {len(headings)} heading(s):\n")
            for h in headings:
                print(f"  [{h['tag']}] {h['text']}")
            all_results.append((url, headings))
        print()
    
    if not all_results:
        print("No headings were extracted from any URL.")
        return
    
    # Save to file option
    if input("Save to file(s)? (y/n): ").strip().lower() == 'y':
        if len(all_results) == 1:
            # Single URL - ask for filename
            url, headings = all_results[0]
            filename_input = input(f"Filename (press Enter for auto-generated): ").strip()
            filename = save_headings(headings, url, filename_input if filename_input else None)
            print(f"✓ Saved to {filename}")
        else:
            # Multiple URLs - save each separately
            for url, headings in all_results:
                filename = save_headings(headings, url)
                print(f"✓ Saved {url} to {filename}")

if __name__ == "__main__":
    main()