"""
ML Link Builder - Official affiliate link generator
Uses Selenium to access ML's Link Builder tool
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

COOKIES_FILE = "ml_linkbuilder_cookies.pkl"

def save_cookies(driver):
    """Save cookies to file"""
    try:
        cookies = driver.get_cookies()
        with open(COOKIES_FILE, 'wb') as f:
            pickle.dump(cookies, f)
        logger.info("Cookies saved successfully")
    except Exception as e:
        logger.warning(f"Could not save cookies: {e}")

def load_cookies(driver):
    """Load cookies from file"""
    try:
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
            logger.info("Cookies loaded successfully")
            return True
    except Exception as e:
        logger.warning(f"Could not load cookies: {e}")
    return False

def generate_link_with_linkbuilder(product_url: str, timeout: int = 30) -> str:
    """
    Uses ML's official Link Builder to generate affiliate links.
    
    Args:
        product_url: ML product URL
        timeout: Max time to wait
        
    Returns:
        Affiliate link or original URL if failed
    """
    driver = None
    try:
        logger.info(f"Using ML Link Builder for: {product_url}")
        
        chrome_options = Options()
        
        # Use temporary profile to avoid locks
        import tempfile
        temp_profile = tempfile.mkdtemp(prefix="ml_linkbuilder_")
        chrome_options.add_argument(f"user-data-dir={temp_profile}")
        
        # Stability arguments
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1400,900")
        
        # Use webdriver-manager
        service = Service(ChromeDriverManager().install())
        
        logger.info("Starting Chrome for Link Builder...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        # Navigate to Link Builder
        logger.info("Navigating to Link Builder...")
        driver.get("https://www.mercadolivre.com.br/afiliados/linkbuilder")
        time.sleep(2)
        
        # Try to load cookies
        cookies_loaded = load_cookies(driver)
        if cookies_loaded:
            logger.info("Refreshing page with cookies...")
            driver.refresh()
            time.sleep(3)
        
        # Check if login is required
        current_url = driver.current_url
        if 'login' in current_url or 'signin' in current_url:
            logger.warning("Login required - Link Builder needs authentication")
            logger.warning("Please login manually in the browser window...")
            
            # Wait for user to login
            for i in range(60):
                time.sleep(1)
                current_url = driver.current_url
                if 'linkbuilder' in current_url and 'login' not in current_url:
                    logger.info("Login detected! Saving cookies...")
                    time.sleep(2)
                    save_cookies(driver)
                    break
            else:
                logger.error("Login timeout")
                return product_url
        
        # Now we should be on Link Builder page
        time.sleep(3)
        
        # Find the textarea for URLs
        logger.info("Looking for URL textarea...")
        url_input = None
        
        try:
            textareas = driver.find_elements(By.CSS_SELECTOR, "textarea")
            for textarea in textareas:
                if textarea.is_displayed() and textarea.is_enabled():
                    parent_classes = textarea.get_attribute('class') or ''
                    if 'nav-search' not in parent_classes:
                        url_input = textarea
                        logger.info("Found URL textarea")
                        break
        except Exception as e:
            logger.error(f"Error finding textarea: {e}")
            return product_url
        
        if not url_input:
            logger.error("Could not find URL textarea")
            return product_url
        
        # Scroll and focus
        driver.execute_script("arguments[0].scrollIntoView(true);", url_input)
        time.sleep(1)
        url_input.click()
        time.sleep(1)
        
        # Enter URL
        logger.info("Entering product URL...")
        url_input.clear()
        time.sleep(0.5)
        url_input.send_keys(product_url)
        time.sleep(1)
        
        # Find and click "Gerar" button
        logger.info("Looking for 'Gerar' button...")
        gerar_button = None
        
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                button_text = button.text.strip().lower()
                if 'gerar' in button_text and button.is_displayed():
                    gerar_button = button
                    logger.info(f"Found 'Gerar' button with text: {button.text}")
                    break
        except Exception as e:
            logger.error(f"Error finding Gerar button: {e}")
        
        if not gerar_button:
            logger.warning("'Gerar' button not found, trying submit button...")
            try:
                gerar_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            except:
                pass
        
        if gerar_button:
            logger.info("Clicking 'Gerar' button...")
            gerar_button.click()
            time.sleep(8)  # Wait for link generation (can take 5-8 seconds)
        else:
            logger.error("Could not find 'Gerar' button")
            return product_url
        
        # Find the generated link in the result box (right side)
        logger.info("Looking for generated link...")
        generated_link = None
        
        try:
            # Look for the link in the result area
            link_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'][readonly], textarea[readonly]")
            for link_input in link_inputs:
                value = link_input.get_attribute('value')
                if value and 'mercadolivre.com' in value and '/sec/' in value:
                    generated_link = value
                    logger.info(f"Found generated link: {generated_link[:80]}...")
                    break
        except Exception as e:
            logger.error(f"Error extracting link: {e}")
        
        if not generated_link:
            logger.warning("Could not find generated link, trying alternative selectors...")
            try:
                # Try to find any text containing the short link
                page_text = driver.page_source
                import re
                matches = re.findall(r'https://mercadolivre\.com/sec/[A-Za-z0-9]+', page_text)
                if matches:
                    generated_link = matches[0]
                    logger.info(f"Found link in page source: {generated_link}")
            except:
                pass
        
        if generated_link:
            return generated_link
        else:
            logger.error("Could not extract generated link")
            return product_url
            
    except Exception as e:
        logger.error(f"Error using Link Builder: {e}")
        return product_url
        
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Chrome closed")
            except:
                pass
