import os
import json
import re
import requests

def shorten_url(url: str) -> str:
    """
    Shorten long URL using is.gd if needed.
    Keeps official short links (meli.la, shope.ee, /sec/) intact.
    Fallback to original URL if shortening fails or returns an error.
    """
    if not url:
        return ""
        
    # If already an official short link, keep it as is!
    if any(domain in url for domain in ['meli.la', 'shope.ee', 'mercadolivre.com/sec/']):
        return url
        
    try:
        from urllib.parse import quote
        encoded_url = quote(url, safe='')
        api_url = f"https://is.gd/create.php?format=simple&url={encoded_url}"
        response = requests.get(api_url, timeout=5)
        text = response.text.strip()
        # Verify it returned a real URL and not an error string like "Error, database insert failed"
        if response.status_code == 200 and text.startswith('http'):
            return text
        return url
    except Exception:
        return url

def extract_product_id(url: str) -> str:
    """
    Extracts a permanent, stable product ID from URL to prevent duplicates.
    Prioritizes canonical catalog IDs (/p/MLB...), user products (/up/MLBU...),
    item IDs in path (/MLB-...), and query params (wid=MLB...).
    Never matches promotional campaign filters (deal%3AMLB...).
    
    Args:
        url: Product URL
        
    Returns:
        Stable unique product ID
    """
    if not url:
        return ""
    
    try:
        clean_url = url.split('#')[0]
        
        # 1. Mercado Livre Canonical Catalog ID: /p/MLB12345678
        p_match = re.search(r'/p/(MLB\d+)', clean_url, re.IGNORECASE)
        if p_match:
            return p_match.group(1).upper()
            
        # 2. Mercado Livre User Product ID: /up/MLBU12345678 or /up/MLB12345678
        up_match = re.search(r'/up/(MLBU?\d+)', clean_url, re.IGNORECASE)
        if up_match:
            return up_match.group(1).upper()
            
        # 3. Path-only match (avoids matching query parameters like deal%3AMLB...):
        path_only = clean_url.split('?')[0]
        path_match = re.search(r'/(MLB-?\d+)', path_only, re.IGNORECASE)
        if path_match:
            return path_match.group(1).replace('-', '').upper()
            
        # 4. Query param wid (Winner Item ID in sponsored/search): wid=MLB12345678
        wid_match = re.search(r'[?&]wid=(MLB\d+)', clean_url, re.IGNORECASE)
        if wid_match:
            return wid_match.group(1).upper()

        # 5. Query param item_id: item_id=MLB12345678
        item_match = re.search(r'[?&]item_id=(MLB\d+)', clean_url, re.IGNORECASE)
        if item_match:
            return item_match.group(1).upper()
            
        # 6. Shopee: i.shopid.itemid or product/shopid/itemid
        if 'shopee' in clean_url:
            shopee_match = re.search(r'i\.(\d+)\.(\d+)', clean_url) or re.search(r'product/(\d+)/(\d+)', clean_url)
            if shopee_match:
                return f"SHP_{shopee_match.group(1)}_{shopee_match.group(2)}"
                
        # Fallback: clean URL slug without query
        slug = path_only.rstrip('/').split('/')[-1]
        return slug or url
        
    except Exception:
        return url.split('?')[0].split('/')[-1]


STATE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'scraper_state.json')

def get_url_page(url: str) -> int:
    """Get the current page offset for a given URL to continue from where it stopped."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
            return state.get(url, 1)
    except Exception:
        pass
    return 1


def set_url_page(url: str, page: int):
    """Save the page offset for a given URL to persist progression across restarts."""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        state = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            except Exception:
                state = {}
        state[url] = max(1, page)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def get_paginated_url(base_url: str, page: int) -> str:
    """Builds a paginated URL for Mercado Livre."""
    if page <= 1:
        return base_url
    sep = '&' if '?' in base_url else '?'
    return f"{base_url}{sep}page={page}"

