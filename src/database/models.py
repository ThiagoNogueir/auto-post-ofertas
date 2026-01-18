"""
Database models using Peewee ORM with SQLite.
Handles deal storage and deduplication.
"""

from peewee import *
from datetime import datetime, timezone, timedelta
import os

# Brazilian timezone (UTC-3)
BRAZIL_TZ = timezone(timedelta(hours=-3))

def get_brazil_time():
    """Get current time in Brazilian timezone"""
    return datetime.now(BRAZIL_TZ)

# Ensure data directory exists
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
data_dir = os.path.join(base_dir, 'data')
os.makedirs(data_dir, exist_ok=True)

# Database connection
db_path = os.path.join(data_dir, 'deals.db')
db = SqliteDatabase(db_path)


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
    image_url = TextField(null=True)
    category = CharField(default='Outros')
    store = CharField(default='Outros')
    sent_at = DateTimeField(default=get_brazil_time)
    
    class Meta:
        table_name = 'deals'
        indexes = (
            (('external_id',), True),  # Unique index for deduplication
            (('category',), False),    # Index for filtering
            (('store',), False),       # Index for filtering by store
        )


def init_database():
    """Initialize database and create tables if they don't exist."""
    db.connect()
    db.create_tables([Deal], safe=True)
    
    # Simple migrations
    try:
        db.execute_sql('ALTER TABLE deals ADD COLUMN image_url TEXT')
    except Exception:
        pass
        
    try:
        db.execute_sql('ALTER TABLE deals ADD COLUMN category TEXT DEFAULT "Outros"')
    except Exception:
        pass

    try:
        db.execute_sql('ALTER TABLE deals ADD COLUMN store TEXT DEFAULT "Outros"')
    except Exception:
        pass
        
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


def save_deal(external_id: str, title: str, price: float, original_url: str, affiliate_url: str = None, image_url: str = None, category: str = 'Outros', store: str = 'Outros'):
    """
    Save a new deal to the database.
    
    Args:
        external_id: Unique identifier from the source platform
        title: Deal title/product name
        price: Current price
        original_url: Original product URL
        affiliate_url: Generated affiliate URL (optional)
        image_url: Product image URL (optional)
        category: Product category (optional)
        store: Store name (optional)
        
    Returns:
        Created Deal instance
    """
    deal = Deal.create(
        external_id=external_id,
        title=title,
        price=price,
        original_url=original_url,
        affiliate_url=affiliate_url,
        image_url=image_url,
        category=category,
        store=store
    )
    return deal
