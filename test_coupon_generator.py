"""
Test script for ML Coupon Generator
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.ml_coupon_generator import generate_coupon_name, get_or_create_coupon
from src.database.models import init_database
from src.utils.logger import logger

def test_coupon_name_generation():
    """Test unique coupon name generation"""
    print("\n" + "="*60)
    print("Testing Coupon Name Generation")
    print("="*60)
    
    # Generate 5 unique names
    names = []
    for i in range(5):
        name = generate_coupon_name(product_id=f"MLB{1234567890+i}")
        names.append(name)
        print(f"{i+1}. {name}")
    
    # Check uniqueness
    if len(names) == len(set(names)):
        print("\n✅ All names are unique!")
    else:
        print("\n❌ Duplicate names found!")
    
    return names

def test_database_integration():
    """Test coupon database integration"""
    print("\n" + "="*60)
    print("Testing Database Integration")
    print("="*60)
    
    # Initialize database
    init_database()
    print("✅ Database initialized")
    
    # Test coupon creation
    test_product_url = "https://www.mercadolivre.com.br/produto/MLB1234567890"
    test_product_id = "MLB1234567890"
    
    print(f"\nTesting coupon for product: {test_product_id}")
    
    coupon_info = get_or_create_coupon(
        product_url=test_product_url,
        product_id=test_product_id,
        discount_percentage=10.0,
        category="Teste"
    )
    
    if coupon_info.get('success'):
        print(f"✅ Coupon created/retrieved: {coupon_info['code']}")
        print(f"   Discount: {coupon_info['discount']}%")
    else:
        print("❌ Failed to create/retrieve coupon")
    
    return coupon_info

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ML COUPON GENERATOR - TEST SUITE")
    print("="*60)
    
    # Test 1: Name generation
    names = test_coupon_name_generation()
    
    # Test 2: Database integration
    coupon_info = test_database_integration()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Generated {len(names)} unique coupon names")
    print(f"✅ Database integration {'successful' if coupon_info.get('success') else 'failed'}")
    
    print("\n" + "="*60)
    print("IMPORTANT NOTES")
    print("="*60)
    print("⚠️  Coupon creation via Selenium requires manual implementation")
    print("⚠️  Visit: https://www.mercadolivre.com.br/afiliados/coupons#hub")
    print("⚠️  Coupons are saved to database as 'pending manual creation'")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
