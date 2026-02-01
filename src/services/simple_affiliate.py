
import os
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def generate_simple_link(url: str) -> str:
    """
    Generates affiliate links using official Link Builders.
    For Mercado Livre: Uses ML official Link Builder
    For Shopee: Uses Shopee official Link Builder
    
    Note: Only HTTPS links are accepted. HTTP links are converted to HTTPS.
    """
    try:
        parsed = urlparse(url)
        
        # Force HTTPS - Convert HTTP to HTTPS
        scheme = 'https' if parsed.scheme in ['http', 'https'] else parsed.scheme
        
        # Mercado Livre - Use ML Link Builder
        if 'mercadolivre.com' in parsed.netloc:
            from .ml_linkbuilder import generate_link_with_linkbuilder
            # Ensure input URL uses HTTPS
            https_url = url.replace('http://', 'https://')
            return generate_link_with_linkbuilder(https_url)
            
        # Shopee - Use Shopee Link Builder
        elif 'shopee.com' in parsed.netloc:
            from .shopee_linkbuilder import generate_shopee_affiliate_link
            # Ensure input URL uses HTTPS
            https_url = url.replace('http://', 'https://')
            return generate_shopee_affiliate_link(https_url)
        
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
