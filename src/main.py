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

TECH_CATEGORIES = {'Celulares', 'Informática', 'Eletrônicos', 'Games'}
CASA_CATEGORIES = {'Casa', 'Construção'}
BELEZA_CATEGORIES = {'Beleza', 'Saúde'}
MERCADO_CATEGORIES = {'Bebidas', 'Alimentos'}
MODA_CATEGORIES = {'Moda', 'Esportes'}
PETS_CATEGORIES = {'Pets'}
KIDS_CATEGORIES = {'Bebês', 'Brinquedos'}
AUTO_CATEGORIES = {'Ferramentas', 'Automotivo'}
ALL_NICHES = TECH_CATEGORIES | CASA_CATEGORIES | BELEZA_CATEGORIES | MERCADO_CATEGORIES | MODA_CATEGORIES | PETS_CATEGORIES | KIDS_CATEGORIES | AUTO_CATEGORIES

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
        deal_title = deal.get('title', '').strip()
        
        if not external_id:
            logger.warning("Could not generate external_id, skipping deal")
            return False
        
        # Check if already processed by ID or Title (prevents duplicates)
        if is_deal_processed(external_id, title=deal_title):
            logger.info(f"Deal already processed: {external_id} - {deal_title[:30]}")
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
        store_name = 'Outros'
        if 'mercadolivre.com' in original_url or 'mercadolibre.com' in original_url or 'meli.la' in original_url:
            store_name = 'Mercado Livre'
        elif 'shopee.com' in original_url or 'shope.ee' in original_url or 's.shopee' in original_url:
            store_name = 'Shopee'
        elif 'amazon.com' in original_url or 'amzn.to' in original_url:
            store_name = 'Amazon'
            
        deal['store'] = store_name
            
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
        niche_mode = routing.get('niche_mode', True)
        
        category = deal.get('category', 'Outros')
        
        # In niche mode, skip items that couldn't be classified into one of the curated niches
        if category == 'Outros' or category not in ALL_NICHES:
            logger.info(f"Skipping deal with unmapped/generic category: '{category}' - {deal_title}")
            return False
            
        telegram_sent = False
        whatsapp_sent = False
        
        # Niche routing:
        # Telegram receives Tech & Setup (Celulares, Informática, Eletrônicos, Games)
        # WhatsApp receives all 8 specialized groups (Tech, Casa, Beleza, Mercado, Moda, Pets, Bebês, Ferramentas)
        is_tech = category in TECH_CATEGORIES
        wa_groups = groups_config.get('whatsapp_groups', {})
        has_wa_group = bool(wa_groups.get(category))

        can_send_telegram = send_telegram and (is_tech or not niche_mode)
        can_send_whatsapp = send_whatsapp and has_wa_group
        
        # 1. Send to Telegram if enabled and matches Tech niche
        if can_send_telegram:
            tg_groups = groups_config.get('telegram_groups', {})
            
            # For Shopee products, try Shopee-specific groups first
            if store_name == 'Shopee':
                # Try Shopee_Category format first (e.g., Shopee_Celulares)
                shopee_category_key = f'Shopee_{category}'
                tg_chat_id = tg_groups.get(shopee_category_key)
                
                # If not found, try Shopee_Default
                if not tg_chat_id:
                    tg_chat_id = tg_groups.get('Shopee_Default')
                
                # If still not found, fallback to general category
                if not tg_chat_id:
                    tg_chat_id = tg_groups.get(category, tg_groups.get('default'))
                    
                logger.info(f"Shopee product - Using Telegram group: {tg_chat_id or 'ENV default'}")
            else:
                # For non-Shopee (ML, etc), use general category groups
                tg_chat_id = tg_groups.get(category, tg_groups.get('default'))
                logger.info(f"{store_name} product - Using Telegram group: {tg_chat_id or 'ENV default'}")

            if send_deal(deal, target_chat_id=tg_chat_id):
                telegram_sent = True

            # Broadcast to individual subscribers for this category
            try:
                from .database import get_subscribers_for_category
                sub_ids = get_subscribers_for_category(category)
                if sub_ids:
                    logger.info(f"Broadcasting deal ({category}) to {len(sub_ids)} individual subscribers...")
                    for s_id in sub_ids:
                        if str(s_id) != str(tg_chat_id):
                            send_deal(deal, target_chat_id=s_id)
                            time.sleep(0.3)
            except Exception as se:
                logger.error(f"Error broadcasting to subscribers: {se}")
        
        # 2. Send to WhatsApp if enabled and matches Casa/Mercado niche
        if can_send_whatsapp:
            logger.info(f"Attempting to send to WhatsApp (Store: {store_name}, Category: {category})")
            try:
                wa_groups = groups_config.get('whatsapp_groups', {})
                
                # For Shopee products, try Shopee-specific groups first
                if store_name == 'Shopee':
                    # Try Shopee_Category format first (e.g., Shopee_Celulares)
                    shopee_category_key = f'Shopee_{category}'
                    group_id = wa_groups.get(shopee_category_key)
                    
                    # If not found, try Shopee_Default
                    if not group_id:
                        group_id = wa_groups.get('Shopee_Default')
                    
                    # If still not found, fallback to general category
                    if not group_id:
                        group_id = wa_groups.get(category, wa_groups.get('default'))
                        
                    logger.info(f"Shopee product - Using WhatsApp group: {group_id or 'none'}")
                else:
                    # For non-Shopee (ML, etc), use general category groups
                    group_id = wa_groups.get(category, wa_groups.get('default'))
                    logger.info(f"{store_name} product - Using WhatsApp group: {group_id or 'none'}")
                
                if group_id:
                    logger.info(f"Sending to WhatsApp Group: {group_id}")
                    wa_result = send_deal_to_whatsapp(
                        group_id=group_id,
                        title=deal.get('title', ''),
                        price=float(deal.get('new_price', 0)),
                        old_price=float(deal.get('old_price', 0) or 0),
                        url=affiliate_url,
                        image_url=deal.get('image_url'),
                        store=store_name
                    )
                    if wa_result:
                        whatsapp_sent = True
                        logger.info("WhatsApp send SUCCESS")
                    else:
                        logger.error("WhatsApp send FAILED (API returned False)")
                else:
                    logger.warning(f"No WhatsApp group configured for {store_name} - {category}")
            except Exception as e:
                logger.error(f"Error sending to WhatsApp: {e}")

        # 3. Send to Pinterest if configured
        pinterest_sent = False
        try:
            from .services.pinterest_api import PinterestAPI
            pin_api = PinterestAPI()
            if pin_api.is_configured():
                pinterest_sent = pin_api.create_pin(
                    title=deal.get('title', ''),
                    price=float(deal.get('new_price', 0)),
                    old_price=float(deal.get('old_price', 0) or 0),
                    affiliate_url=affiliate_url,
                    image_url=deal.get('image_url'),
                    category=category,
                    store=store_name,
                    coupon_code=deal.get('coupon_code')
                )
        except Exception as pe:
            logger.debug(f"Pinterest post skipped: {pe}")

        # 4. Always save to database so we can see in dashboard
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
        # Load URLs from config file
        urls_config_path = os.path.join(os.path.dirname(__file__), '..', 'urls_config.json')
        urls_to_monitor = []
        
        try:
            if os.path.exists(urls_config_path):
                with open(urls_config_path, 'r', encoding='utf-8') as f:
                    urls_config = json.load(f)
                    urls_to_monitor = urls_config.get('urls_to_monitor', [])
                    
                    # Filter out empty strings
                    urls_to_monitor = [url for url in urls_to_monitor if url and url.strip()]
                    
                    if urls_to_monitor:
                        logger.info(f"Loaded {len(urls_to_monitor)} URLs from config")
                    else:
                        logger.warning("Config file exists but has no valid URLs")
            else:
                logger.warning("URLs config file not found")
                
        except Exception as e:
            logger.error(f"Error loading URLs config: {e}")
        
        # Fallback to default URLs if none loaded
        if not urls_to_monitor:
            urls_to_monitor = [
                "https://lista.mercadolivre.com.br/celulares-telefones/_Orden_sold_quantity",
                "https://lista.mercadolivre.com.br/computadores/_Orden_sold_quantity",
                "https://lista.mercadolivre.com.br/saude/suplementos-alimentares/_Orden_sold_quantity",
                "https://lista.mercadolivre.com.br/animais/_Orden_sold_quantity",
                "https://lista.mercadolivre.com.br/calcados-roupas-bolsas/_Orden_sold_quantity"
            ]
            logger.warning(f"Using fallback URLs: {len(urls_to_monitor)} URLs")
        
        total_deals_found = 0
        total_deals_sent = 0
        collected_candidates = []
        
        driver = None

        from .utils.helpers import get_url_page, set_url_page, get_paginated_url

        try:
            for url in urls_to_monitor:
                current_page = get_url_page(url)
                logger.info(f"Processing URL: {url} (Continuing from Page {current_page})")
                
                pages_checked = 0
                max_pages_per_run = 2 if 'mercadolivre.com' in url else 1
                
                while pages_checked < max_pages_per_run:
                    target_url = get_paginated_url(url, current_page)
                    logger.info(f"Fetching: {target_url} (Page {current_page})")
                    
                    raw_data = fetch_html_selenium(target_url, driver=driver)
                    if not raw_data:
                        logger.warning(f"No data fetched from {target_url}, skipping")
                        break
                        
                    deals = extract_deals_from_html(raw_data, target_url)
                    total_deals_found += len(deals)
                    
                    if not deals:
                        logger.info(f"No deals found on page {current_page}, resetting to page 1 for next run")
                        set_url_page(url, 1)
                        break
                        
                    # Pre-validate and collect qualified deals for curation
                    for deal in deals:
                        if validate_deal(deal):
                            ext_id = extract_product_id(deal.get('original_url', ''))
                            if ext_id and not is_deal_processed(ext_id, title=deal.get('title', '')):
                                if not any(extract_product_id(c.get('original_url', '')) == ext_id for c in collected_candidates):
                                    collected_candidates.append(deal)
                    
                    # Advance page for rotation in next run
                    next_page = current_page + 1 if current_page < 5 else 1
                    set_url_page(url, next_page)
                    pages_checked += 1
                    break
        finally:
            if driver:
                logger.info("Closing Chrome Driver...")
                try:
                    driver.quit()
                except Exception:
                    pass
            import gc
            gc.collect()

        # --- Shopee Affiliate API Offers Fetching ---
        try:
            from .services.shopee_api import ShopeeAffiliateAPI
            shopee_api = ShopeeAffiliateAPI()
            if shopee_api.is_configured():
                logger.info("Shopee Open API active! Fetching category offers from Shopee...")
                shopee_keywords = [
                    ("pc gamer", "Games"),
                    ("placa de video", "Informática"),
                    ("teclado mecanico", "Informática"),
                    ("casa e decoracao", "Casa"),
                    ("perfume importado", "Beleza"),
                    ("whisky", "Bebidas")
                ]
                for kw, cat in shopee_keywords:
                    shp_deals = shopee_api.fetch_offers(keyword=kw, limit=5)
                    for d in shp_deals:
                        d['category'] = cat
                        if validate_deal(d):
                            ext_id = extract_product_id(d.get('original_url', ''))
                            if ext_id and not is_deal_processed(ext_id, title=d.get('title', '')):
                                if not any(extract_product_id(c.get('original_url', '')) == ext_id for c in collected_candidates):
                                    collected_candidates.append(d)
                                    total_deals_found += 1
            else:
                logger.debug("Shopee Open API not configured in .env (SHOPEE_APP_ID / SHOPEE_SECRET)")
        except Exception as se:
            logger.warning(f"Shopee API fetch error: {se}")

        # --- Curation & Rate Limiter: Dispatch only TOP deals per run ---
        if collected_candidates:
            # Sort candidates by discount percentage (highest discount first)
            collected_candidates.sort(key=lambda d: d.get('discount_pct', 0), reverse=True)
            
            # Read limits from config (default max 1 deal per niche group per cycle)
            max_per_group = urls_config.get('max_deals_per_group', 1)
            max_telegram = urls_config.get('max_deals_per_run_telegram', 2)
            
            GROUPS_CLUSTERS = {
                'Tech & Games': TECH_CATEGORIES,
                'Casa & Decoração': CASA_CATEGORIES,
                'Beleza & Perfumaria': BELEZA_CATEGORIES,
                'Mercado & Bebidas': MERCADO_CATEGORIES,
                'Moda & Calçados': MODA_CATEGORIES,
                'Pet Shop': PETS_CATEGORIES,
                'Bebês & Brinquedos': KIDS_CATEGORIES,
                'Ferramentas & Automotivo': AUTO_CATEGORIES
            }
            
            dispatched_ids = set()
            
            # 1. Dispatch to Telegram (Top Tech deals)
            top_tech = [d for d in collected_candidates if d.get('category') in TECH_CATEGORIES][:max_telegram]
            for deal in top_tech:
                ext_id = extract_product_id(deal.get('original_url', ''))
                if ext_id not in dispatched_ids:
                    if process_deal(deal):
                        total_deals_sent += 1
                        dispatched_ids.add(ext_id)
                        time.sleep(3)
                        
            # 2. Dispatch to each WhatsApp group (Top deal in that cluster)
            for cluster_name, cats in GROUPS_CLUSTERS.items():
                cluster_deals = [d for d in collected_candidates if d.get('category') in cats and extract_product_id(d.get('original_url', '')) not in dispatched_ids]
                for deal in cluster_deals[:max_per_group]:
                    ext_id = extract_product_id(deal.get('original_url', ''))
                    if process_deal(deal):
                        total_deals_sent += 1
                        dispatched_ids.add(ext_id)
                        time.sleep(3)
        else:
            logger.info("No new deals meeting the discount, niche and ticket criteria in this cycle.")
        
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
    
    # Start Telegram Subscriber Listener Thread
    from .services import start_subscriber_listener_thread
    start_subscriber_listener_thread()
    
    # Check configuration
    debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    if debug_mode:
        logger.warning("Running in DEBUG MODE - deals will not be sent to Telegram")
    
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


if __name__ == "__main__":
    main()
