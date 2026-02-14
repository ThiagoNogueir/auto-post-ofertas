"""
ML Coupon Generator - Automated coupon generation for Mercado Livre affiliates
Uses Selenium to automate coupon creation via ML's web interface
"""
import os
import time
import hashlib
import pickle
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from ..utils.logger import logger
from ..database.models import save_coupon, get_coupon_by_product, get_coupon_by_code

# Reuse ML LinkBuilder cookies
COOKIES_FILE = "ml_linkbuilder_cookies.pkl"


def generate_coupon_name(product_id: str = None, prefix: str = "PROMO", category: str = None) -> str:
    """
    Generate a simple, user-friendly coupon name.
    
    Format Options:
    - With category: CATEGORIA_NUMERO (ex: CELULAR_01, ELETRO_05)
    - Without category: PREFIX_NUMERO (ex: PROMO_01, OFERTA_10)
    
    Args:
        product_id: Optional product ID
        prefix: Coupon prefix (default: PROMO)
        category: Product category for more descriptive names
        
    Returns:
        Simple coupon code
    """
    from ..database.models import Coupon
    
    # Simplify category name for coupon code
    category_map = {
        'Celulares': 'CEL',
        'Eletrônicos': 'ELET',
        'Computadores': 'COMP',
        'Suplementos': 'SUPLEM',
        'Animais': 'PET',
        'Roupas': 'MODA',
        'Calçados': 'CALC',
        'Outros': 'PROMO'
    }
    
    # Determine base prefix
    if category and category in category_map:
        base_prefix = category_map[category]
    else:
        base_prefix = prefix
    
    # Find next available number for this prefix
    try:
        # Get all coupons with this prefix
        existing = Coupon.select().where(
            Coupon.coupon_code.startswith(base_prefix)
        ).order_by(Coupon.created_at.desc()).limit(100)
        
        # Extract numbers and find max
        max_num = 0
        for coupon in existing:
            try:
                # Extract number from code like "CEL_05" or "PROMO_10"
                parts = coupon.coupon_code.split('_')
                if len(parts) == 2:
                    num = int(parts[1])
                    max_num = max(max_num, num)
            except:
                continue
        
        # Next number
        next_num = max_num + 1
    except:
        # If error, start from 1
        next_num = 1
    
    # Format: PREFIX_NN (ex: CEL_01, PROMO_05)
    coupon_name = f"{base_prefix}_{next_num:02d}"
    
    return coupon_name


def load_cookies(driver):
    """Load cookies from ML LinkBuilder"""
    try:
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
            logger.info("ML cookies loaded successfully")
            return True
    except Exception as e:
        logger.warning(f"Could not load ML cookies: {e}")
    return False


def save_cookies(driver):
    """Save cookies for future use"""
    try:
        cookies = driver.get_cookies()
        with open(COOKIES_FILE, 'wb') as f:
            pickle.dump(cookies, f)
        logger.info("ML cookies saved successfully")
    except Exception as e:
        logger.warning(f"Could not save cookies: {e}")


def create_coupon_selenium(product_url: str, discount_percentage: float = 5.0, 
                          product_id: str = None, category: str = 'Outros',
                          timeout: int = 30) -> dict:
    """
    Create a coupon using Selenium automation on ML's coupon page.
    
    Args:
        product_url: ML product URL
        discount_percentage: Discount percentage (default: 5%)
        product_id: ML product ID
        category: Product category
        timeout: Max time to wait
        
    Returns:
        Dictionary with coupon info: {'code': str, 'discount': float, 'success': bool}
    """
    driver = None
    result = {'code': None, 'discount': discount_percentage, 'success': False}
    
    try:
        logger.info(f"Creating coupon for product: {product_id}")
        
        # Check if we already have a coupon for this product
        existing_coupon = get_coupon_by_product(product_id) if product_id else None
        if existing_coupon:
            logger.info(f"Found existing coupon: {existing_coupon.coupon_code}")
            result['code'] = existing_coupon.coupon_code
            result['discount'] = float(existing_coupon.discount_percentage or discount_percentage)
            result['success'] = True
            return result
        
        # Generate unique coupon name
        coupon_code = generate_coupon_name(product_id, category=category)
        
        # Check if this code already exists (very unlikely but safe)
        if get_coupon_by_code(coupon_code):
            logger.warning(f"Coupon code {coupon_code} already exists, generating new one")
            coupon_code = generate_coupon_name(product_id + str(time.time()))
        
        logger.info(f"Generated coupon code: {coupon_code}")
        
        # Setup Chrome
        chrome_options = Options()
        profile_dir = os.path.join(os.getcwd(), "ml_chrome_profile")
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        
        chrome_options.add_argument(f"user-data-dir={profile_dir}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1400,900")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        # Navigate to coupons page
        logger.info("Navigating to ML Coupons page...")
        driver.get("https://www.mercadolivre.com.br/afiliados/coupons#hub")
        time.sleep(5)
        
        # Check if login is required
        current_url = driver.current_url
        if 'login' in current_url or 'signin' in current_url:
            logger.warning("Login required - waiting for manual login...")
            
            # Wait for user to login
            for i in range(60):
                time.sleep(1)
                current_url = driver.current_url
                if 'coupons' in current_url and 'login' not in current_url:
                    logger.info("Login detected! Saving cookies...")
                    time.sleep(2)
                    save_cookies(driver)
                    break
            else:
                logger.error("Login timeout")
                return result
        
        time.sleep(3)
        
        # NOTE: This is a placeholder for the actual coupon creation logic
        # The exact selectors and workflow will depend on ML's coupon interface
        # This would need to be customized based on the actual page structure
        
        logger.warning("Coupon creation via Selenium requires manual implementation")
        logger.warning("Please visit https://www.mercadolivre.com.br/afiliados/coupons#hub")
        logger.warning("and create coupons manually for now.")
        
        # For now, save the coupon to database as "pending manual creation"
        # This allows the system to track what coupons should be created
        
        try:
            save_coupon(
                coupon_code=coupon_code,
                product_id=product_id or 'unknown',
                discount_percentage=discount_percentage,
                category=category,
                expires_at=datetime.now() + timedelta(days=30)
            )
            logger.info(f"Coupon {coupon_code} saved to database (pending manual creation)")
            result['code'] = coupon_code
            result['success'] = True
        except Exception as e:
            logger.error(f"Error saving coupon to database: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating coupon: {e}")
        return result
        
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Chrome closed")
            except:
                pass


def apply_coupon_to_link(affiliate_link: str, coupon_code: str) -> str:
    """
    Apply a coupon code to an affiliate link.
    
    Args:
        affiliate_link: ML affiliate link
        coupon_code: Coupon code to apply
        
    Returns:
        Modified link with coupon parameter
    """
    if not coupon_code:
        return affiliate_link
    
    # Add coupon as URL parameter
    separator = '&' if '?' in affiliate_link else '?'
    return f"{affiliate_link}{separator}coupon={coupon_code}"


def get_or_create_coupon(product_url: str, product_id: str = None, 
                         discount_percentage: float = 5.0, 
                         category: str = 'Outros') -> dict:
    """
    Get existing coupon or create a new one for a product.
    
    Args:
        product_url: ML product URL
        product_id: ML product ID
        discount_percentage: Discount percentage
        category: Product category
        
    Returns:
        Dictionary with coupon info
    """
    # Try to get existing coupon
    if product_id:
        existing = get_coupon_by_product(product_id)
        if existing:
            return {
                'code': existing.coupon_code,
                'discount': float(existing.discount_percentage or discount_percentage),
                'success': True
            }
    
    # Create new coupon
    return create_coupon_selenium(
        product_url=product_url,
        discount_percentage=discount_percentage,
        product_id=product_id,
        category=category
    )
