
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
from ..utils.logger import logger

def get_driver():
    """
    Initializes and returns a Selenium WebDriver instance with local profile.
    """
    try:
        chrome_options = Options()
        chrome_bin = os.environ.get("CHROME_BIN")
        if chrome_bin:
            chrome_options.binary_location = chrome_bin
            
        # Headless mode for stability (no profile needed)
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Additional stability arguments
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.page_load_strategy = 'normal'
        
        if os.environ.get("CHROMEDRIVER_PATH"):
            service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
        else:
            service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Increase timeouts
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(30)
        
        # Stealth
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        logger.info("Chrome Driver initialized successfully (headless mode)")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Chrome Driver: {e}")
        return None

def fetch_html_selenium(url: str, driver=None) -> str:
    """
    Fetches raw HTML using Selenium with retry logic.
    If driver is provided, reuses it. Otherwise creates a new one (legacy mode).
    """
    should_quit = False
    if driver is None:
        driver = get_driver()
        should_quit = True
        
    if not driver:
        return ""

    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Navigating to: {url} (attempt {retry_count + 1}/{max_retries})")
            driver.get(url)
            
            # Wait for JS to load
            time.sleep(5) 
            
            # Scroll logic
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 1.5);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            html = driver.page_source
            
            if html and len(html) > 100:
                logger.info(f"Successfully fetched {len(html)} bytes")
                return html
            else:
                logger.warning(f"Page source too short, retrying...")
                retry_count += 1
                time.sleep(3)

        except Exception as e:
            retry_count += 1
            logger.error(f"Selenium error (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying in 5 seconds...")
                time.sleep(5)
                
                # Try to recover
                try:
                    driver.refresh()
                except:
                    # If refresh fails, reinitialize driver if we own it
                    if should_quit:
                        try:
                            driver.quit()
                        except:
                            pass
                        driver = get_driver()
                        if not driver:
                            return ""
            else:
                logger.error(f"Max retries reached for {url}")
        
    # Cleanup if we own the driver
    if should_quit and driver:
        try:
            driver.quit()
        except:
            pass
            
    return ""
