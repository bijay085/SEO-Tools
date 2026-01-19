"""JSON-LD schema extraction and business info extraction."""
from __future__ import annotations
import json
import re
import warnings
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", category=UserWarning, module="html.parser")

PHONE_PATTERN = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
LICENSE_PATTERN = re.compile(r'(?:license|lic|#)\s*[:#]?\s*([A-Z0-9-]+)', re.IGNORECASE)


def _get_soup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _is_schema_org(data: dict) -> bool:
    context = data.get("@context", "")
    return isinstance(context, str) and "schema.org" in context


def extract_json_ld_schemas(html: str) -> List[dict]:
    """Extract all JSON-LD schema.org schemas from HTML."""
    soup = _get_soup(html)
    schemas: List[dict] = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            content = script.string
            if not content:
                continue
            data = json.loads(content)
            if isinstance(data, dict) and _is_schema_org(data):
                schemas.append(data)
            elif isinstance(data, list):
                schemas.extend(item for item in data if isinstance(item, dict) and _is_schema_org(item))
        except (json.JSONDecodeError, AttributeError):
            continue

    return schemas


def search_variables(schemas: List[dict], variables: List[str]) -> Dict[str, List[Any]]:
    """Search for specific variables in schemas."""
    found: Dict[str, List[Any]] = {}

    def _search(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in variables and value not in found.get(key, []):
                    found.setdefault(key, []).append(value)
                if isinstance(value, (dict, list)):
                    _search(value)
        elif isinstance(obj, list):
            for item in obj:
                _search(item)

    for schema in schemas:
        _search(schema)
    return found


def extract_business_info(schemas: List[dict], html: str, base_url: str) -> Dict[str, Any]:
    """
    Extract business information from schemas and HTML.
    Returns dict with: rating, review_count, address, areas_served, hours, 
    phone, quote_url, services, has_coupon, has_emergency, is_licensed
    """
    info = {
        "rating": None,
        "review_count": None,
        "addresses": [],
        "areas_served": [],
        "hours": "",
        "phones": [],
        "quote_url": "",
        "services": [],
        "has_coupon": False,
        "has_emergency": False,
        "is_licensed": False,
        "license_number": "",
        "business_name": "",
        "founding_date": "",
        "founders": [],
    }
    
    # Extract from schemas
    _extract_from_schemas(schemas, info)
    
    # Extract from HTML
    _extract_from_html(html, base_url, info)
    
    return info


def merge_business_info(accumulated: Dict[str, Any], page_info: Dict[str, Any]) -> None:
    """
    Merge page_info into accumulated business info.
    Combines lists, keeps best values, and merges boolean flags.
    """
    # Merge lists - add unique items
    for key in ["addresses", "areas_served", "phones", "services"]:
        if key in page_info and isinstance(page_info[key], list):
            for item in page_info[key]:
                if item and item not in accumulated[key]:
                    accumulated[key].append(item)
    
    # Merge strings - keep first non-empty value
    for key in ["hours", "quote_url", "license_number", "business_name", "founding_date"]:
        if key in page_info and page_info[key] and not accumulated[key]:
            accumulated[key] = page_info[key]
    
    # Merge founders list - add unique founders
    if "founders" in page_info and isinstance(page_info["founders"], list):
        for founder in page_info["founders"]:
            if isinstance(founder, dict) and founder.get("name"):
                # Check if founder already exists
                if not any(f["name"] == founder["name"] for f in accumulated.get("founders", [])):
                    accumulated.setdefault("founders", []).append(founder)
    
    # Merge booleans - use OR logic
    for key in ["has_coupon", "has_emergency", "is_licensed"]:
        if key in page_info:
            accumulated[key] = accumulated[key] or page_info[key]
    
    # Merge numbers - keep best/highest value
    if "rating" in page_info and page_info["rating"] is not None:
        if accumulated["rating"] is None or page_info["rating"] > accumulated["rating"]:
            accumulated["rating"] = page_info["rating"]
    
    if "review_count" in page_info and page_info["review_count"] is not None:
        if accumulated["review_count"] is None or page_info["review_count"] > accumulated["review_count"]:
            accumulated["review_count"] = page_info["review_count"]


def _extract_from_schemas(schemas: List[dict], info: Dict) -> None:
    """Extract business info from JSON-LD schemas."""
    for schema in schemas:
        # Business name
        if not info["business_name"]:
            stype = schema.get("@type", "")
            # Handle @type as string or array
            if isinstance(stype, list):
                stype_list = stype
            elif isinstance(stype, str):
                stype_list = [stype]
            else:
                stype_list = []
            
            # Skip WebPage, WebSite, BreadcrumbList types
            skip_types = {"WebPage", "WebSite", "BreadcrumbList"}
            if not any(t in skip_types for t in stype_list):
                name = schema.get("name")
                if name:
                    info["business_name"] = str(name)
        
        # Rating & Reviews
        agg = schema.get("aggregateRating", {})
        if isinstance(agg, dict):
            if info["rating"] is None and "ratingValue" in agg:
                try:
                    info["rating"] = float(agg["ratingValue"])
                except (ValueError, TypeError):
                    pass
            if info["review_count"] is None:
                for key in ["reviewCount", "ratingCount"]:
                    if key in agg:
                        try:
                            info["review_count"] = int(str(agg[key]).replace(",", ""))
                            break
                        except (ValueError, TypeError):
                            pass
        
        # Address
        addr = schema.get("address")
        if addr:
            addr_str = _parse_address(addr)
            if addr_str and addr_str not in info["addresses"]:
                info["addresses"].append(addr_str)
        
        # Phone
        for key in ["telephone", "phone", "contactPhone"]:
            val = schema.get(key)
            if val and val not in info["phones"]:
                info["phones"].append(str(val))
        
        # Contact points
        contacts = schema.get("contactPoint", [])
        if isinstance(contacts, dict):
            contacts = [contacts]
        for cp in contacts:
            if isinstance(cp, dict) and cp.get("telephone"):
                phone = cp["telephone"]
                if phone not in info["phones"]:
                    info["phones"].append(phone)
        
        # Areas Served
        for key in ["areaServed", "serviceArea", "areasServed"]:
            val = schema.get(key)
            areas = _parse_areas(val)
            for area in areas:
                if area not in info["areas_served"]:
                    info["areas_served"].append(area)
        
        # Hours
        if not info["hours"]:
            info["hours"] = _parse_hours(schema)
            if "24" in info["hours"]:
                info["has_emergency"] = True
        
        # Services
        services = _parse_services(schema)
        for svc in services:
            if svc not in info["services"]:
                info["services"].append(svc)
        
        # Founding Date
        if not info["founding_date"]:
            founding_date = schema.get("foundingDate")
            if founding_date:
                info["founding_date"] = str(founding_date)
        
        # Founders
        founders = schema.get("founder", [])
        if isinstance(founders, dict):
            founders = [founders]
        for founder in founders:
            if isinstance(founder, dict):
                founder_name = founder.get("name")
                if founder_name:
                    founder_info = {
                        "name": str(founder_name),
                        "job_title": founder.get("jobTitle", ""),
                    }
                    # Check if this founder is already in the list
                    if not any(f["name"] == founder_info["name"] for f in info["founders"]):
                        info["founders"].append(founder_info)


def _parse_address(addr) -> str:
    """Parse address from schema format."""
    if isinstance(addr, str):
        return addr
    if isinstance(addr, dict):
        parts = []
        for key in ["streetAddress", "addressLocality", "addressRegion", "postalCode"]:
            val = addr.get(key)
            if val:
                parts.append(str(val))
        return ", ".join(parts)
    return ""


def _parse_areas(val) -> List[str]:
    """Parse areas served from schema format."""
    areas = []
    if isinstance(val, str):
        areas.append(val)
    elif isinstance(val, list):
        for v in val:
            if isinstance(v, str):
                areas.append(v)
            elif isinstance(v, dict):
                name = v.get("name") or v.get("addressLocality")
                if name:
                    areas.append(str(name))
    elif isinstance(val, dict):
        name = val.get("name") or val.get("addressLocality")
        if name:
            areas.append(str(name))
    return areas


def _parse_hours(schema: dict) -> str:
    """Parse business hours from schema."""
    # Simple openingHours
    oh = schema.get("openingHours")
    if isinstance(oh, str):
        if "24" in oh.lower() or "always" in oh.lower():
            return "24/7"
        return oh
    if isinstance(oh, list):
        if any("24" in str(h).lower() for h in oh):
            return "24/7"
        return ", ".join(str(h) for h in oh)
    
    # Detailed openingHoursSpecification
    ohs = schema.get("openingHoursSpecification", [])
    if isinstance(ohs, dict):
        ohs = [ohs]
    
    day_hours = {}
    for spec in ohs:
        if not isinstance(spec, dict):
            continue
        days = spec.get("dayOfWeek", [])
        if isinstance(days, str):
            days = [days]
        opens = spec.get("opens", "")
        closes = spec.get("closes", "")
        
        if opens and closes:
            time_str = f"{opens} - {closes}"
            for day in days:
                day_name = day.replace("https://schema.org/", "").replace("http://schema.org/", "")
                day_hours[day_name] = time_str
    
    if day_hours:
        return ", ".join(f"{d}: {t}" for d, t in day_hours.items())
    return ""


def _parse_services(schema: dict) -> List[str]:
    """Parse services from schema."""
    services = []
    
    # hasOfferCatalog
    catalog = schema.get("hasOfferCatalog", {})
    if isinstance(catalog, dict):
        items = catalog.get("itemListElement", [])
        for item in items:
            if isinstance(item, dict):
                name = item.get("name")
                if not name:
                    offered = item.get("itemOffered", {})
                    if isinstance(offered, dict):
                        name = offered.get("name")
                if name:
                    services.append(str(name))
    
    # makesOffer
    offers = schema.get("makesOffer", [])
    if isinstance(offers, dict):
        offers = [offers]
    for offer in offers:
        if isinstance(offer, dict):
            name = offer.get("name")
            if not name:
                offered = offer.get("itemOffered", {})
                if isinstance(offered, dict):
                    name = offered.get("name")
            if name:
                services.append(str(name))
    
    # Service type schema
    if schema.get("@type") == "Service":
        name = schema.get("name")
        if name:
            services.append(str(name))
    
    return services


def _extract_from_html(html: str, base_url: str, info: Dict) -> None:
    """Extract business info from HTML content."""
    soup = _get_soup(html)
    text = soup.get_text(separator=" ", strip=True).lower()
    
    # Phones from HTML
    if not info["phones"]:
        phones = PHONE_PATTERN.findall(soup.get_text())
        info["phones"] = list(set(phones[:5]))
    
    # Quote/Contact URL
    if not info["quote_url"]:
        for a in soup.find_all("a", href=True):
            link_text = a.get_text(strip=True).lower()
            href = a.get("href", "")
            
            if any(w in link_text for w in ["quote", "free estimate", "get estimate", "request"]):
                info["quote_url"] = _make_absolute_url(href, base_url)
                break
            elif "contact" in link_text and not info["quote_url"]:
                info["quote_url"] = _make_absolute_url(href, base_url)
    
    # Coupon/Offer check
    if not info["has_coupon"]:
        for a in soup.find_all("a", href=True):
            link_text = a.get_text(strip=True).lower()
            if any(w in link_text for w in ["coupon", "offer", "discount", "special", "deal", "promo"]):
                info["has_coupon"] = True
                break
    
    # Emergency service check
    if not info["has_emergency"]:
        emergency_keywords = ["24/7", "24 hour", "emergency service", "emergency repair", 
                            "available 24", "always available", "round the clock"]
        for kw in emergency_keywords:
            if kw in text:
                info["has_emergency"] = True
                if "24" in kw and not info["hours"]:
                    info["hours"] = "24/7"
                break
    
    # License check
    if not info["is_licensed"]:
        license_keywords = ["licensed", "license #", "license:", "lic #", "lic.", 
                          "contractor license", "state license", "bonded", "insured"]
        for kw in license_keywords:
            if kw in text:
                info["is_licensed"] = True
                match = LICENSE_PATTERN.search(soup.get_text())
                if match:
                    info["license_number"] = match.group(1)
                break


def _make_absolute_url(href: str, base_url: str) -> str:
    """Convert relative URL to absolute."""
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    elif href.startswith("http"):
        return href
    return ""


def format_business_report(info: Dict) -> str:
    """Format business info as a report string."""
    lines = [
        f"Rating: {info['rating']}/5" if info['rating'] else "Rating: N/A",
        f"Review: {info['review_count']:,}" if info['review_count'] else "Review: N/A",
        f"Address: {info['addresses'][0]}" if info['addresses'] else "Address: N/A",
        f"Areas Served: {', '.join(info['areas_served'])}" if info['areas_served'] else "Areas Served: N/A",
        f"Hours: {info['hours']}" if info['hours'] else "Hours: N/A",
        f"Phone: {', '.join(info['phones'])}" if info['phones'] else "Phone: N/A",
        f"Get a Quote: {info['quote_url']}" if info['quote_url'] else "Get a Quote: N/A",
        f"Services: {', '.join(info['services'])}" if info['services'] else "Services: N/A",
        f"Offer/Coupon: {'Available' if info['has_coupon'] else 'Not Available'}",
        f"24/7 Emergency Service: {'Yes' if info['has_emergency'] else 'No'}",
        f"Licensed: {'Yes' + (' (' + info['license_number'] + ')' if info.get('license_number') else '') if info['is_licensed'] else 'No'}",
    ]
    
    # Add founding date if available
    if info.get('founding_date'):
        lines.append(f"Founding Date: {info['founding_date']}")
    
    # Add founders if available
    if info.get('founders'):
        founders_list = []
        for founder in info['founders']:
            founder_str = founder.get('name', '')
            if founder.get('job_title'):
                founder_str += f" ({founder['job_title']})"
            founders_list.append(founder_str)
        if founders_list:
            lines.append(f"Founder(s): {', '.join(founders_list)}")
    
    return "\n".join(lines)