"""Main entry point for the web scraper."""
from urllib.parse import urlparse
from modules.crawler import scrape_priority_paths, scrape_business
from modules.display import print_info, print_separator, print_results
from modules.exporter import export_json, export_csv, export_excel, export_crawl_results
from modules.logger import default_logger as logger


def main() -> None:
    """Run the web scraper."""
    print("\n" + "=" * 60)
    print("       LOCAL BUSINESS SEO SCRAPER")
    print("=" * 60)
    
    try:
        start_url = input("\nEnter website URL (e.g. https://example.com): ").strip()
        if not start_url:
            print("No URL provided, exiting.")
            logger.warning("No URL provided by user")
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
            logger.info(f"Starting quick scan for {domain}")
            business_info = scrape_business(start_url)
            
            # Ask about export
            export_choice = input("\nExport results? (json/csv/excel/all/n): ").strip().lower()
            if export_choice in ["json", "all"]:
                try:
                    filepath = export_json(business_info, f"business_{domain.replace('.', '_')}")
                    print(f"\n✓ Exported to: {filepath}")
                    logger.info(f"Exported JSON to {filepath}")
                except Exception as e:
                    print(f"\n✗ Error exporting JSON: {e}")
                    logger.error(f"Error exporting JSON: {e}", exc_info=True)
            
            if export_choice in ["csv", "all"]:
                try:
                    filepath = export_csv(business_info, f"business_{domain.replace('.', '_')}")
                    print(f"✓ Exported to: {filepath}")
                    logger.info(f"Exported CSV to {filepath}")
                except Exception as e:
                    print(f"✗ Error exporting CSV: {e}")
                    logger.error(f"Error exporting CSV: {e}", exc_info=True)
            
            if export_choice in ["excel", "all"]:
                try:
                    filepath = export_excel(business_info, f"business_{domain.replace('.', '_')}")
                    print(f"✓ Exported to: {filepath}")
                    logger.info(f"Exported Excel to {filepath}")
                except ImportError as e:
                    print(f"✗ Excel export requires openpyxl. Install with: pip install openpyxl")
                    logger.warning(f"Excel export failed: {e}")
                except Exception as e:
                    print(f"✗ Error exporting Excel: {e}")
                    logger.error(f"Error exporting Excel: {e}", exc_info=True)
        else:
            # Full crawl
            domain = urlparse(start_url).netloc
            logger.info(f"Starting full crawl for {domain}")
            print_info("Starting full crawl at", domain)
            print_separator()
            
            results = scrape_priority_paths(start_url)
            print_results(results)
            
            # Ask about export
            export_choice = input("\nExport results? (json/n): ").strip().lower()
            if export_choice == "json":
                try:
                    filepath = export_crawl_results(results, f"crawl_{domain.replace('.', '_')}")
                    print(f"\n✓ Exported to: {filepath}")
                    logger.info(f"Exported crawl results to {filepath}")
                except Exception as e:
                    print(f"\n✗ Error exporting results: {e}")
                    logger.error(f"Error exporting crawl results: {e}", exc_info=True)
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        logger.info("Operation cancelled by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}", exc_info=True)


if __name__ == "__main__":
    main()