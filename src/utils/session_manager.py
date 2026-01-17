"""
Session Manager for handling browser cookies.
Saves and loads cookies to maintain login sessions across runs.
"""

import pickle
import os
from typing import Optional
from selenium import webdriver
from ..utils.logger import logger


class SessionManager:
    """Manages browser session persistence using cookies."""
    
    def __init__(self, cookies_file: str = 'data/cookies.pkl'):
        """
        Initialize SessionManager.
        
        Args:
            cookies_file: Path to the cookies file
        """
        self.cookies_file = cookies_file
        # Ensure data directory exists
        os.makedirs(os.path.dirname(cookies_file), exist_ok=True)
    
    def save_cookies(self, driver: webdriver.Chrome) -> None:
        """
        Save cookies from the current browser session.
        
        Args:
            driver: Selenium WebDriver instance
        """
        try:
            cookies = driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info(f"Cookies saved successfully to {self.cookies_file}")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
    
    def load_cookies(self, driver: webdriver.Chrome) -> bool:
        """
        Load cookies into the browser session.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            True if cookies were loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.cookies_file):
                logger.warning(f"Cookies file not found: {self.cookies_file}")
                return False
            
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Could not add cookie {cookie.get('name')}: {e}")
            
            logger.info(f"Cookies loaded successfully from {self.cookies_file}")
            return True
            
        except FileNotFoundError:
            logger.warning(f"Cookies file not found: {self.cookies_file}")
            return False
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False
    
    def clear_cookies(self) -> None:
        """Delete the cookies file."""
        try:
            if os.path.exists(self.cookies_file):
                os.remove(self.cookies_file)
                logger.info(f"Cookies file deleted: {self.cookies_file}")
        except Exception as e:
            logger.error(f"Failed to delete cookies file: {e}")
