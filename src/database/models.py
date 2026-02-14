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


class Coupon(BaseModel):
    """
    Coupon model for tracking generated ML affiliate coupons.
    
    Fields:
        id: Auto-incrementing primary key
        coupon_code: Unique coupon code (e.g., PROMO_20260214_A3F2)
        product_id: ML product ID this coupon applies to
        discount_percentage: Discount percentage (e.g., 5.0 for 5%)
        discount_amount: Fixed discount amount (if applicable)
        created_at: When the coupon was created
        expires_at: When the coupon expires
        is_active: Whether the coupon is currently active
        usage_count: How many times the coupon has been used
        max_usage: Maximum number of uses allowed
        category: Product category
    """
    id = AutoField(primary_key=True)
    coupon_code = CharField(unique=True, index=True)
    product_id = CharField(index=True)
    discount_percentage = DecimalField(max_digits=5, decimal_places=2, null=True)
    discount_amount = DecimalField(max_digits=10, decimal_places=2, null=True)
    created_at = DateTimeField(default=get_brazil_time)
    expires_at = DateTimeField(null=True)
    is_active = BooleanField(default=True)
    usage_count = IntegerField(default=0)
    max_usage = IntegerField(null=True)
    category = CharField(default='Outros')
    
    class Meta:
        table_name = 'coupons'
        indexes = (
            (('coupon_code',), True),   # Unique index for coupon codes
            (('product_id',), False),   # Index for product lookup
            (('is_active',), False),    # Index for active coupons
        )


def init_database():
    """Initialize database and create tables if they don't exist."""
    db.connect()
    db.create_tables([Deal, Coupon], safe=True)
    
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


def save_coupon(coupon_code: str, product_id: str, discount_percentage: float = None, 
                discount_amount: float = None, expires_at = None, max_usage: int = None,
                category: str = 'Outros'):
    """
    Save a new coupon to the database.
    
    Args:
        coupon_code: Unique coupon code
        product_id: ML product ID
        discount_percentage: Discount percentage (optional)
        discount_amount: Fixed discount amount (optional)
        expires_at: Expiration datetime (optional)
        max_usage: Maximum number of uses (optional)
        category: Product category (optional)
        
    Returns:
        Created Coupon instance
    """
    coupon = Coupon.create(
        coupon_code=coupon_code,
        product_id=product_id,
        discount_percentage=discount_percentage,
        discount_amount=discount_amount,
        expires_at=expires_at,
        max_usage=max_usage,
        category=category
    )
    return coupon


def get_coupon_by_product(product_id: str):
    """
    Get an active coupon for a specific product.
    
    Args:
        product_id: ML product ID
        
    Returns:
        Coupon instance or None
    """
    try:
        return Coupon.select().where(
            (Coupon.product_id == product_id) & 
            (Coupon.is_active == True)
        ).order_by(Coupon.created_at.desc()).first()
    except:
        return None


def get_coupon_by_code(coupon_code: str):
    """
    Get a coupon by its code.
    
    Args:
        coupon_code: Coupon code
        
    Returns:
        Coupon instance or None
    """
    try:
        return Coupon.get(Coupon.coupon_code == coupon_code)
    except:
        return None


def is_coupon_active(coupon_code: str) -> bool:
    """
    Check if a coupon is active.
    
    Args:
        coupon_code: Coupon code
        
    Returns:
        True if active, False otherwise
    """
    try:
        coupon = Coupon.get(Coupon.coupon_code == coupon_code)
        
        # Check if active flag is set
        if not coupon.is_active:
            return False
        
        # Check if expired
        if coupon.expires_at and coupon.expires_at < get_brazil_time():
            return False
        
        # Check if max usage reached
        if coupon.max_usage and coupon.usage_count >= coupon.max_usage:
            return False
        
        return True
    except:
        return False


def update_coupon_usage(coupon_code: str):
    """
    Increment the usage count for a coupon.
    
    Args:
        coupon_code: Coupon code
    """
    try:
        coupon = Coupon.get(Coupon.coupon_code == coupon_code)
        coupon.usage_count += 1
        coupon.save()
    except:
        pass
