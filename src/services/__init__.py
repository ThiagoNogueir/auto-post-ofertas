"""Services package initialization."""
from .ai_processor import extract_deals_from_text, validate_deal
from .simple_affiliate import generate_simple_link
from .telegram_bot import send_deal, send_notification
from .evolution_api import send_deal_to_whatsapp

__all__ = [
    'extract_deals_from_text',
    'validate_deal',
    'generate_simple_link',
    'send_deal',
    'send_notification',
    'send_deal_to_whatsapp'
]
