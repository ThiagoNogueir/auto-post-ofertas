
import os
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def generate_simple_link(url: str) -> str:
    """
    Adds affiliate tracking parameters to URLs based on configuration.
    This is a simplified version that doesn't require scraping/login.
    """
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Mercado Livre
        if 'mercadolivre.com' in parsed.netloc:
            # Mercado Livre uses encrypted /sec/ links that cannot be generated
            # without their official API or logging into the dashboard.
            # To automate this reliably, consider using an Affiliate Network (Lomadee, Awin).
            # Returning original URL to prevent 404s.
            return url
                
        # Shopee
        elif 'shopee.com' in parsed.netloc:
            shopee_id = os.getenv('SHOPEE_AFFILIATE_ID')
            if shopee_id:
                params['af_id'] = [shopee_id] # Example param
                
        # Rebuild URL
        new_query = urlencode(params, doseq=True)
        new_url = urlunparse(parsed._replace(query=new_query))
        return new_url
        
    except Exception as e:
        print(f"Error generating link: {e}")
        return url
