"""Database package initialization."""
from .models import init_database, Deal, is_deal_processed, save_deal

__all__ = ['init_database', 'Deal', 'is_deal_processed', 'save_deal']
