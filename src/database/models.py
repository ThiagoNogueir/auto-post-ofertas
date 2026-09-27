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

# Database connection: PostgreSQL if DATABASE_URL is set, otherwise SQLite fallback
database_url = os.getenv('DATABASE_URL')
if database_url:
    from playhouse.db_url import connect
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    db = connect(database_url)
else:
    db_path = os.path.join(data_dir, 'deals.db')
    db = SqliteDatabase(db_path)

SUBSCRIBERS_BACKUP_FILE = os.path.join(data_dir, 'subscribers_backup.json')

def save_subscribers_backup():
    """Backup active subscribers to JSON for state resilience across container restarts."""
    try:
        import json
        subs = list(Subscriber.select())
        data = [{
            'chat_id': str(s.chat_id),
            'username': s.username,
            'first_name': s.first_name,
            'categories': s.categories,
            'is_active': s.is_active
        } for s in subs]
        with open(SUBSCRIBERS_BACKUP_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def restore_subscribers_backup():
    """Restore subscribers if table is empty after container restart."""
    try:
        import json
        count = Subscriber.select().count()
        if count > 0:
            return
            
        data = []
        # 1. Try environment variable SUBSCRIBERS_BACKUP_JSON first (cloud persistence)
        env_backup = os.getenv('SUBSCRIBERS_BACKUP_JSON')
        if env_backup:
            try:
                data = json.loads(env_backup)
            except Exception:
                pass
                
        # 2. Try file backup
        if not data and os.path.exists(SUBSCRIBERS_BACKUP_FILE):
            try:
                with open(SUBSCRIBERS_BACKUP_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                pass
                
        if data:
            restored = 0
            for item in data:
                Subscriber.get_or_create(
                    chat_id=str(item.get('chat_id')),
                    defaults={
                        'username': item.get('username'),
                        'first_name': item.get('first_name'),
                        'categories': item.get('categories', 'Nenhuma'),
                        'is_active': item.get('is_active', True)
                    }
                )
                restored += 1
    except Exception:
        pass


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


class Subscriber(BaseModel):
    """
    Subscriber model for Telegram users and their category preferences.
    """
    id = AutoField(primary_key=True)
    chat_id = CharField(unique=True, index=True)
    username = CharField(null=True)
    first_name = CharField(null=True)
    categories = TextField(default='Todas')  # Comma-separated: "Celulares,Informática,Games" or "Todas"
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=get_brazil_time)
    updated_at = DateTimeField(default=get_brazil_time)

    class Meta:
        table_name = 'subscribers'
        indexes = (
            (('chat_id',), True),
            (('is_active',), False),
        )


def init_database():
    """Initialize database and create tables if they don't exist."""
    db.connect(reuse_if_open=True)
    db.create_tables([Deal, Coupon, Subscriber], safe=True)
    
    # Restore subscriber preferences if table is empty
    restore_subscribers_backup()
    
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


def is_deal_processed(external_id: str, title: str = None) -> bool:
    """
    Check if a deal has already been processed by external_id OR title.
    Prevents duplicate postings even if URLs or parameters vary slightly.
    
    Args:
        external_id: Unique identifier from the source platform
        title: Deal title (optional, used for secondary deduplication)
        
    Returns:
        True if deal exists in database, False otherwise
    """
    try:
        if external_id and Deal.select().where(Deal.external_id == external_id).exists():
            return True
            
        if title and title.strip():
            clean_title = title.strip()
            if Deal.select().where(Deal.title == clean_title).exists():
                return True
                
        return False
    except Exception:
        return False


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


def get_or_create_subscriber(chat_id: str, username: str = None, first_name: str = None) -> Subscriber:
    """Get existing subscriber or create a new one."""
    chat_id = str(chat_id)
    sub, created = Subscriber.get_or_create(
        chat_id=chat_id,
        defaults={
            'username': username,
            'first_name': first_name,
            'categories': 'Nenhuma',
            'is_active': True
        }
    )
    if not created:
        updated = False
        if username and sub.username != username:
            sub.username = username
            updated = True
        if first_name and sub.first_name != first_name:
            sub.first_name = first_name
            updated = True
        if updated:
            sub.updated_at = get_brazil_time()
            sub.save()
            save_subscribers_backup()
    else:
        save_subscribers_backup()
    return sub


def toggle_subscriber_category(chat_id: str, category: str) -> Subscriber:
    """Toggle a category subscription for a user."""
    sub = get_or_create_subscriber(chat_id)
    all_categories = [
        'Celulares', 'Informática', 'Eletrônicos', 'Games', 'Casa',
        'Bebidas', 'Beleza', 'Moda', 'Ferramentas', 'Automotivo', 'Pets', 'Outros'
    ]
    
    current_raw = (sub.categories or 'Nenhuma').strip()
    is_all = current_raw == 'Todas'
    
    if category == 'Todas':
        sub.categories = 'Nenhuma' if is_all else 'Todas'
    elif category in ('Limpar', 'Nenhuma'):
        sub.categories = 'Nenhuma'
    else:
        # Category is one of individual categories
        if is_all:
            # If user had 'Todas' and clicked one category, deselect that one
            current = [c for c in all_categories if c != category]
        elif current_raw in ('Nenhuma', ''):
            current = [category]
        else:
            current = [c.strip() for c in current_raw.split(',') if c.strip() and c.strip() != 'Nenhuma']
            if category in current:
                current.remove(category)
            else:
                current.append(category)

        if set(current) >= set(all_categories):
            sub.categories = 'Todas'
        elif not current:
            sub.categories = 'Nenhuma'
        else:
            sub.categories = ','.join(current)
            
    sub.updated_at = get_brazil_time()
    sub.save()
    save_subscribers_backup()
    return sub


def toggle_subscriber_active(chat_id: str) -> Subscriber:
    """Pause or resume alerts for a user."""
    sub = get_or_create_subscriber(chat_id)
    sub.is_active = not sub.is_active
    sub.updated_at = get_brazil_time()
    sub.save()
    save_subscribers_backup()
    return sub


def get_subscribers_for_category(category: str) -> list:
    """Get all active subscriber chat_ids interested in this category."""
    try:
        active_subs = Subscriber.select().where(Subscriber.is_active == True)
        matched_chat_ids = []
        
        for sub in active_subs:
            cats = [c.strip() for c in sub.categories.split(',') if c.strip()]
            if 'Todas' in cats or category in cats:
                matched_chat_ids.append(sub.chat_id)
                
        return matched_chat_ids
    except Exception:
        return []

