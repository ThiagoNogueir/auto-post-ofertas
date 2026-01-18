"""
Evolution API integration for WhatsApp messaging.
Sends deals to WhatsApp groups based on category mapping.
"""

import requests
import os
from ..utils.logger import logger
from dotenv import load_dotenv

# Force load .env
load_dotenv()


class EvolutionAPI:
    def __init__(self):
        self.base_url = os.getenv('EVOLUTION_API_URL', '')
        self.api_key = os.getenv('EVOLUTION_API_KEY', '')
        self.instance_name = os.getenv('EVOLUTION_INSTANCE_NAME', '')
        logger.info(f"Evolution API Init: URL={self.base_url}, Instance={self.instance_name}, KeyLen={len(self.api_key)}")
        
    def is_configured(self):
        """Check if Evolution API is properly configured"""
        configured = bool(self.base_url and self.api_key and self.instance_name)
        logger.info(f"Evolution API configured: {configured}")
        return configured
    
    def send_text_message(self, group_id: str, text: str) -> bool:
        """
        Send a text message to a WhatsApp group
        
        Args:
            group_id: WhatsApp group ID (format: 5511999999999-1234567890@g.us)
            text: Text message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        # if not self.is_configured():
        #     logger.warning("Evolution API not configured")
        #     return False
            
        try:
            url = f"{self.base_url}/message/sendText/{self.instance_name}"
            
            headers = {
                'Content-Type': 'application/json',
                'apikey': self.api_key
            }
            
            payload = {
                'number': group_id,
                'text': text
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 201 or response.status_code == 200:
                logger.info(f"Message sent to WhatsApp group {group_id}")
                return True
            else:
                logger.error(f"Failed to send WhatsApp message: {response.status_code} - Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def send_image_message(self, group_id: str, image_url: str, caption: str = ""):
        # if not self.is_configured():
        #     logger.warning("Evolution API not configured")
        #     return False
            
        try:
            url = f"{self.base_url}/message/sendMedia/{self.instance_name}"
            
            headers = {
                'Content-Type': 'application/json',
                'apikey': self.api_key
            }
            
            payload = {
                'number': group_id,
                'mediatype': 'image',
                'media': image_url,
                'caption': caption
            }
            logger.info(f"Sending WhatsApp Image to {url} | Group: {group_id} | Media: {image_url}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 201 or response.status_code == 200:
                logger.info(f"Image sent to WhatsApp group {group_id}")
                return True
            else:
                logger.error(f"Failed to send WhatsApp image: {response.status_code} -Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp image: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


def send_deal_to_whatsapp(group_id: str, title: str, price: float, old_price: float, url: str, image_url: str = None):
    """
    Send a deal notification to WhatsApp group
    
    Args:
        group_id: WhatsApp group ID
        title: Product title
        price: Current price
        old_price: Original price
        url: Product URL
        image_url: Optional product image URL
    """
    evolution = EvolutionAPI()
    
    # if not evolution.is_configured():
    #     return False
    
    # Calculate discount
    discount = 0
    if old_price and old_price > price:
        discount = int(((old_price - price) / old_price) * 100)
    
    # Format message
    message = f"""🔥 *OFERTA IMPERDÍVEL!* 🔥

📦 {title}

💰 *De:* ~R$ {old_price:.2f}~
💵 *Por:* R$ {price:.2f}
🏷️ *Desconto:* {discount}% OFF

🛒 Link: {url}

⚡ Corre que é por tempo limitado!"""
    
    # Send image with caption if available, otherwise just text
    if image_url:
        return evolution.send_image_message(group_id, image_url, message)
    else:
        return evolution.send_text_message(group_id, message)
