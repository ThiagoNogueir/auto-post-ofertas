"""
Example usage of PromoBot components.
This file demonstrates how to use each module independently.
"""

from dotenv import load_dotenv
load_dotenv()


def example_database():
    """Example: Using the database."""
    print("\n" + "=" * 60)
    print("Example 1: Database Operations")
    print("=" * 60)
    
    from src.database import init_database, save_deal, is_deal_processed, Deal
    
    # Initialize
    db = init_database()
    
    # Save a deal
    deal = save_deal(
        external_id="test-123",
        title="Produto Teste",
        price=99.90,
        original_url="https://example.com/product",
        affiliate_url="https://example.com/product?aff=123"
    )
    print(f"✓ Saved deal: {deal.title}")
    
    # Check if processed
    if is_deal_processed("test-123"):
        print("✓ Deal already in database")
    
    # Query all deals
    all_deals = Deal.select()
    print(f"✓ Total deals in database: {all_deals.count()}")
    
    db.close()


def example_logger():
    """Example: Using the logger."""
    print("\n" + "=" * 60)
    print("Example 2: Logger")
    print("=" * 60)
    
    from src.utils.logger import logger
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("✓ Check logs/bot.log for output")


def example_ai_processor():
    """Example: Using the AI processor."""
    print("\n" + "=" * 60)
    print("Example 3: AI Processor")
    print("=" * 60)
    
    from src.services import extract_deals_from_text, validate_deal
    
    sample_text = """
    Oferta Relâmpago!
    
    Smartphone XYZ Pro
    De R$ 1.999,00 por apenas R$ 1.299,00
    Link: https://shopee.com.br/product/123
    
    Notebook ABC Ultra
    De R$ 3.500,00 por R$ 2.800,00
    Link: https://shopee.com.br/product/456
    """
    
    print("Extracting deals from text...")
    deals = extract_deals_from_text(sample_text)
    
    print(f"✓ Found {len(deals)} deals")
    for i, deal in enumerate(deals, 1):
        print(f"\nDeal {i}:")
        print(f"  Title: {deal.get('title')}")
        print(f"  Price: R$ {deal.get('new_price')}")
        print(f"  Valid: {validate_deal(deal)}")


def example_telegram():
    """Example: Sending to Telegram."""
    print("\n" + "=" * 60)
    print("Example 4: Telegram Notification")
    print("=" * 60)
    
    from src.services import send_deal, send_notification
    
    # Send a simple notification
    send_notification("🤖 Test notification from PromoBot!")
    
    # Send a deal
    test_deal = {
        'title': 'Produto Teste',
        'old_price': 199.90,
        'new_price': 99.90,
        'original_url': 'https://example.com/product',
        'affiliate_url': 'https://example.com/product?aff=123',
        'image_url': None
    }
    
    send_deal(test_deal)
    print("✓ Check Telegram for messages (if not in DEBUG mode)")


def example_link_generator():
    """Example: Generating affiliate links."""
    print("\n" + "=" * 60)
    print("Example 5: Link Generator")
    print("=" * 60)
    
    from src.services import generate_link
    
    product_url = "https://shopee.com.br/product/123456"
    
    print(f"Generating affiliate link for: {product_url}")
    affiliate_url = generate_link(product_url)
    
    if affiliate_url:
        print(f"✓ Generated: {affiliate_url}")
    else:
        print("✗ Failed to generate link")


def example_session_manager():
    """Example: Session management."""
    print("\n" + "=" * 60)
    print("Example 6: Session Manager")
    print("=" * 60)
    
    from src.utils import SessionManager
    from src.browser import setup_driver, quit_driver
    
    # Create session manager
    session = SessionManager()
    
    # Setup driver
    driver = setup_driver(headless=True)
    
    # Navigate to a page
    driver.get("https://www.google.com")
    
    # Save cookies
    session.save_cookies(driver)
    print("✓ Cookies saved")
    
    # Load cookies (on next run)
    driver.get("https://www.google.com")
    session.load_cookies(driver)
    print("✓ Cookies loaded")
    
    # Cleanup
    quit_driver(driver)


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PromoBot - Component Examples")
    print("=" * 60)
    
    examples = [
        ("Database", example_database),
        ("Logger", example_logger),
        ("AI Processor", example_ai_processor),
        ("Telegram", example_telegram),
        # ("Link Generator", example_link_generator),  # Commented - requires browser
        # ("Session Manager", example_session_manager),  # Commented - requires browser
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
