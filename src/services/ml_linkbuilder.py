"""
ML Link Builder - Official affiliate link generator
Uses Selenium to access ML's Link Builder tool
"""
import os
import time
import pickle
from typing import Optional
import requests
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
    """Load cookies from file or env"""
    try:
        if not os.path.exists(COOKIES_FILE):
            b64_env = os.getenv("ML_COOKIES_BASE64")
            if b64_env:
                import base64
                with open(COOKIES_FILE, "wb") as f:
                    f.write(base64.b64decode(b64_env))
                logger.info("Restored cookies from ML_COOKIES_BASE64 environment variable")

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

def generate_link_via_api(product_url: str) -> Optional[str]:
    """
    Generates official ML affiliate short link (meli.la) directly via HTTP API.
    Does not launch Chrome or use Selenium.
    """
    try:
        if not os.path.exists(COOKIES_FILE):
            b64_env = os.getenv("ML_COOKIES_BASE64")
            if b64_env:
                import base64
                with open(COOKIES_FILE, "wb") as f:
                    f.write(base64.b64decode(b64_env))
                logger.info("Restored cookies from ML_COOKIES_BASE64 environment variable")
            else:
                logger.warning(f"Cookies file {COOKIES_FILE} not found for API generation")
                return None
            
        with open(COOKIES_FILE, 'rb') as f:
            cookie_list = pickle.load(f)
            
        cookies = {c['name']: c['value'] for c in cookie_list}
        csrf_token = cookies.get('_csrf')
        affiliate_tag = os.getenv('ML_AFFILIATE_ID') or cookies.get('orgnickp')
        
        if not affiliate_tag:
            logger.warning("No affiliate tag found in env or cookies")
            return None
            
        # Clean URL anchor and trailing spaces
        clean_url = product_url.split('#')[0].strip()
        
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'x-csrf-token': csrf_token or '',
            'referer': clean_url,
            'origin': 'https://produto.mercadolivre.com.br',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        
        response = requests.post(
            'https://www.mercadolivre.com.br/affiliate-program/api/v2/stripe/user/links',
            json={'url': clean_url, 'tag': affiliate_tag},
            headers=headers,
            cookies=cookies,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            short_url = data.get('short_url')
            if short_url:
                logger.info(f"Generated affiliate link via ML API (No Chrome): {short_url}")
                return short_url
        else:
            logger.warning(f"ML Affiliate API returned status {response.status_code}: {response.text[:150]}")
            
    except Exception as e:
        logger.error(f"Error calling ML Affiliate API: {e}")
        
    return None

def generate_link_with_linkbuilder(product_url: str, timeout: int = 30) -> str:
    """
    Uses ML's official Link Builder to generate affiliate links.
    Tries fast HTTP API first (no Chrome), then falls back to headless Selenium.
    
    Args:
        product_url: ML product URL
        timeout: Max time to wait
        
    Returns:
        Affiliate link or original URL if failed
    """
    # 1. Try direct API first (Instant, No Chrome window)
    api_link = generate_link_via_api(product_url)
    if api_link:
        return api_link
        
    logger.info("Falling back to Selenium Link Builder (Headless mode)...")
    driver = None
    try:
        logger.info(f"Using ML Link Builder for: {product_url}")
        
        chrome_options = Options()
        
        # Use persistent profile directory for cookies
        profile_dir = os.path.join(os.getcwd(), "ml_chrome_profile")
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
            logger.info(f"Created profile directory: {profile_dir}")
        
        chrome_options.add_argument(f"user-data-dir={profile_dir}")
        
        # Headless mode so Chrome doesn't open on user's screen
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1400,900")
        
        # Use webdriver-manager
        service = Service(ChromeDriverManager().install())
        
        logger.info("Starting Headless Chrome for Link Builder...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        # Navigate directly to Link Builder (cookies are in the profile)
        logger.info("Navigating to Link Builder...")
        driver.get("https://www.mercadolivre.com.br/afiliados/linkbuilder")
        time.sleep(5)
        
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
        
        # Find the textarea for URLs - be very specific
        logger.info("Looking for URL textarea...")
        url_input = None
        
        try:
            # Wait for the page to fully load
            time.sleep(2)
            
            # Find all textareas
            textareas = driver.find_elements(By.CSS_SELECTOR, "textarea")
            logger.info(f"Found {len(textareas)} textarea elements")
            
            # Look for the one that's visible and in the main content area
            for i, textarea in enumerate(textareas):
                try:
                    if textarea.is_displayed() and textarea.is_enabled():
                        # Get placeholder or nearby text to identify the right one
                        placeholder = textarea.get_attribute('placeholder') or ''
                        aria_label = textarea.get_attribute('aria-label') or ''
                        
                        logger.info(f"Textarea {i}: placeholder='{placeholder}', aria-label='{aria_label}'")
                        
                        # Skip search bars and headers
                        parent_classes = textarea.get_attribute('class') or ''
                        if 'nav-search' in parent_classes or 'header' in parent_classes:
                            continue
                        
                        # This should be the URL input textarea
                        url_input = textarea
                        logger.info(f"Selected textarea {i} as URL input")
                        break
                except Exception as e:
                    logger.warning(f"Error checking textarea {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error finding textarea: {e}")
            return product_url
        
        if not url_input:
            logger.error("Could not find URL textarea")
            return product_url
        
        # Scroll to textarea and give it focus
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
