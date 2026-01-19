# 🔍 Local Business SEO Scraper

A Python-based web scraper designed to extract structured business information from local business websites. It parses JSON-LD schema markup and HTML content to gather SEO-relevant data like ratings, reviews, contact info, services, and more.

---

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Output Fields](#-output-fields)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Examples](#-examples)
- [Dependencies](#-dependencies)
- [License](#-license)

---

## ✨ Features

- **JSON-LD Schema Extraction** - Automatically parses structured data from websites
- **HTML Fallback** - Extracts info from HTML when schema is unavailable
- **Two Scan Modes**:
  - **Quick Scan** - Scrapes only key pages (homepage, about, contact, services)
  - **Full Crawl** - Crawls entire website with configurable exclusions
- **Business Info Report** - Generates formatted report with all extracted data
- **Configurable** - Exclude/prioritize paths via JSON config
- **Export Options** - Save results as JSON or CSV

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/local-business-scraper.git
cd local-business-scraper

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### requirements.txt

```
requests>=2.28.0
beautifulsoup4>=4.11.0
lxml>=4.9.0
colorama>=0.4.6
```

---

## 💻 Usage

### Basic Usage

```bash
python main.py
```

```
============================================================
       LOCAL BUSINESS SEO SCRAPER
============================================================

Enter website URL (e.g. https://example.com): https://bakerbrothersplumbing.com

Options:
  1. Quick scan (homepage, about, contact only) - FAST
  2. Full crawl (all pages) - SLOW but thorough

Select option (1 or 2): 1
```

### Programmatic Usage

```python
from modules.crawler import scrape_business, scrape_priority_paths

# Quick scan - key pages only
business_info = scrape_business("https://example.com")

# Full crawl - all pages
results = scrape_priority_paths("https://example.com", max_pages=500)
```

---

## 📊 Output Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Rating** | Average rating out of 5 | `4.9/5` |
| **Review** | Total review count | `24,176` |
| **Address** | Full business address(es) | `2615 Big Town Blvd, Mesquite, TX 75150` |
| **Areas Served** | Service locations | `Dallas, Rockwall County, Kaufman County` |
| **Hours** | Operating hours | `24/7` or `Monday-Friday: 8AM-6PM` |
| **Phone** | Contact number(s) | `(214) 324-8811` |
| **Get a Quote** | Quote/contact page URL | `https://example.com/contact` |
| **Services** | List of services offered | `drain cleaning, water heaters, plumbing` |
| **Offer/Coupon** | Coupon availability | `Available` / `Not Available` |
| **24/7 Emergency** | Emergency service availability | `Yes` / `No` |
| **Licensed** | License status | `Yes` / `No` (with license # if found) |

---

## 📁 Project Structure

```
local-business-scraper/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
│
├── modules/
│   ├── __init__.py            # Package exports
│   ├── config.py              # Configuration loader
│   ├── url_utils.py           # URL normalization utilities
│   ├── link_extractor.py      # HTML link extraction
│   ├── schema_extractor.py    # JSON-LD & business info extraction
│   ├── file_handler.py        # Save HTML/JSON files
│   ├── crawler.py             # Core crawling logic
│   ├── display.py             # Console output formatting
│   │
│   └── config/
│       └── scraper.json       # Scraper configuration
│
├── scraped_pages/             # Saved HTML & schema files (auto-created)
└── results/                   # Export directory (auto-created)
```

---

## ⚙️ Configuration

Edit `modules/config/scraper.json` to customize scraping behavior:

### Exclude Paths

Pages starting with these paths will be skipped:

```json
{
  "exclude_paths": [
    "/products",
    "/cart",
    "/checkout",
    "/blog",
    "/wp-admin"
  ]
}
```

### Priority Paths

Pages containing these paths are prioritized for business info extraction:

```json
{
  "priority_paths": [
    "/",
    "/about",
    "/about-us",
    "/contact",
    "/services",
    "/reviews"
  ]
}
```

### Variables to Extract

Schema fields to search for:

```json
{
  "variables": [
    "@type",
    "name",
    "telephone",
    "address",
    "aggregateRating",
    "areaServed",
    "openingHours"
  ]
}
```

---

## 📝 Examples

### Example Output

```
============================================================
BUSINESS INFORMATION REPORT
============================================================
Rating: 4.9/5
Review: 24,176
Address: 2615 Big Town Blvd, Mesquite, TX 75150
Areas Served: Dallas, Rockwall County, Kaufman County, Denton County, Ellis County, Collin County
Hours: 24/7
Phone: (214) 324-8811
Get a Quote: https://bakerbrothersplumbing.com/contact
Services: drain cleaning, water heaters, trenchless sewer repair, water filtration, gas lines
Offer/Coupon: Available
24/7 Emergency Service: Yes
Licensed: Yes (TECL 17060)
============================================================
```

### Export to JSON

```python
import json
from modules.crawler import scrape_business

info = scrape_business("https://example.com")

with open("results/business.json", "w") as f:
    json.dump(info, f, indent=2)
```

### Batch Processing

```python
from modules.crawler import scrape_business

websites = [
    "https://business1.com",
    "https://business2.com",
    "https://business3.com",
]

results = []
for url in websites:
    info = scrape_business(url)
    info["website"] = url
    results.append(info)
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | >=2.28.0 | HTTP requests |
| `beautifulsoup4` | >=4.11.0 | HTML parsing |
| `lxml` | >=4.9.0 | Fast XML/HTML parser |
| `colorama` | >=0.4.6 | Colored terminal output |

---

## 🔧 Troubleshooting

### Common Issues

**1. No schema found on pages**
- Not all websites use JSON-LD schema markup
- The scraper will fall back to HTML extraction

**2. Missing data in report**
- Some fields may not be available on the website
- Check if the website has the information publicly available

**3. Connection errors**
- Check your internet connection
- Some websites may block automated requests
- Try increasing `REQUEST_TIMEOUT` in `crawler.py`

**4. Blocked pages not being excluded**
- Ensure paths in `exclude_paths` start with `/`
- Check for trailing slashes

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

---

## 👨‍💻 Author

Your Name - [GitHub](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- [Schema.org](https://schema.org/) - Structured data vocabulary
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing library
