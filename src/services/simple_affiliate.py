
import os
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def generate_simple_link(url: str) -> str:
    """
    Generates affiliate links by appending specific query parameters.
    No scraping or external API calls involved for stability.
    """
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Mercado Livre
        if 'mercadolivre.com' in parsed.netloc:
            # Mercado Livre uses encrypted /sec/ links usually, but we can try appending tracking IDs
            ml_id = os.getenv('ML_AFFILIATE_ID')
            if ml_id:
                params['tracking_id'] = [ml_id]
                params['matt_tool'] = ['my_bot'] # Identificador opcional
                
                # Rebuild URL
                new_query = urlencode(params, doseq=True)
                new_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment
                ))
                return new_url
            return url
            
        # Shopee
        elif 'shopee.com' in parsed.netloc:
            shopee_id = os.getenv('SHOPEE_AFFILIATE_ID')
            if shopee_id:
                # Add Shopee affiliate params if ID exists
                params['af_id'] = [shopee_id]
                params['utm_source'] = [shopee_id]
                
                # Rebuild URL
                new_query = urlencode(params, doseq=True)
                new_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment
                ))
                return new_url
        
        return url
        
    except Exception as e:
        print(f"Error generating link: {e}")
        return url
