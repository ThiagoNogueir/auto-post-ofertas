
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
from ..utils.logger import logger

def fetch_html_selenium(url: str) -> str:
    """
    Fetches raw HTML using a headless Chrome browser.
    Essential for SPA sites like Shopee that require JS.
    """
    driver = None
    try:
        logger.info(f"Starting Selenium fetch for: {url}")
        
        chrome_options = Options()
        chrome_bin = os.environ.get("CHROME_BIN")
        if chrome_bin:
            chrome_options.binary_location = chrome_bin
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if os.environ.get("CHROMEDRIVER_PATH"):
            service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
        else:
            service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Stealth: Remove navigator.webdriver flag
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        driver.get(url)
        
        # Wait for JS to load - increased time for ML/Shopee
        logger.info("Waiting for page to load...")
        time.sleep(8)  # Increased from 5 to 8 seconds
        
        # Try to wait for product elements to appear (ML specific)
        if 'mercadolivre.com' in url:
            try:
                # Wait up to 15 seconds for product cards to appear
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                
                wait = WebDriverWait(driver, 15)
                # Wait for actual product cards (POLYCARD is the React component ML uses)
                # Try multiple selectors as ML changes their structure
                selectors_to_try = [
                    "div[id='POLYCARD']",  # New React component
                    "li.ui-search-layout__item",  # Classic layout
                    "ol.ui-search-layout",  # Container
                    "div.poly-card"  # Alternative
                ]
                
                element_found = False
                for selector in selectors_to_try:
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        logger.info(f"Product elements detected using selector: {selector}")
                        element_found = True
                        break
                    except:
                        continue
                
                if not element_found:
                    logger.warning("No product elements detected with any selector")
                    
            except Exception as e:
                logger.warning(f"Timeout waiting for products: {e}")
        
        # Additional wait for JS to finish rendering
        time.sleep(3)
        
        # Scroll down progressively to trigger ALL lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 1.5);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        html = driver.page_source
        
        # DEBUG: Save HTML to file for inspection (TEMPORARY)
        if 'mercadolivre.com' in url:
            try:
                debug_path = os.path.join('logs', 'ml_debug.html')
                with open(debug_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.info(f"Saved HTML to {debug_path} for inspection")
            except Exception as e:
                logger.warning(f"Could not save debug HTML: {e}")
        
        
        
        # Return full HTML for the parser
        logger.info(f"Selenium fetched {len(html)} characters")
        return html

    except Exception as e:
        logger.error(f"Selenium error fetching {url}: {e}")
        return ""
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
