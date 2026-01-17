"""
Gerador de Links de Afiliado do Mercado Livre.
Usa a API oficial do Mercado Livre para gerar links de afiliado.
"""

import os
import requests
from typing import Optional
from ..utils.logger import logger


class MercadoLivreAffiliate:
    """Gerenciador de links de afiliado do Mercado Livre."""
    
    def __init__(self):
        self.access_token = os.getenv('ML_ACCESS_TOKEN')
        self.tag_id = os.getenv('ML_TAG_ID', 'PROMOBOT')
        self.base_url = 'https://api.mercadolibre.com'
    
    def generate_affiliate_link(self, product_url: str) -> Optional[str]:
        """
        Gera link de afiliado para um produto do Mercado Livre.
        
        Args:
            product_url: URL original do produto
            
        Returns:
            Link de afiliado ou URL original se falhar
        """
        if not self.access_token or self.access_token == 'seu_token_ml':
            logger.warning("ML_ACCESS_TOKEN not configured, using original URL")
            return product_url
        
        try:
            # Extract product ID from URL
            product_id = self._extract_product_id(product_url)
            if not product_id:
                logger.warning(f"Could not extract product ID from {product_url}")
                return product_url
            
            # Generate affiliate link using ML API
            affiliate_url = self._call_ml_api(product_id, product_url)
            
            if affiliate_url:
                logger.info(f"Generated ML affiliate link for {product_id}")
                return affiliate_url
            else:
                logger.warning("Failed to generate affiliate link, using original")
                return product_url
                
        except Exception as e:
            logger.error(f"Error generating ML affiliate link: {e}")
            return product_url
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        """Extract product ID from Mercado Livre URL."""
        try:
            # ML URLs can be:
            # https://produto.mercadolivre.com.br/MLB-123456-title
            # https://www.mercadolivre.com.br/p/MLB123456
            # https://articulo.mercadolibre.com.ar/MLA-123456-title
            
            parts = url.split('/')
            for part in parts:
                if part.startswith('MLB') or part.startswith('MLA') or part.startswith('MLM'):
                    # Remove everything after the ID
                    product_id = part.split('-')[0]
                    return product_id
            
            return None
        except Exception as e:
            logger.error(f"Error extracting product ID: {e}")
            return None
    
    def _call_ml_api(self, product_id: str, original_url: str) -> Optional[str]:
        """
        Call Mercado Livre API to generate affiliate link.
        
        Note: This is a simplified version. The actual ML Affiliate API
        requires registration and approval. For now, we'll add tracking
        parameters to the URL.
        """
        try:
            # Method 1: Use ML's official affiliate link structure
            # This requires being registered in the ML Affiliate Program
            if self.access_token and self.access_token != 'seu_token_ml':
                affiliate_url = f"{original_url}?tracking_id={self.tag_id}"
                return affiliate_url
            
            # Method 2: Fallback - add UTM parameters for tracking
            separator = '&' if '?' in original_url else '?'
            tracking_url = f"{original_url}{separator}utm_source=promobot&utm_medium=telegram&utm_campaign={self.tag_id}"
            
            return tracking_url
            
        except Exception as e:
            logger.error(f"Error calling ML API: {e}")
            return None


def generate_ml_affiliate_link(product_url: str) -> str:
    """
    Convenience function to generate ML affiliate link.
    
    Args:
        product_url: Original product URL
        
    Returns:
        Affiliate link or original URL
    """
    generator = MercadoLivreAffiliate()
    return generator.generate_affiliate_link(product_url)
