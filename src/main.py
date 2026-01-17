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
from .database import init_database, is_deal_processed, save_deal
from .services import validate_deal, send_deal, send_notification
from .services.parser import extract_deals_from_html
from .services.simple_affiliate import generate_simple_link as generate_link
from .utils.logger import logger

# Load environment variables
from .services.simple_scraper_selenium import fetch_html_selenium

def fetch_raw_data(url: str) -> str:
    """
    Fetch raw HTML using Selenium to handle JS-heavy sites (Shopee).
    """
    return fetch_html_selenium(url)


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
        
        # Determine store name
        store_name = 'Outros'
        if 'mercadolivre.com' in original_url:
            store_name = 'Mercado Livre'
        elif 'shopee.com' in original_url:
            store_name = 'Shopee'
            
        # Send to Telegram
        if send_deal(deal):
            # Save to database
            save_deal(
                external_id=external_id,
                title=deal.get('title', ''),
                price=float(deal.get('new_price', 0)),
                original_url=original_url,
                affiliate_url=affiliate_url,
                image_url=deal.get('image_url'),
                category=deal.get('category', 'Outros'),
                store=store_name
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
        # Monitor main offers AND specific categories for better deal finding
        urls_to_monitor = [
            # --- Mercado Livre  ---
            "https://lista.mercadolivre.com.br/ofertas",
            "https://lista.mercadolivre.com.br/celulares-telefones/_Discount_5-100", # Filtro de desconto ativo
            "https://lista.mercadolivre.com.br/informatica/_Discount_5-100",
            "https://lista.mercadolivre.com.br/games/_Discount_5-100",
            
            # --- Shopee (Busca com filtro de desconto/relevancia) ---
            "https://shopee.com.br/search?keyword=celular&sortBy=sales",
            "https://shopee.com.br/search?keyword=notebook&sortBy=sales",
            "https://shopee.com.br/search?keyword=game&sortBy=sales",
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
            
            # 2. Extract deals using Parser (No AI)
            deals = extract_deals_from_html(raw_data, url)
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
    
    # Start API in a separate thread (if not already running)
    try:
        import threading
        from api.app import app
        def run_api():
            app.run(host='0.0.0.0', port=8000, use_reloader=False) # use_reloader=False is important for threads
        
        api_thread = threading.Thread(target=run_api)
        api_thread.daemon = True
        api_thread.start()
        logger.info("API Server started on port 8000")
    except Exception as e:
        logger.error(f"Failed to start API thread: {e}")

    # Import config manager
    from src.utils.config_manager import should_run, update_last_run
    
    # Run immediately on startup
    logger.info("Running initial job...")
    run_job()
    update_last_run()
    
    # Keep running
    logger.info("Entering dynamic main loop. Press Ctrl+C to stop.")
    try:
        while True:
            if should_run():
                logger.info("Triggering scheduled job...")
                run_job()
                update_last_run()
            
            time.sleep(5)  # Check every 5 seconds for force_run or timeout
    except KeyboardInterrupt:
        logger.info("Shutting down PromoBot...")

        send_notification("🛑 PromoBot stopped")


if __name__ == "__main__":
    main()
