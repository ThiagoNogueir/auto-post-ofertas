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


def format_deal_message(deal_data: Dict) -> str:
    """
    Format deal data into a Telegram message.
    
    Args:
        deal_data: Deal dictionary with title, old_price, new_price, etc.
        
    Returns:
        Formatted message string
    """
    title = deal_data.get('title', 'Sem título')
    old_price = deal_data.get('old_price', 0)
    new_price = deal_data.get('new_price', 0)
    affiliate_url = deal_data.get('affiliate_url', deal_data.get('original_url', ''))
    
    # Calculate discount percentage
    discount = 0
    if old_price and new_price and old_price > new_price:
        discount = int(((old_price - new_price) / old_price) * 100)
    
    # Build message
    message = f"🔥 *OFERTA IMPERDÍVEL* 🔥\n\n"
    message += f"📦 {escape_markdown(title)}\n\n"
    
    if old_price and old_price > new_price:
        message += f"~~R$ {escape_markdown(f'{old_price:.2f}')}~~ ➡️ *R$ {escape_markdown(f'{new_price:.2f}')}*\n"
        message += f"💰 *{discount}% OFF*\n\n"
    else:
        message += f"💵 *R$ {escape_markdown(f'{new_price:.2f}')}*\n\n"
    
    message += f"🔗 [Clique aqui para comprar]({escape_markdown(affiliate_url)})"
    
    return message


def send_deal(deal_data: Dict) -> bool:
    """
    Send deal notification to Telegram.
    
    In DEBUG mode, only logs the deal without sending.
    In production mode, sends photo with caption to Telegram.
    
    Args:
        deal_data: Deal dictionary with title, price, image_url, affiliate_url, etc.
        
    Returns:
        True if successful, False otherwise
    """
    # Check DEBUG mode
    debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    if debug_mode:
        logger.info("=" * 50)
        logger.info("DEBUG MODE: Deal would be sent to Telegram")
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
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id or bot_token == 'seu_token':
            logger.error("Telegram credentials not configured")
            return False
        
        # Format message
        caption = format_deal_message(deal_data)
        image_url = deal_data.get('image_url')
        
        # Telegram API endpoint
        base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Send photo with caption if image available, otherwise send text
        if image_url:
            url = f"{base_url}/sendPhoto"
            payload = {
                'chat_id': chat_id,
                'photo': image_url,
                'caption': caption,
                'parse_mode': 'MarkdownV2'
            }
        else:
            url = f"{base_url}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': caption,
                'parse_mode': 'MarkdownV2',
                'disable_web_page_preview': False
            }
        
        # Send request
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Deal sent to Telegram successfully: {deal_data.get('title')}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send deal to Telegram: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
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
