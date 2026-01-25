
import os
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def generate_simple_link(url: str) -> str:
    """
    Generates affiliate links.
    For Mercado Livre: Uses official Link Builder
    For Shopee: Appends tracking parameters
    
    Note: Only HTTPS links are accepted. HTTP links are converted to HTTPS.
    """
    try:
        parsed = urlparse(url)
        
        # Force HTTPS - Convert HTTP to HTTPS
        scheme = 'https' if parsed.scheme in ['http', 'https'] else parsed.scheme
        
        # Mercado Livre - Use Link Builder
        if 'mercadolivre.com' in parsed.netloc:
            from .ml_linkbuilder import generate_link_with_linkbuilder
            # Ensure input URL uses HTTPS
            https_url = url.replace('http://', 'https://')
            return generate_link_with_linkbuilder(https_url)
            
        # Shopee
        elif 'shopee.com' in parsed.netloc:
            params = parse_qs(parsed.query)
            shopee_id = os.getenv('SHOPEE_AFFILIATE_ID')
            if shopee_id:
                params['af_id'] = [shopee_id]
                params['utm_source'] = [shopee_id]
                
                new_query = urlencode(params, doseq=True)
                new_url = urlunparse((
                    scheme,  # Use HTTPS
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment
                ))
                return new_url
        
        # For other URLs, ensure HTTPS
        final_url = urlunparse((
            scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return final_url
        
    except Exception as e:
        print(f"Error generating link: {e}")
        return url
