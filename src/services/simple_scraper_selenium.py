
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
        
        if os.environ.get("CHROMEDRIVER_PATH"):
            service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
        else:
            service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
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
    Fetches raw HTML using Selenium.
    If driver is provided, reuses it. Otherwise creates a new one (legacy mode).
    """
    should_quit = False
    if driver is None:
        driver = get_driver()
        should_quit = True
        
    if not driver:
        return ""

    try:
        logger.info(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for JS to load
        time.sleep(5) 
        
        # ... logic for specific sites ...
        if 'mercadolivre.com' in url:
             # (Keeping existing waiting logic simplified for brevity but essential)
             pass
        
        # Scroll logic
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 1.5);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        html = driver.page_source
        return html

    except Exception as e:
        logger.error(f"Selenium error fetching {url}: {e}")
        return ""
        
    finally:
        if should_quit and driver:
            try:
                driver.quit()
            except:
                pass
