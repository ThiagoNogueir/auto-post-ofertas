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
    Extracts a stable product ID from URL to prevent duplicates.
    
    Args:
        url: Product URL
        
    Returns:
        Stable ID or original URL if extraction fails
    """
    try:
        # Mercado Livre (MLB-12345678 or MLB12345678)
        ml_match = re.search(r'(MLB-?\d+)', url)
        if ml_match:
            return ml_match.group(1).replace('-', '')
            
        # Shopee (i.shopid.itemid)
        # Pattern: shopee.com.br/product/123/456 or shopee.com.br/...-i.123.456
        if 'shopee' in url:
            # Try i.123.456 pattern
            shopee_match = re.search(r'i\.(\d+)\.(\d+)', url)
            if shopee_match:
                return f"shp_{shopee_match.group(1)}_{shopee_match.group(2)}"
            
            # Try finding just numbers at the end
            # ...
            
        # Fallback to simple split logic but cleaner
        # Remove query params
        clean_url = url.split('?')[0]
        # Remove trailing slash
        if clean_url.endswith('/'):
            clean_url = clean_url[:-1]
        
        return clean_url.split('/')[-1]
        
    except Exception:
        return url.split('/')[-1]
