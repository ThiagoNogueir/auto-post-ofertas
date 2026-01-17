"""
Link Generator using Selenium.
Handles login and affiliate link generation for Shopee/Mercado Livre.
"""

import os
import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from ..browser.driver_setup import setup_driver, quit_driver
from ..utils.session_manager import SessionManager
from ..utils.logger import logger


class LinkGenerator:
    """Handles affiliate link generation with session management."""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.driver = None
    
    def _ensure_driver(self):
        """Ensure driver is initialized."""
        if self.driver is None:
            self.driver = setup_driver(headless=True)
    
    def _is_logged_in(self) -> bool:
        """
        Check if user is logged in to Shopee.
        
        Returns:
            True if logged in, False otherwise
        """
        try:
            # Navigate to Shopee homepage
            self.driver.get("https://shopee.com.br")
            time.sleep(2)
            
            # Check for login indicators (adjust selectors as needed)
            # This is a placeholder - you'll need to adjust based on actual Shopee structure
            try:
                self.driver.find_element(By.CSS_SELECTOR, "[data-testid='account-menu']")
                logger.info("User is logged in")
                return True
            except NoSuchElementException:
                logger.info("User is not logged in")
                return False
                
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def _perform_login(self) -> bool:
        """
        Perform login to Shopee.
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            email = os.getenv('SHOPEE_LOGIN')
            password = os.getenv('SHOPEE_PASS')
            
            if not email or not password or email == 'email':
                logger.error("Shopee credentials not configured")
                return False
            
            logger.info("Attempting to login to Shopee...")
            
            # Navigate to login page
            self.driver.get("https://shopee.com.br/buyer/login")
            time.sleep(2)
            
            # Fill login form (adjust selectors as needed)
            # This is a placeholder - you'll need to adjust based on actual Shopee structure
            try:
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "loginKey"))
                )
                email_input.send_keys(email)
                
                password_input = self.driver.find_element(By.NAME, "password")
                password_input.send_keys(password)
                
                # Click login button
                login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_button.click()
                
                # Wait for login to complete
                time.sleep(5)
                
                # Verify login
                if self._is_logged_in():
                    logger.info("Login successful")
                    self.session_manager.save_cookies(self.driver)
                    return True
                else:
                    logger.error("Login failed")
                    return False
                    
            except TimeoutException:
                logger.error("Login form elements not found")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def generate_affiliate_link(self, product_url: str) -> Optional[str]:
        """
        Generate affiliate link for a product.
        
        Args:
            product_url: Original product URL
            
        Returns:
            Affiliate link or None if generation failed
        """
        try:
            self._ensure_driver()
            
            # Load cookies
            self.driver.get("https://shopee.com.br")
            time.sleep(1)
            self.session_manager.load_cookies(self.driver)
            self.driver.refresh()
            time.sleep(2)
            
            # Check if logged in
            if not self._is_logged_in():
                logger.warning("Not logged in, attempting login...")
                if not self._perform_login():
                    logger.error("Cannot generate link: login failed")
                    return None
            
            # Navigate to affiliate link generator page
            # This is a placeholder - adjust based on actual Shopee affiliate program
            logger.info(f"Generating affiliate link for: {product_url}")
            
            # For now, return the original URL with a tracking parameter
            # You'll need to implement the actual affiliate link generation logic
            affiliate_url = f"{product_url}?affiliate_id=promobot"
            
            logger.info(f"Generated affiliate link: {affiliate_url}")
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Error generating affiliate link: {e}")
            return None
    
    def close(self):
        """Close the driver."""
        if self.driver:
            quit_driver(self.driver)
            self.driver = None


def generate_link(product_url: str) -> Optional[str]:
    """
    Convenience function to generate an affiliate link.
    
    Args:
        product_url: Original product URL
        
    Returns:
        Affiliate link or None if generation failed
    """
    generator = LinkGenerator()
    try:
        return generator.generate_affiliate_link(product_url)
    finally:
        generator.close()
