"""
Simple Affiliate Link Generator
Routes to the appropriate link builder (ML or Shopee)
Integrates coupon generation for Mercado Livre products
"""
import os
import json
from ..utils.logger import logger


def generate_simple_link(url: str, with_coupon: bool = True) -> str:
    """
    Generate affiliate link for the given URL.
    Routes to ML or Shopee link builder based on URL.
    
    Args:
        url: Product URL
        with_coupon: Whether to generate/apply coupon (ML only)
        
    Returns:
        Affiliate link or original URL if failed
    """
    try:
        # Determine platform
        if 'mercadolivre.com' in url or 'mercadolibre.com' in url:
            from .ml_linkbuilder import generate_link_with_linkbuilder
            from .ml_coupon_generator import get_or_create_coupon, apply_coupon_to_link
            from ..utils.helpers import extract_product_id
            
            # Generate affiliate link
            affiliate_link = generate_link_with_linkbuilder(url)
            
            # Try to add coupon if enabled
            if with_coupon and affiliate_link:
                try:
                    # Load coupon config
                    coupon_config = {}
                    config_path = os.path.join(os.getcwd(), 'coupon_config.json')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            coupon_config = json.load(f)
                    
                    # Check if coupons are enabled
                    if coupon_config.get('enabled', False):
                        product_id = extract_product_id(url)
                        
                        # Get default discount
                        default_discount = coupon_config.get('default_discount_percentage', 5)
                        
                        logger.info(f"Attempting to create/get coupon for product {product_id}")
                        coupon_info = get_or_create_coupon(
                            product_url=url,
                            product_id=product_id,
                            discount_percentage=default_discount
                        )
                        
                        if coupon_info.get('success') and coupon_info.get('code'):
                            logger.info(f"Applying coupon {coupon_info['code']} to link")
                            affiliate_link = apply_coupon_to_link(affiliate_link, coupon_info['code'])
                        else:
                            logger.warning("Could not create/get coupon")
                    else:
                        logger.info("Coupons disabled in config")
                        
                except Exception as e:
                    logger.error(f"Error adding coupon to link: {e}")
                    # Continue without coupon
            
            return affiliate_link
            
        elif 'shopee.com' in url:
            from .shopee_linkbuilder import generate_link_with_linkbuilder as shopee_generate
            return shopee_generate(url)
            
        else:
            logger.warning(f"Unknown platform for URL: {url}")
            return url
            
    except Exception as e:
        logger.error(f"Error generating affiliate link: {e}")
        return url
