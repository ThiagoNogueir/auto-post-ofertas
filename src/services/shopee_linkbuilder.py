"""
Shopee Link Builder - Official affiliate link generator
Uses Selenium to access Shopee's Affiliate Link Builder tool
"""
import os
import time
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from ..utils.logger import logger

SHOPEE_COOKIES_FILE = "shopee_linkbuilder_cookies.pkl"

def save_shopee_cookies(driver):
    """Save Shopee cookies to file"""
    try:
        cookies = driver.get_cookies()
        with open(SHOPEE_COOKIES_FILE, 'wb') as f:
            pickle.dump(cookies, f)
        logger.info("Shopee cookies saved successfully")
    except Exception as e:
        logger.warning(f"Could not save Shopee cookies: {e}")

def load_shopee_cookies(driver):
    """Load Shopee cookies from file"""
    try:
        if os.path.exists(SHOPEE_COOKIES_FILE):
            with open(SHOPEE_COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
            logger.info("Shopee cookies loaded successfully")
            return True
    except Exception as e:
        logger.warning(f"Could not load Shopee cookies: {e}")
    return False

def generate_shopee_affiliate_link(product_url: str, timeout: int = 30) -> str:
    """
    Uses Shopee's official Affiliate Link Builder to generate affiliate links.
    
    Args:
        product_url: Shopee product URL
        timeout: Max time to wait
        
    Returns:
        Affiliate link or original URL if failed
    """
    driver = None
    try:
        logger.info(f"Using Shopee Link Builder for: {product_url}")
        
        chrome_options = Options()
        
        # Use persistent profile directory for cookies
        profile_dir = os.path.join(os.getcwd(), "shopee_chrome_profile")
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
            logger.info(f"Created Shopee profile directory: {profile_dir}")
        
        chrome_options.add_argument(f"user-data-dir={profile_dir}")
        
        # Stability arguments
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1400,900")
        
        # Use webdriver-manager
        service = Service(ChromeDriverManager().install())
        
        logger.info("Starting Chrome for Shopee Link Builder...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        # Navigate to Shopee Affiliate Link Builder
        # URL pode variar dependendo da região - ajustar conforme necessário
        logger.info("Navigating to Shopee Affiliate Link Builder...")
        driver.get("https://affiliate.shopee.com.br/offer/product_offer")
        time.sleep(5)
        
        # Check if login is required
        current_url = driver.current_url
        if 'login' in current_url or 'signin' in current_url or 'account' in current_url:
            logger.warning("Login required - Shopee Link Builder needs authentication")
            logger.warning("Please login manually in the browser window...")
            
            # Wait for user to login
            for i in range(60):
                time.sleep(1)
                current_url = driver.current_url
                if 'product_offer' in current_url and 'login' not in current_url:
                    logger.info("Login detected! Saving cookies...")
                    time.sleep(2)
                    save_shopee_cookies(driver)
                    break
            else:
                logger.error("Login timeout")
                return product_url
        
        # Now we should be on Shopee Affiliate page
        time.sleep(3)
        
        # Find the input field for product URL
        logger.info("Looking for product URL input field...")
        url_input = None
        
        try:
            # Wait for the page to fully load
            time.sleep(2)
            
            # Try different selectors for Shopee's input field
            # Shopee pode usar diferentes seletores, vamos tentar vários
            selectors = [
                "input[placeholder*='link']",
                "input[placeholder*='URL']",
                "input[placeholder*='produto']",
                "input[type='text']",
                "textarea"
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Check if it's in the main content area
                            parent_classes = element.get_attribute('class') or ''
                            if 'nav' in parent_classes or 'header' in parent_classes:
                                continue
                            
                            url_input = element
                            logger.info(f"Found input field using selector: {selector}")
                            break
                    
                    if url_input:
                        break
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error finding input field: {e}")
            return product_url
        
        if not url_input:
            logger.error("Could not find product URL input field")
            return product_url
        
        # Scroll to input and give it focus
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", url_input)
            time.sleep(1)
            
            # Click to focus
            url_input.click()
            time.sleep(1)
            
            # Clear any existing content
            url_input.clear()
            time.sleep(0.5)
            
            # Use JavaScript to set value as backup
            driver.execute_script("arguments[0].value = '';", url_input)
            time.sleep(0.5)
            
            logger.info("Entering product URL...")
            url_input.send_keys(product_url)
            time.sleep(2)
            
            # Verify it was entered
            entered_value = url_input.get_attribute('value')
            logger.info(f"Entered value length: {len(entered_value)} chars")
            
        except Exception as e:
            logger.error(f"Error entering URL: {e}")
            return product_url
        
        # Find and click generate/submit button
        logger.info("Looking for generate button...")
        generate_button = None
        
        try:
            # Try to find button with common texts
            button_texts = ['gerar', 'generate', 'criar', 'create', 'obter', 'get']
            buttons = driver.find_elements(By.TAG_NAME, "button")
            
            for button in buttons:
                button_text = button.text.strip().lower()
                for text in button_texts:
                    if text in button_text and button.is_displayed():
                        generate_button = button
                        logger.info(f"Found generate button with text: {button.text}")
                        break
                if generate_button:
                    break
        except Exception as e:
            logger.error(f"Error finding generate button: {e}")
        
        if not generate_button:
            logger.warning("Generate button not found, trying submit button...")
            try:
                generate_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            except:
                pass
        
        if generate_button:
            logger.info("Clicking generate button...")
            generate_button.click()
            time.sleep(8)  # Wait for link generation
        else:
            logger.error("Could not find generate button")
            return product_url
        
        # Find the generated affiliate link
        logger.info("Looking for generated affiliate link...")
        generated_link = None
        
        try:
            # Look for the link in result areas
            # Shopee pode mostrar o link em diferentes formatos
            link_selectors = [
                "input[readonly]",
                "textarea[readonly]",
                "input[type='text'][disabled]",
                "div[class*='link']",
                "span[class*='link']"
            ]
            
            for selector in link_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        value = element.get_attribute('value') or element.text
                        if value and 'shopee.com' in value and ('aff' in value or 'affiliate' in value):
                            generated_link = value
                            logger.info(f"Found generated link: {generated_link[:80]}...")
                            break
                    
                    if generated_link:
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting link: {e}")
        
        if not generated_link:
            logger.warning("Could not find generated link, trying alternative methods...")
            try:
                # Try to find any text containing affiliate link pattern
                page_text = driver.page_source
                import re
                # Shopee affiliate links geralmente contêm parâmetros específicos
                matches = re.findall(r'https://[a-z.]*shopee\.com\.br/[^"\'<>\s]+(?:aff|affiliate)[^"\'<>\s]*', page_text)
                if matches:
                    generated_link = matches[0]
                    logger.info(f"Found link in page source: {generated_link}")
            except:
                pass
        
        if generated_link:
            return generated_link
        else:
            logger.error("Could not extract generated affiliate link")
            return product_url
            
    except Exception as e:
        logger.error(f"Error using Shopee Link Builder: {e}")
        return product_url
        
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Chrome closed")
            except:
                pass
