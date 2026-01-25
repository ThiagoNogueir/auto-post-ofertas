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
from .services import validate_deal, send_deal, send_notification, send_deal_to_whatsapp
import json
from .utils.helpers import extract_product_id

from .services.parser import extract_deals_from_html
from .services.simple_affiliate import generate_simple_link as generate_link
from .utils.logger import logger
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
        external_id = extract_product_id(original_url)
        
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
        
        # Validate HTTPS - Skip products without HTTPS
        if not affiliate_url.startswith('https://'):
            logger.warning(f"Product link does not use HTTPS, skipping: {deal.get('title')}")
            logger.warning(f"URL: {affiliate_url}")
            return False
        
        deal['affiliate_url'] = affiliate_url
        
        # Determine store name
        # Determine store name
        store_name = 'Outros'
        if 'mercadolivre.com' in original_url:
            store_name = 'Mercado Livre'
        elif 'shopee.com' in original_url:
            store_name = 'Shopee'
            
        # --- Channel Routing Logic ---
        
        # Load config
        groups_config = {}
        try:
            if os.path.exists('groups_config.json'):
                with open('groups_config.json', 'r', encoding='utf-8') as f:
                    groups_config = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load groups_config.json: {e}")
            
        routing = groups_config.get('category_routing', {})
        enabled = routing.get('enabled', False)
        send_telegram = routing.get('send_to_telegram', True)
        send_whatsapp = routing.get('send_to_whatsapp', False)
        
        category = deal.get('category', 'Outros')
        
        telegram_sent = False
        whatsapp_sent = False
        
        # 1. Send to Telegram if enabled
        if send_telegram:
            tg_groups = groups_config.get('telegram_groups', {})
            # Try specific category group, fallback to default
            tg_chat_id = tg_groups.get(category, tg_groups.get('default'))
            
            # If empty in config JSON, send_deal will fallback to .env variable
            # But let's log what we are doing
            if tg_chat_id:
                logger.info(f"Sending to Telegram Group: {tg_chat_id}")
            else:
                logger.info(f"Sending to Telegram Default (ENV)")

            if send_deal(deal, target_chat_id=tg_chat_id):
                telegram_sent = True
        
        # 2. Send to WhatsApp if enabled
        if send_whatsapp:
            logger.info(f"Attempting to send to WhatsApp (Category: {category})")
            try:
                wa_groups = groups_config.get('whatsapp_groups', {})
                # Try specific category group, fallback to default
                group_id = wa_groups.get(category, wa_groups.get('default'))
                
                if group_id:
                    logger.info(f"Sending to WhatsApp Group: {group_id}")
                    wa_result = send_deal_to_whatsapp(
                        group_id=group_id,
                        title=deal.get('title', ''),
                        price=float(deal.get('new_price', 0)),
                        old_price=float(deal.get('old_price', 0) or 0),
                        url=affiliate_url,
                        image_url=deal.get('image_url')
                    )
                    if wa_result:
                        whatsapp_sent = True
                        logger.info("WhatsApp send SUCCESS")
                    else:
                        logger.error("WhatsApp send FAILED (API returned False)")
                else:
                    logger.warning(f"No WhatsApp group configured for category '{category}' and no default")
            except Exception as e:
                logger.error(f"Error sending to WhatsApp: {e}")

        # 3. Always save to database so we can see in dashboard
        # But log the delivery status
        save_deal(
            external_id=external_id,
            title=deal.get('title', ''),
            price=float(deal.get('new_price', 0)),
            original_url=original_url,
            affiliate_url=affiliate_url,
            image_url=deal.get('image_url'),
            category=category,
            store=store_name
        )
        logger.info(f"Deal saved to DB: {deal.get('title')} (TG: {telegram_sent}, WA: {whatsapp_sent})")
        return True
            
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
        # Example URLs to monitor (you can make this configurable)
        # Monitor main offers AND specific categories for better deal finding
        urls_to_monitor = [
            # --- Mercado Livre (Categorias Solicitadas - Mais Vendidos) ---
            
            # Tecnologia - Celulares
            "https://lista.mercadolivre.com.br/celulares-telefones/_Orden_sold_quantity",
            
            # Tecnologia - Computadores
            "https://lista.mercadolivre.com.br/computadores/_Orden_sold_quantity",
            
            # Esportes - Suplementos
            "https://lista.mercadolivre.com.br/saude/suplementos-alimentares/_Orden_sold_quantity",
            
            # Pet Shop
            "https://lista.mercadolivre.com.br/animais/_Orden_sold_quantity",
            
            # Moda
            "https://lista.mercadolivre.com.br/calcados-roupas-bolsas/_Orden_sold_quantity",
            
            # --- Shopee (Mantendo busca por relevância) ---
            "https://shopee.com.br/search?keyword=celular&sortBy=sales",
            "https://shopee.com.br/search?keyword=notebook&sortBy=sales",
            "https://shopee.com.br/search?keyword=game&sortBy=sales",
        ]
        
        total_deals_found = 0
        total_deals_sent = 0
        
        # Initialize Driver ONCE
        from .services.simple_scraper_selenium import get_driver
        logger.info("Initializing Single Chrome Driver...")
        driver = get_driver()
        
        if not driver:
            logger.error("Failed to initialize driver. Aborting job.")
            return

        try:
            for url in urls_to_monitor:
                logger.info(f"Processing URL: {url}")
                
                # 1. Fetch raw data (reusing driver)
                raw_data = fetch_html_selenium(url, driver=driver)
                
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
        finally:
            logger.info("Closing Chrome Driver...")
            if driver:
                driver.quit()
        
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
    # API Server is running separately via iniciar_bot.bat
    # Logic removed to avoid port conflict (Address already in use)

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
