"""
Browser driver setup with MAXIMUM STEALTH configuration.
Uses Chrome/Chromium with advanced anti-detection measures.
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from ..utils.logger import logger


def setup_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Setup Chrome WebDriver with maximum stealth configuration.
    
    This configuration includes:
    1. Modern headless mode (--headless=new)
    2. Disabled automation flags
    3. Realistic user agent
    4. Various anti-detection measures
    
    Args:
        headless: Whether to run in headless mode (default: True)
        
    Returns:
        Configured Chrome WebDriver instance
    """
    logger.info("Setting up Chrome WebDriver with stealth configuration...")
    
    # Chrome options
    chrome_options = Options()
    
    # 1. Use new headless mode (better than old --headless)
    if headless:
        chrome_options.add_argument('--headless=new')
    
    # 2. CRUCIAL: Disable automation flags to hide Selenium
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # 3. Set realistic User-Agent
    ua = UserAgent()
    user_agent = ua.random
    chrome_options.add_argument(f'user-agent={user_agent}')
    logger.debug(f"Using User-Agent: {user_agent}")
    
    # 4. Additional stealth arguments
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    
    # 5. Window size (important for rendering)
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    
    # 6. Language and encoding
    chrome_options.add_argument('--lang=pt-BR')
    chrome_options.add_experimental_option('prefs', {
        'intl.accept_languages': 'pt-BR,pt,en-US,en'
    })
    
    # 7. Exclude automation switches
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 8. Set binary location if specified in environment
    chrome_bin = os.getenv('CHROME_BIN')
    if chrome_bin:
        chrome_options.binary_location = chrome_bin
        logger.debug(f"Using Chrome binary: {chrome_bin}")
    
    # 9. Set chromedriver path if specified in environment
    chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
    service = None
    if chromedriver_path:
        service = Service(executable_path=chromedriver_path)
        logger.debug(f"Using ChromeDriver: {chromedriver_path}")
    
    # Create driver
    try:
        if service:
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        # 10. Execute CDP commands to further hide automation
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Chrome WebDriver setup completed successfully")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to setup Chrome WebDriver: {e}")
        raise


def quit_driver(driver: webdriver.Chrome) -> None:
    """
    Safely quit the WebDriver.
    
    Args:
        driver: Chrome WebDriver instance to quit
    """
    try:
        if driver:
            driver.quit()
            logger.info("Chrome WebDriver closed successfully")
    except Exception as e:
        logger.error(f"Error closing WebDriver: {e}")
