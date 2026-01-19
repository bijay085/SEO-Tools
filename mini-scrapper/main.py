"""Main entry point for the web scraper."""
from urllib.parse import urlparse
from modules.crawler import scrape_priority_paths, scrape_business
from modules.display import print_info, print_separator, print_results


def main() -> None:
    """Run the web scraper."""
    print("\n" + "=" * 60)
    print("       LOCAL BUSINESS SEO SCRAPER")
    print("=" * 60)
    
    start_url = input("\nEnter website URL (e.g. https://example.com): ").strip()
    if not start_url:
        print("No URL provided, exiting.")
        return
    
    # Extract domain and always start from homepage
    if not start_url.startswith(("http://", "https://")):
        start_url = "https://" + start_url
    
    # Parse and extract just the domain
    parsed = urlparse(start_url)
    domain = parsed.netloc or start_url.split('/')[0].replace('https://', '').replace('http://', '')
    
    # Always start from homepage (domain root)
    start_url = f"https://{domain}/"
    
    print("\nOptions:")
    print("  1. Quick scan (homepage, about, contact only) - FAST")
    print("  2. Full crawl (all pages) - SLOW but thorough")
    
    choice = input("\nSelect option (1 or 2): ").strip()
    
    if choice == "1":
        # Quick business info scan
        scrape_business(start_url)
    else:
        # Full crawl
        domain = urlparse(start_url).netloc
        print_info("Starting full crawl at", domain)
        print_separator()
        
        results = scrape_priority_paths(start_url)
        print_results(results)


if __name__ == "__main__":
    main()