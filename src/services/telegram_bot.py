"""
Telegram Bot service for sending deal notifications.
Supports DEBUG mode for testing without actually sending messages.
"""

import os
import requests
from typing import Dict, Optional
from ..utils.logger import logger


def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


import html
from ..utils.helpers import shorten_url

def format_deal_message(deal_data: Dict) -> str:
    """Format deal data into an attractive HTML message for Telegram."""
    title = html.escape(deal_data.get('title', 'Sem título'))
    old_price = float(deal_data.get('old_price', 0) or 0)
    new_price = float(deal_data.get('new_price', 0) or 0)
    affiliate_url = deal_data.get('affiliate_url', deal_data.get('original_url', ''))
    coupon_code = deal_data.get('coupon_code')
    coupon_discount = deal_data.get('coupon_discount')
    
    # Shorten URL
    short_url = shorten_url(affiliate_url)
    
    discount_pct = deal_data.get('discount_pct', 0)
    if discount_pct == 0 and old_price > new_price:
        discount_pct = round(((old_price - new_price) / old_price) * 100)

    # Store identification tag at the top
    store = deal_data.get('store', '')
    url_lower = str(deal_data.get('affiliate_url', deal_data.get('original_url', ''))).lower()
    store_lower = (store or '').lower()
    
    if 'shopee' in store_lower or 'shope.ee' in url_lower or 'shopee.com' in url_lower or 's.shopee' in url_lower:
        store_tag = "🟠 <b>SHOPEE</b>\n"
    elif 'mercado' in store_lower or 'mercadolivre' in url_lower or 'mercadolibre' in url_lower or 'meli.la' in url_lower:
        store_tag = "🟡 <b>MERCADO LIVRE</b>\n"
    elif 'amazon' in store_lower or 'amazon' in url_lower or 'amzn.to' in url_lower:
        store_tag = "🔵 <b>AMAZON</b>\n"
    elif store:
        store_tag = f"🏷️ <b>{html.escape(store.upper())}</b>\n"
    else:
        store_tag = "🛒 <b>OFERTA</b>\n"

    # Build message
    if discount_pct > 0:
        message = f"{store_tag}🔥 <b>OFERTA IMPERDÍVEL ({discount_pct}% OFF)!</b> 🔥\n\n"
    else:
        message = f"{store_tag}🔥 <b>OFERTA IMPERDÍVEL!</b> 🔥\n\n"
        
    message += f"📦 <b>{title}</b>\n\n"
    
    if old_price and old_price > new_price:
        savings = old_price - new_price
        message += f"❌ De: <s>R$ {old_price:.2f}</s>\n"
        message += f"✅ Por: <b>R$ {new_price:.2f}</b>\n"
        message += f"💰 <b>Economia de:</b> R$ {savings:.2f}\n\n"
    else:
        message += f"💵 <b>R$ {new_price:.2f}</b>\n\n"
    
    # Add coupon info if available
    if coupon_code:
        message += f"🎟️ <b>CUPOM:</b> <code>{html.escape(coupon_code)}</code>\n"
        if coupon_discount:
            message += f"💰 <b>Desconto Extra:</b> {coupon_discount:.0f}%\n\n"
        else:
            message += "\n"
    
    message += f'🛒 <a href="{short_url}"><b>Clique aqui para comprar</b></a>\n'
    message += f"<i>{short_url}</i>\n\n"
    message += "⚡ <i>Corre que é por tempo limitado!</i>"
    
    return message


def send_deal(deal_data: Dict, target_chat_id: Optional[str] = None) -> bool:
    """
    Send deal notification to Telegram.
    
    In DEBUG mode, only logs the deal without sending.
    In production mode, sends photo with caption or text to Telegram using HTML.
    
    Args:
        deal_data: Deal dictionary with title, price, image_url, affiliate_url, etc.
        target_chat_id: Optional specific chat_id to send to. If None, uses env var.
        
    Returns:
        True if successful, False otherwise
    """
    # Check DEBUG mode
    debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    if debug_mode:
        logger.info("=" * 50)
        logger.info(f"DEBUG MODE: Deal would be sent to Telegram (ChatID: {target_chat_id or 'ENV'})")
        logger.info(f"Title: {deal_data.get('title')}")
        logger.info(f"Price: R$ {deal_data.get('new_price', 0):.2f}")
        logger.info(f"Old Price: R$ {deal_data.get('old_price', 0):.2f}")
        logger.info(f"URL: {deal_data.get('affiliate_url', deal_data.get('original_url'))}")
        logger.info(f"Image: {deal_data.get('image_url', 'N/A')}")
        logger.info("=" * 50)
        return True
    
    # Production mode - send to Telegram
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = target_chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id or bot_token == 'seu_token':
            logger.error("Telegram credentials not configured")
            return False
        
        # Format message in HTML
        caption = format_deal_message(deal_data)
        image_url = deal_data.get('image_url')
        
        # Telegram API endpoint
        base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # 1. Try sending photo with caption if image available and caption <= 1024 chars
        if image_url and len(caption) <= 1024:
            try:
                url = f"{base_url}/sendPhoto"
                payload = {
                    'chat_id': chat_id,
                    'photo': image_url,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, json=payload, timeout=12)
                if response.status_code == 200:
                    logger.info(f"Deal sent to Telegram (photo): {deal_data.get('title')}")
                    return True
                else:
                    logger.warning(f"sendPhoto failed ({response.status_code}): {response.text[:150]}, falling back to text message...")
            except Exception as pe:
                logger.warning(f"Photo send error: {pe}, falling back to text message...")

        # 2. Fallback or primary: Send as HTML text message
        try:
            url = f"{base_url}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': caption,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                logger.info(f"Deal sent to Telegram (text): {deal_data.get('title')}")
                return True
            else:
                logger.error(f"sendMessage failed ({response.status_code}): {response.text[:200]}")
                return False
        except requests.exceptions.RequestException as te:
            logger.error(f"Failed to send text deal to Telegram: {te}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error sending deal to Telegram: {e}")
        return False


def send_notification(message: str) -> bool:
    """
    Send a simple text notification to Telegram.
    
    Args:
        message: Message to send
        
    Returns:
        True if successful, False otherwise
    """
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id or bot_token == 'seu_token':
            logger.warning("Telegram not configured, skipping notification")
            return False
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info("Notification sent to Telegram")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return False
