"""Console display and formatting utilities."""
from __future__ import annotations
from typing import Dict, List, Any
from colorama import Fore, Style, init

init(autoreset=True)

SEPARATOR = "-" * 60


def print_separator() -> None:
    print(f"{Fore.CYAN}{SEPARATOR}{Style.RESET_ALL}")


def print_header(text: str) -> None:
    print(f"{Fore.MAGENTA}{'=' * 20} {text} {'=' * 20}{Style.RESET_ALL}")


def print_info(label: str, value: str = "") -> None:
    print(f"{Fore.CYAN}[{label}]{Style.RESET_ALL} {value}")


def print_success(text: str) -> None:
    print(f"  {Fore.GREEN}{text}{Style.RESET_ALL}")


def print_error(text: str) -> None:
    print(f"  {Fore.RED}{text}{Style.RESET_ALL}")


def print_warning(text: str) -> None:
    print(f"{Fore.YELLOW}{text}{Style.RESET_ALL}")


def print_status_code(code: int | None) -> None:
    if code is None:
        return
    color = Fore.GREEN if 200 <= code < 300 else Fore.YELLOW if 300 <= code < 400 else Fore.RED
    print(f"{Fore.CYAN}[Status Code]{Style.RESET_ALL} {color}{code}{Style.RESET_ALL}")


def print_crawl_status(status: str, is_priority: bool = False, is_blocked: bool = False) -> None:
    color = Fore.RED if is_blocked else Fore.GREEN if is_priority else Fore.YELLOW
    print(f"{color}[Status]{Style.RESET_ALL} {status}")


# Status message constants
STATUS_PRIORITY = "Priority page"
STATUS_BLOCKED = "Blocked path (excluded)"
STATUS_OTHER = "Other page (not priority/excluded)"


def print_schema_check(checked: bool, found: bool, schema_count: int = 0) -> None:
    check_color = Fore.GREEN if checked else Fore.RED
    found_color = Fore.GREEN if found else Fore.RED
    print(f"{check_color}[Checked for schema]{Style.RESET_ALL} {checked}")
    if found and schema_count > 0:
        print(f"{found_color}[Found schema]{Style.RESET_ALL} {found} ({schema_count} schema{'s' if schema_count > 1 else ''})")
    else:
        print(f"{found_color}[Found schema]{Style.RESET_ALL} {found}")


def print_found_variables(found_vars: Dict[str, List[Any]], max_len: int = 100) -> None:
    if not found_vars:
        return
    print(f"{Fore.MAGENTA}[Variables found in schema:]{Style.RESET_ALL}")
    for var_name, values in found_vars.items():
        for value in values:
            display = str(value)
            if len(display) > max_len:
                display = display[:max_len] + "..."
            print(f"  {Fore.CYAN}{var_name}:{Style.RESET_ALL} {Fore.YELLOW}{display}{Style.RESET_ALL}")


def print_link_stats(total: int, new: int, external: int, queue_size: int) -> None:
    print(f"  {Fore.BLUE}[Links: {total} found, {new} new added, {external} external, {queue_size} in queue]{Style.RESET_ALL}")


def print_skipped(url: str, reason: str = "blocked") -> None:
    print(f"{Fore.YELLOW}[Skipped ({reason})]{Style.RESET_ALL} {url}")


def print_results(results: dict) -> None:
    """Print final scraping results summary."""
    import sys
    print_separator()
    sys.stdout.flush()
    print_header("SCRAPING RESULTS")
    sys.stdout.flush()
    print(f"{Fore.WHITE}Total pages crawled:{Style.RESET_ALL} {Fore.YELLOW}{results['total_pages_crawled']}{Style.RESET_ALL}")
    sys.stdout.flush()

    print(f"\n{Fore.GREEN}--- PRIORITY PAGES ---{Style.RESET_ALL}")
    sys.stdout.flush()
    print(f"{Fore.WHITE}Priority pages found:{Style.RESET_ALL} {Fore.YELLOW}{results['priority_pages_found']}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}With JSON-LD schema:{Style.RESET_ALL} {Fore.GREEN}{results['priority_pages_with_schema']}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Without schema:{Style.RESET_ALL} {Fore.RED}{results['priority_pages_without_schema']}{Style.RESET_ALL}")
    sys.stdout.flush()

    print(f"\n{Fore.YELLOW}--- REMAINING PAGES ---{Style.RESET_ALL}")
    sys.stdout.flush()
    print(f"{Fore.WHITE}Remaining pages found:{Style.RESET_ALL} {Fore.YELLOW}{results['remaining_pages_found']}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}With JSON-LD schema:{Style.RESET_ALL} {Fore.GREEN}{results['remaining_pages_with_schema']}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Without schema:{Style.RESET_ALL} {Fore.RED}{results['remaining_pages_without_schema']}{Style.RESET_ALL}")
    sys.stdout.flush()

    for label, key in [("Priority", "priority_schemas_found"), ("Remaining", "remaining_schemas_found")]:
        if results.get(key):
            print(f"\n{Fore.GREEN}{label} pages with schema:{Style.RESET_ALL}")
            for url in results[key]:
                print(f"  {Fore.CYAN}-{Style.RESET_ALL} {url}")
    sys.stdout.flush()