"""
PromoBot Main Orchestrator
Monitors Shopee/Mercado Livre for deals and sends notifications.
"""

import os
import time
import schedule
import requests
from typing import List, Dict
from dotenv import load_dotenv

from .database import init_database, is_deal_processed, save_deal
from .services import extract_deals_from_text, validate_deal, generate_link, send_deal, send_notification
from .utils.logger import logger

# Load environment variables
load_dotenv()


def fetch_raw_data(url: str) -> str:
    """
    Fetch raw data from a URL using Jina AI Reader.
    
    Jina AI Reader converts any URL to clean markdown.
    
    Args:
        url: URL to fetch
        
    Returns:
        Raw markdown text
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        logger.info(f"Fetching data from: {url}")
        
        response = requests.get(jina_url, timeout=30)
        response.raise_for_status()
        
        content = response.text
        logger.info(f"Fetched {len(content)} characters of content")
        return content
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from {url}: {e}")
        return ""


def process_deal(deal: Dict) -> bool:
    """
    Process a single deal: deduplicate, generate link, and send notification.
    
    Args:
        deal: Deal dictionary from AI processor
        
    Returns:
        True if deal was processed successfully, False otherwise
    """
    try:
        # Validate deal
        if not validate_deal(deal):
            logger.warning("Invalid deal, skipping")
            return False
        
        # Generate external ID from URL
        original_url = deal.get('original_url', '')
        external_id = original_url.split('/')[-1].split('?')[0]
        
        if not external_id:
            logger.warning("Could not generate external_id, skipping deal")
            return False
        
        # Check if already processed
        if is_deal_processed(external_id):
            logger.info(f"Deal already processed: {external_id}")
            return False
        
        # Generate affiliate link
        logger.info(f"Generating affiliate link for: {deal.get('title')}")
        affiliate_url = generate_link(original_url)
        
        if not affiliate_url:
            logger.warning("Failed to generate affiliate link, using original URL")
            affiliate_url = original_url
        
        deal['affiliate_url'] = affiliate_url
        
        # Send to Telegram
        if send_deal(deal):
            # Save to database
            save_deal(
                external_id=external_id,
                title=deal.get('title', ''),
                price=float(deal.get('new_price', 0)),
                original_url=original_url,
                affiliate_url=affiliate_url
            )
            logger.info(f"Deal processed successfully: {deal.get('title')}")
            return True
        else:
            logger.error("Failed to send deal to Telegram")
            return False
            
    except Exception as e:
        logger.error(f"Error processing deal: {e}")
        return False


def run_job():
    """
    Main job: Fetch data, extract deals, process them.
    """
    logger.info("=" * 60)
    logger.info("Starting PromoBot job...")
    logger.info("=" * 60)
    
    try:
        # Example URLs to monitor (you can make this configurable)
        urls_to_monitor = [
            "https://shopee.com.br/flash_sale",
            "https://www.mercadolivre.com.br/ofertas",
        ]
        
        total_deals_found = 0
        total_deals_sent = 0
        
        for url in urls_to_monitor:
            logger.info(f"Processing URL: {url}")
            
            # 1. Fetch raw data
            raw_data = fetch_raw_data(url)
            if not raw_data:
                logger.warning(f"No data fetched from {url}, skipping")
                continue
            
            # 2. Extract deals using AI
            deals = extract_deals_from_text(raw_data)
            total_deals_found += len(deals)
            
            if not deals:
                logger.info(f"No deals found in {url}")
                continue
            
            # 3. Process each deal
            for deal in deals:
                if process_deal(deal):
                    total_deals_sent += 1
                    # Add delay between deals to avoid rate limiting
                    time.sleep(2)
        
        logger.info("=" * 60)
        logger.info(f"Job completed: {total_deals_found} deals found, {total_deals_sent} sent")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in job execution: {e}")
        send_notification(f"⚠️ PromoBot Error: {str(e)}")


def main():
    """
    Main entry point.
    Initialize database and start scheduled jobs.
    """
    logger.info("=" * 60)
    logger.info("PromoBot MultiMarket Docker Gold - Starting...")
    logger.info("=" * 60)
    
    # Initialize database
    logger.info("Initializing database...")
    init_database()
    
    # Check configuration
    debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    if debug_mode:
        logger.warning("Running in DEBUG MODE - deals will not be sent to Telegram")
    
    # Send startup notification
    send_notification("🤖 PromoBot started successfully!")
    
    # Schedule job to run every hour
    schedule.every(1).hours.do(run_job)
    
    # Run immediately on startup
    logger.info("Running initial job...")
    run_job()
    
    # Keep running
    logger.info("Entering main loop. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Shutting down PromoBot...")
        send_notification("🛑 PromoBot stopped")


if __name__ == "__main__":
    main()
