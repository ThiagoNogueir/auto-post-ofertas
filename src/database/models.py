"""
Database models using Peewee ORM with SQLite.
Handles deal storage and deduplication.
"""

from peewee import *
from datetime import datetime
import os

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Database connection
db = SqliteDatabase('data/deals.db')


class BaseModel(Model):
    """Base model class for all database models."""
    class Meta:
        database = db


class Deal(BaseModel):
    """
    Deal model for storing promotional offers.
    
    Fields:
        id: Auto-incrementing primary key
        external_id: Unique identifier from the source platform (Shopee/ML)
        title: Deal title/product name
        price: Current price
        original_url: Original product URL
        affiliate_url: Generated affiliate URL
        sent_at: Timestamp when deal was sent to Telegram
    """
    id = AutoField(primary_key=True)
    external_id = CharField(unique=True, index=True)
    title = CharField()
    price = DecimalField(max_digits=10, decimal_places=2)
    original_url = TextField()
    affiliate_url = TextField(null=True)
    sent_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'deals'
        indexes = (
            (('external_id',), True),  # Unique index for deduplication
        )


def init_database():
    """Initialize database and create tables if they don't exist."""
    db.connect()
    db.create_tables([Deal], safe=True)
    return db


def is_deal_processed(external_id: str) -> bool:
    """
    Check if a deal has already been processed.
    
    Args:
        external_id: Unique identifier from the source platform
        
    Returns:
        True if deal exists in database, False otherwise
    """
    return Deal.select().where(Deal.external_id == external_id).exists()


def save_deal(external_id: str, title: str, price: float, original_url: str, affiliate_url: str = None):
    """
    Save a new deal to the database.
    
    Args:
        external_id: Unique identifier from the source platform
        title: Deal title/product name
        price: Current price
        original_url: Original product URL
        affiliate_url: Generated affiliate URL (optional)
        
    Returns:
        Created Deal instance
    """
    deal = Deal.create(
        external_id=external_id,
        title=title,
        price=price,
        original_url=original_url,
        affiliate_url=affiliate_url
    )
    return deal
