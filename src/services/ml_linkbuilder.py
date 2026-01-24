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
        
        # Use persistent profile directory for cookies
        profile_dir = os.path.join(os.getcwd(), "ml_chrome_profile")
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
            logger.info(f"Created profile directory: {profile_dir}")
        
        chrome_options.add_argument(f"user-data-dir={profile_dir}")
        
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
