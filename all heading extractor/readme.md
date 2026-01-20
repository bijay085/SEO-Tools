# Site Heading Extractor

A simple Python tool to extract all headings (H1-H6) from any website. Perfect for SEO analysis and content structure review.

## Features

- Extracts all headings (H1, H2, H3, H4, H5, H6) from a webpage
- **Multiple URLs support** - Process multiple websites at once (comma-separated)
- **Filter by heading level** - Extract only specific heading levels (e.g., H1 and H2 only)
- **Better error handling** - Specific error messages for connection issues, timeouts, HTTP errors
- **Smart file handling** - Automatically adds timestamps to prevent overwriting existing files
- Displays headings in a clean, organized format
- Option to save results to a text file with metadata (URL, timestamp, count)
- Automatically handles URLs with or without protocol (http/https)
- User-friendly command-line interface

## Requirements

- Python 3.6 or higher
- `requests` library
- `beautifulsoup4` library

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests beautifulsoup4
```

## Usage

Run the script:

```bash
python main.py
```

When prompted:
1. Enter the URL(s) of the website(s) you want to analyze (comma-separated for multiple)
2. Optionally filter by heading levels (e.g., `h1,h2` or press Enter for all)
3. The script will display all headings found on each page
4. Optionally save the results to a text file

### Examples

#### Single URL - All Headings
```
Enter URL(s) (comma-separated for multiple): example.com
Filter by heading levels? (e.g., h1,h2 or press Enter for all): 

Processing: https://example.com
✓ Found 5 heading(s):

  [H1] Welcome to Example
  [H2] About Us
  [H2] Services
  [H3] Web Development
  [H3] SEO Services

Save to file(s)? (y/n): y
Filename (press Enter for auto-generated): 
✓ Saved to example.com_headings.txt
```

#### Multiple URLs
```
Enter URL(s) (comma-separated for multiple): example.com, google.com, github.com
Filter by heading levels? (e.g., h1,h2 or press Enter for all): 

Processing: https://example.com
✓ Found 3 heading(s): ...

Processing: https://google.com
✓ Found 2 heading(s): ...

Save to file(s)? (y/n): y
✓ Saved https://example.com to example.com_headings.txt
✓ Saved https://google.com to google.com_headings.txt
```

#### Filter by Heading Level
```
Enter URL(s) (comma-separated for multiple): example.com
Filter by heading levels? (e.g., h1,h2 or press Enter for all): h1,h2
Filtering for: H1, H2

Processing: https://example.com
✓ Found 3 heading(s):

  [H1] Welcome to Example
  [H2] About Us
  [H2] Services
```

## Output Format

Headings are displayed and saved in the following format:
```
[TAG] Heading Text
```

Where `TAG` is the heading level (H1, H2, H3, etc.) and `Heading Text` is the actual heading content.

When saved to a file, the output includes metadata:
```
Headings extracted from: https://example.com
Extracted on: 2024-01-15 14:30:45
Total headings: 5
------------------------------------------------------------

[H1] Welcome to Example
[H2] About Us
...
```

### File Naming

- If a filename is provided and the file already exists, a timestamp is automatically appended (e.g., `headings_20240115_143045.txt`)
- If no filename is provided, it's auto-generated from the domain name (e.g., `example.com_headings.txt`)
- For multiple URLs, each URL gets its own file with an auto-generated name

## Error Handling

The tool provides specific error messages for different scenarios:
- **Timeout errors**: When a request takes longer than 10 seconds
- **Connection errors**: When the website is unreachable or internet connection fails
- **HTTP errors**: When the server returns an error status (404, 500, etc.)
- **Invalid URLs**: When the URL format is incorrect

## Notes

- The script uses a standard User-Agent header to avoid being blocked by some websites
- Request timeout is set to 10 seconds
- Only headings with actual text content are extracted (empty headings are ignored)
- Files are automatically timestamped to prevent accidental overwriting
- Multiple URLs are processed sequentially (one at a time)

## License

This project is open source and available for personal and commercial use.
