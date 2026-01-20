"""JSON-LD schema extraction and business info extraction - Enhanced Version."""
from __future__ import annotations
import json
import re
import warnings
from typing import List, Dict, Any, Optional, Set
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

warnings.filterwarnings("ignore", category=UserWarning, module="html.parser")

# Enhanced phone patterns - multiple formats
PHONE_PATTERNS = [
    re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),  # US standard
    re.compile(r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),  # International
    re.compile(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'),  # Without parentheses
    re.compile(r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}'),  # With parentheses
    re.compile(r'\d{10}'),  # 10 digits only
]

# Email pattern
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

# License pattern
LICENSE_PATTERN = re.compile(r'(?:license|lic|#)\s*[:#]?\s*([A-Z0-9-]+)', re.IGNORECASE)

# Social media domains
SOCIAL_DOMAINS = {
    'facebook.com', 'fb.com', 'facebook',
    'twitter.com', 'x.com', 'twitter',
    'instagram.com', 'instagram',
    'linkedin.com', 'linkedin',
    'youtube.com', 'youtube',
    'pinterest.com', 'pinterest',
    'tiktok.com', 'tiktok',
    'snapchat.com', 'snapchat',
}


def _get_soup(html: str) -> BeautifulSoup:
    """Create BeautifulSoup instance with best available parser."""
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _is_schema_org(data: dict) -> bool:
    """Check if data is a schema.org schema."""
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
    Extract comprehensive business information from schemas and HTML.
    Returns enhanced dict with many more fields.
    """
    info = {
        # Basic info
        "business_name": "",
        "description": "",
        "website": "",
        "logo": "",
        "images": [],
        
        # Contact info
        "rating": None,
        "review_count": None,
        "addresses": [],
        "address_components": [],  # Full address breakdown
        "areas_served": [],
        "hours": "",
        "phones": [],
        "emails": [],
        "quote_url": "",
        
        # Business details
        "services": [],
        "categories": [],
        "price_range": "",
        "payment_methods": [],
        "languages": [],
        
        # Flags
        "has_coupon": False,
        "has_emergency": False,
        "is_licensed": False,
        "license_number": "",
        
        # Additional
        "founding_date": "",
        "founders": [],
        "social_media": {},
        "meta_description": "",
        "meta_keywords": [],
    }
    
    # Extract from schemas first (most reliable)
    _extract_from_schemas(schemas, info)
    
    # Extract from HTML (fallback and additional data)
    _extract_from_html(html, base_url, info)
    
    # Extract meta tags
    _extract_meta_tags(html, info)
    
    return info


def merge_business_info(accumulated: Dict[str, Any], page_info: Dict[str, Any]) -> None:
    """
    Merge page_info into accumulated business info.
    Combines lists, keeps best values, and merges boolean flags.
    """
    # Merge lists - add unique items
    for key in ["addresses", "address_components", "areas_served", "phones", "emails", 
                "services", "categories", "payment_methods", "languages", "images", "meta_keywords"]:
        if key in page_info and isinstance(page_info[key], list):
            for item in page_info[key]:
                if item and item not in accumulated.get(key, []):
                    accumulated.setdefault(key, []).append(item)
    
    # Merge strings - keep first non-empty value
    for key in ["hours", "quote_url", "license_number", "business_name", "founding_date",
                "description", "website", "logo", "price_range", "meta_description"]:
        if key in page_info and page_info[key] and not accumulated.get(key):
            accumulated[key] = page_info[key]
    
    # Merge social media dict
    if "social_media" in page_info and isinstance(page_info["social_media"], dict):
        accumulated.setdefault("social_media", {}).update(page_info["social_media"])
    
    # Merge founders list
    if "founders" in page_info and isinstance(page_info["founders"], list):
        for founder in page_info["founders"]:
            if isinstance(founder, dict) and founder.get("name"):
                if not any(f.get("name") == founder["name"] for f in accumulated.get("founders", [])):
                    accumulated.setdefault("founders", []).append(founder)
    
    # Merge booleans - use OR logic
    for key in ["has_coupon", "has_emergency", "is_licensed"]:
        if key in page_info:
            accumulated[key] = accumulated.get(key, False) or page_info[key]
    
    # Merge numbers - keep best/highest value
    if "rating" in page_info and page_info["rating"] is not None:
        if accumulated.get("rating") is None or page_info["rating"] > accumulated["rating"]:
            accumulated["rating"] = page_info["rating"]
    
    if "review_count" in page_info and page_info["review_count"] is not None:
        if accumulated.get("review_count") is None or page_info["review_count"] > accumulated["review_count"]:
            accumulated["review_count"] = page_info["review_count"]


def _extract_from_schemas(schemas: List[dict], info: Dict) -> None:
    """Extract comprehensive business info from JSON-LD schemas."""
    for schema in schemas:
        # Business name
        if not info["business_name"]:
            stype = schema.get("@type", "")
            stype_list = [stype] if isinstance(stype, str) else (stype if isinstance(stype, list) else [])
            
            skip_types = {"WebPage", "WebSite", "BreadcrumbList", "ItemList"}
            if not any(t in skip_types for t in stype_list):
                name = schema.get("name") or schema.get("legalName")
                if name:
                    info["business_name"] = str(name)
        
        # Description
        if not info["description"]:
            desc = schema.get("description") or schema.get("about")
            if desc:
                info["description"] = str(desc)
        
        # Website & Logo
        if not info["website"]:
            url = schema.get("url") or schema.get("sameAs")
            if isinstance(url, str) and url.startswith("http"):
                info["website"] = url
        
        logo = schema.get("logo")
        if logo:
            if isinstance(logo, dict):
                logo_url = logo.get("url") or logo.get("@id")
            else:
                logo_url = logo
            if logo_url and logo_url not in info["images"]:
                info["logo"] = str(logo_url)
                info["images"].append(str(logo_url))
        
        # Images
        for img_key in ["image", "photo", "photos"]:
            img_val = schema.get(img_key)
            if isinstance(img_val, list):
                for img in img_val:
                    img_url = img.get("url") if isinstance(img, dict) else img
                    if img_url and img_url not in info["images"]:
                        info["images"].append(str(img_url))
            elif img_val:
                img_url = img_val.get("url") if isinstance(img_val, dict) else img_val
                if img_url and img_url not in info["images"]:
                    info["images"].append(str(img_url))
        
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
        
        # Address with full components
        addr = schema.get("address")
        if addr:
            addr_str = _parse_address(addr)
            if addr_str and addr_str not in info["addresses"]:
                info["addresses"].append(addr_str)
            
            # Full address components
            if isinstance(addr, dict):
                addr_comp = {
                    "street": addr.get("streetAddress", ""),
                    "city": addr.get("addressLocality", ""),
                    "state": addr.get("addressRegion", ""),
                    "zip": addr.get("postalCode", ""),
                    "country": addr.get("addressCountry", ""),
                }
                if any(addr_comp.values()):
                    info["address_components"].append(addr_comp)
        
        # Phone - enhanced extraction
        for key in ["telephone", "phone", "contactPhone", "phoneNumber"]:
            val = schema.get(key)
            if val:
                phone = _normalize_phone(str(val))
                if phone and phone not in info["phones"]:
                    info["phones"].append(phone)
        
        # Contact points
        contacts = schema.get("contactPoint", [])
        if isinstance(contacts, dict):
            contacts = [contacts]
        for cp in contacts:
            if isinstance(cp, dict):
                if cp.get("telephone"):
                    phone = _normalize_phone(str(cp["telephone"]))
                    if phone and phone not in info["phones"]:
                        info["phones"].append(phone)
                if cp.get("email"):
                    email = str(cp["email"]).lower()
                    if email not in info["emails"]:
                        info["emails"].append(email)
        
        # Email
        email = schema.get("email")
        if email:
            email_str = str(email).lower()
            if email_str not in info["emails"]:
                info["emails"].append(email_str)
        
        # Areas Served
        for key in ["areaServed", "serviceArea", "areasServed", "coverageArea"]:
            val = schema.get(key)
            areas = _parse_areas(val)
            for area in areas:
                if area and area not in info["areas_served"]:
                    info["areas_served"].append(area)
        
        # Hours
        if not info["hours"]:
            info["hours"] = _parse_hours(schema)
            if "24" in info["hours"]:
                info["has_emergency"] = True
        
        # Services - enhanced
        services = _parse_services(schema)
        for svc in services:
            if svc and svc not in info["services"]:
                info["services"].append(svc)
        
        # Categories/Industries
        for key in ["@type", "additionalType", "category", "industry", "serviceType"]:
            val = schema.get(key)
            if isinstance(val, list):
                for v in val:
                    cat = str(v).replace("https://schema.org/", "").replace("http://schema.org/", "")
                    if cat and cat not in info["categories"]:
                        info["categories"].append(cat)
            elif val:
                cat = str(val).replace("https://schema.org/", "").replace("http://schema.org/", "")
                if cat and cat not in info["categories"]:
                    info["categories"].append(cat)
        
        # Price Range
        if not info["price_range"]:
            price_range = schema.get("priceRange") or schema.get("price")
            if price_range:
                info["price_range"] = str(price_range)
        
        # Payment Methods
        payment = schema.get("paymentAccepted") or schema.get("paymentMethod")
        if payment:
            if isinstance(payment, list):
                info["payment_methods"].extend([str(p) for p in payment if p not in info["payment_methods"]])
            else:
                if str(payment) not in info["payment_methods"]:
                    info["payment_methods"].append(str(payment))
        
        # Languages
        langs = schema.get("inLanguage") or schema.get("availableLanguage")
        if langs:
            if isinstance(langs, list):
                info["languages"].extend([str(l) for l in langs if l not in info["languages"]])
            else:
                if str(langs) not in info["languages"]:
                    info["languages"].append(str(langs))
        
        # Founding Date
        if not info["founding_date"]:
            founding_date = schema.get("foundingDate") or schema.get("dateFounded")
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
                        "email": founder.get("email", ""),
                    }
                    if not any(f.get("name") == founder_info["name"] for f in info["founders"]):
                        info["founders"].append(founder_info)
        
        # Social Media (from sameAs)
        same_as = schema.get("sameAs", [])
        if isinstance(same_as, str):
            same_as = [same_as]
        for url in same_as:
            if isinstance(url, str):
                social_platform = _identify_social_platform(url)
                if social_platform:
                    info["social_media"][social_platform] = url


def _normalize_phone(phone: str) -> str:
    """Normalize phone number format."""
    # Remove common separators
    phone = re.sub(r'[^\d+]', '', phone)
    # Basic validation
    if len(phone) >= 10:
        return phone
    return ""


def _identify_social_platform(url: str) -> Optional[str]:
    """Identify social media platform from URL."""
    url_lower = url.lower()
    for platform in SOCIAL_DOMAINS:
        if platform in url_lower:
            # Map to standard names
            if platform in ['fb.com', 'facebook']:
                return 'facebook'
            elif platform in ['x.com', 'twitter']:
                return 'twitter'
            elif platform == 'instagram':
                return 'instagram'
            elif platform == 'linkedin':
                return 'linkedin'
            elif platform == 'youtube':
                return 'youtube'
            elif platform == 'pinterest':
                return 'pinterest'
            elif platform == 'tiktok':
                return 'tiktok'
            elif platform == 'snapchat':
                return 'snapchat'
    return None


def _parse_address(addr) -> str:
    """Parse address from schema format."""
    if isinstance(addr, str):
        return addr
    if isinstance(addr, dict):
        parts = []
        for key in ["streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry"]:
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
                name = v.get("name") or v.get("addressLocality") or v.get("@id")
                if name:
                    areas.append(str(name))
    elif isinstance(val, dict):
        name = val.get("name") or val.get("addressLocality") or val.get("@id")
        if name:
            areas.append(str(name))
    return areas


def _parse_hours(schema: dict) -> str:
    """Parse business hours from schema."""
    oh = schema.get("openingHours")
    if isinstance(oh, str):
        if "24" in oh.lower() or "always" in oh.lower():
            return "24/7"
        return oh
    if isinstance(oh, list):
        if any("24" in str(h).lower() for h in oh):
            return "24/7"
        return ", ".join(str(h) for h in oh)
    
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
        return ", ".join(f"{d}: {t}" for d, t in sorted(day_hours.items()))
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
    stype = schema.get("@type", "")
    if isinstance(stype, list):
        stype_list = stype
    elif isinstance(stype, str):
        stype_list = [stype]
    else:
        stype_list = []
    
    if "Service" in stype_list:
        name = schema.get("name")
        if name:
            services.append(str(name))
    
    return services


def _extract_from_html(html: str, base_url: str, info: Dict) -> None:
    """Extract business info from HTML content - enhanced version."""
    soup = _get_soup(html)
    text = soup.get_text(separator=" ", strip=True)
    text_lower = text.lower()
    
    # Enhanced phone extraction
    if not info["phones"]:
        found_phones: Set[str] = set()
        for pattern in PHONE_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                normalized = _normalize_phone(match)
                if normalized:
                    found_phones.add(normalized)
        info["phones"] = list(found_phones)[:10]  # Limit to 10
    
    # Email extraction
    if not info["emails"]:
        emails = EMAIL_PATTERN.findall(text)
        info["emails"] = list(set([e.lower() for e in emails]))[:5]  # Limit to 5
    
    # Business name from title/h1 if not found
    if not info["business_name"]:
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove common suffixes
            for suffix in [" - Home", " | Home", " - Official Site", " | Official Site"]:
                title = title.replace(suffix, "")
            if title:
                info["business_name"] = title[:100]  # Limit length
    
    # Logo from common locations
    if not info["logo"]:
        for selector in ['img[alt*="logo" i]', 'img.logo', '.logo img', 'header img']:
            logo_img = soup.select_one(selector)
            if logo_img and logo_img.get("src"):
                logo_url = _make_absolute_url(logo_img["src"], base_url)
                if logo_url:
                    info["logo"] = logo_url
                    if logo_url not in info["images"]:
                        info["images"].append(logo_url)
                    break
    
    # Quote/Contact URL
    if not info["quote_url"]:
        for a in soup.find_all("a", href=True):
            link_text = a.get_text(strip=True).lower()
            href = a.get("href", "")
            
            quote_keywords = ["quote", "free estimate", "get estimate", "request quote", 
                            "request a quote", "get quote", "estimate"]
            if any(kw in link_text for kw in quote_keywords):
                info["quote_url"] = _make_absolute_url(href, base_url)
                break
            elif "contact" in link_text and not info["quote_url"]:
                info["quote_url"] = _make_absolute_url(href, base_url)
    
    # Social media links
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        platform = _identify_social_platform(href)
        if platform and platform not in info["social_media"]:
            info["social_media"][platform] = href
    
    # Coupon/Offer check
    if not info["has_coupon"]:
        coupon_keywords = ["coupon", "offer", "discount", "special", "deal", "promo", 
                          "promotion", "sale", "save"]
        for a in soup.find_all("a", href=True):
            link_text = a.get_text(strip=True).lower()
            if any(kw in link_text for kw in coupon_keywords):
                info["has_coupon"] = True
                break
    
    # Emergency service check
    if not info["has_emergency"]:
        emergency_keywords = ["24/7", "24 hour", "emergency service", "emergency repair", 
                            "available 24", "always available", "round the clock", 
                            "emergency", "24 hours"]
        for kw in emergency_keywords:
            if kw in text_lower:
                info["has_emergency"] = True
                if "24" in kw and not info["hours"]:
                    info["hours"] = "24/7"
                break
    
    # License check
    if not info["is_licensed"]:
        license_keywords = ["licensed", "license #", "license:", "lic #", "lic.", 
                          "contractor license", "state license", "bonded", "insured",
                          "certified", "certification"]
        for kw in license_keywords:
            if kw in text_lower:
                info["is_licensed"] = True
                match = LICENSE_PATTERN.search(text)
                if match:
                    info["license_number"] = match.group(1)
                break
    
    # Extract from structured HTML (address tags, etc.)
    address_tags = soup.find_all(["address", "div"], class_=re.compile(r"address|location", re.I))
    for tag in address_tags:
        addr_text = tag.get_text(strip=True)
        if addr_text and len(addr_text) > 10:  # Reasonable address length
            if addr_text not in info["addresses"]:
                info["addresses"].append(addr_text)


def _extract_meta_tags(html: str, info: Dict) -> None:
    """Extract meta tags and Open Graph data."""
    soup = _get_soup(html)
    
    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"}) or \
                soup.find("meta", attrs={"property": "og:description"})
    if meta_desc and meta_desc.get("content"):
        info["meta_description"] = meta_desc["content"]
    
    # Meta keywords
    meta_keywords = soup.find("meta", attrs={"name": "keywords"})
    if meta_keywords and meta_keywords.get("content"):
        keywords = [k.strip() for k in meta_keywords["content"].split(",")]
        info["meta_keywords"] = keywords
    
    # Open Graph image
    og_image = soup.find("meta", attrs={"property": "og:image"})
    if og_image and og_image.get("content"):
        img_url = og_image["content"]
        if img_url not in info["images"]:
            info["images"].append(img_url)


def _make_absolute_url(href: str, base_url: str) -> str:
    """Convert relative URL to absolute."""
    if not href:
        return ""
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return urljoin(base_url, href)


def format_business_report(info: Dict) -> str:
    """Format business info as a comprehensive report string."""
    lines = [
        f"Business Name: {info.get('business_name', 'N/A')}",
        f"Description: {info.get('description', 'N/A')[:200]}" if info.get('description') else "Description: N/A",
        f"Website: {info.get('website', 'N/A')}",
        f"Rating: {info.get('rating', 'N/A')}/5" if info.get('rating') else "Rating: N/A",
        f"Review Count: {info.get('review_count', 'N/A'):,}" if info.get('review_count') else "Review Count: N/A",
    ]
    
    # Addresses
    if info.get('addresses'):
        lines.append(f"Address: {info['addresses'][0]}")
        if len(info['addresses']) > 1:
            lines.append(f"Additional Addresses: {', '.join(info['addresses'][1:])}")
    else:
        lines.append("Address: N/A")
    
    # Areas Served
    if info.get('areas_served'):
        lines.append(f"Areas Served: {', '.join(info['areas_served'])}")
    else:
        lines.append("Areas Served: N/A")
    
    lines.extend([
        f"Hours: {info.get('hours', 'N/A')}",
        f"Phone: {', '.join(info.get('phones', []))}" if info.get('phones') else "Phone: N/A",
        f"Email: {', '.join(info.get('emails', []))}" if info.get('emails') else "Email: N/A",
        f"Get a Quote: {info.get('quote_url', 'N/A')}",
        f"Services: {', '.join(info.get('services', []))}" if info.get('services') else "Services: N/A",
        f"Categories: {', '.join(info.get('categories', []))}" if info.get('categories') else "Categories: N/A",
        f"Price Range: {info.get('price_range', 'N/A')}",
        f"Payment Methods: {', '.join(info.get('payment_methods', []))}" if info.get('payment_methods') else "Payment Methods: N/A",
        f"Languages: {', '.join(info.get('languages', []))}" if info.get('languages') else "Languages: N/A",
        f"Offer/Coupon: {'Available' if info.get('has_coupon') else 'Not Available'}",
        f"24/7 Emergency Service: {'Yes' if info.get('has_emergency') else 'No'}",
        f"Licensed: {'Yes' + (' (' + info.get('license_number', '') + ')' if info.get('license_number') else '') if info.get('is_licensed') else 'No'}",
    ])
    
    # Social Media
    if info.get('social_media'):
        social_lines = [f"{platform.capitalize()}: {url}" for platform, url in info['social_media'].items()]
        lines.append(f"Social Media: {', '.join(social_lines)}")
    
    # Founding Date
    if info.get('founding_date'):
        lines.append(f"Founding Date: {info['founding_date']}")
    
    # Founders
    if info.get('founders'):
        founders_list = []
        for founder in info['founders']:
            founder_str = founder.get('name', '')
            if founder.get('job_title'):
                founder_str += f" ({founder['job_title']})"
            founders_list.append(founder_str)
        lines.append(f"Founder(s): {', '.join(founders_list)}")
    
    return "\n".join(lines)
