import os
import time
from bs4 import BeautifulSoup
from ..utils.logger import logger

def fetch_html_fast(url: str) -> str:
    """
    Fetches raw HTML using curl_cffi with Chrome impersonation.
    Extremely fast (~1-2s) and consumes only ~15MB RAM (avoids Render 512MB OOM crashes).
    """
    try:
        from curl_cffi import requests as cffi_requests
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        response = cffi_requests.get(url, impersonate="chrome120", timeout=15, headers=headers)
        if response.status_code == 200 and len(response.text) > 2000:
            logger.info(f"Fast Engine successfully fetched {len(response.text)} bytes for {url}")
            return response.text
        else:
            logger.warning(f"Fast Engine got status {response.status_code} ({len(response.text)} bytes) for {url}")
    except Exception as e:
        logger.debug(f"Fast Engine not available or error for {url}: {e}")
    return ""


def get_driver():
    """
    Initializes and returns a Selenium WebDriver instance with low-memory configuration.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        chrome_bin = os.environ.get("CHROME_BIN")
        if chrome_bin:
            chrome_options.binary_location = chrome_bin
            
        # Headless mode with ultra-low memory usage for Render Free Tier (512MB RAM cap)
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,720")
        chrome_options.add_argument("--renderer-process-limit=1")
        chrome_options.add_argument("--js-flags=--max-old-space-size=128")
        chrome_options.add_argument("--disable-features=AudioServiceOutOfProcess,IsolateOrigins,site-per-process")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Additional stability arguments
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.page_load_strategy = 'normal'
        
        if os.environ.get("CHROMEDRIVER_PATH"):
            service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
        else:
            service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(45)
        driver.set_script_timeout(20)
        
        # Stealth
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        logger.info("Chrome Driver initialized successfully (low-memory headless mode)")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Chrome Driver: {e}")
        return None


def fetch_html_selenium(url: str, driver=None) -> str:
    """
    Fetches raw HTML using Fast Engine first (< 15MB RAM).
    Falls back to Selenium only if Fast Engine fails or returns empty.
    """
    # 1. Primary: Fast Engine (Low memory, prevents Render crashes)
    fast_html = fetch_html_fast(url)
    if fast_html:
        return fast_html
        
    # 2. Fallback: Selenium WebDriver
    logger.info(f"Falling back to Selenium for: {url}")
    should_quit = False
    if driver is None:
        driver = get_driver()
        should_quit = True
        
    if not driver:
        return ""

    max_retries = 2
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Navigating to: {url} (Selenium attempt {retry_count + 1}/{max_retries})")
            driver.get(url)
            
            # Wait for JS to load
            time.sleep(3) 
            
            # Simple scroll
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            html = driver.page_source
            
            if html and len(html) > 100:
                logger.info(f"Successfully fetched {len(html)} bytes via Selenium")
                return html
            else:
                logger.warning("Page source too short, retrying...")
                retry_count += 1
                time.sleep(2)

        except Exception as e:
            retry_count += 1
            logger.error(f"Selenium error (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                time.sleep(3)
        
    # Cleanup if we own the driver
    if should_quit and driver:
        try:
            driver.quit()
        except Exception:
            pass
            
    return ""
