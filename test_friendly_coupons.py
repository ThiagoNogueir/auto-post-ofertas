"""
Test script for ML Coupon Generator - Testing Friendly Names
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.ml_coupon_generator import generate_coupon_name
from src.database.models import init_database
from src.utils.logger import logger

def test_friendly_names():
    """Test friendly coupon name generation"""
    print("\n" + "="*60)
    print("Testing Friendly Coupon Names")
    print("="*60)
    
    # Initialize database
    init_database()
    
    # Test different categories
    categories = [
        ('Celulares', 'MLB123'),
        ('Celulares', 'MLB456'),
        ('Eletrônicos', 'MLB789'),
        ('Computadores', 'MLB101'),
        ('Outros', 'MLB202')
    ]
    
    print("\nGerando cupons com nomes amigáveis:\n")
    
    for category, product_id in categories:
        name = generate_coupon_name(product_id=product_id, category=category)
        print(f"  {category:15} → {name}")
    
    print("\n" + "="*60)
    print("✅ Nomes amigáveis gerados com sucesso!")
    print("="*60)
    
    print("\n📝 IMPORTANTE:")
    print("   Estes códigos devem ser criados MANUALMENTE em:")
    print("   https://www.mercadolivre.com.br/afiliados/coupons#hub")
    print("\n   Veja o arquivo CUPONS_GUIA.md para instruções completas.")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_friendly_names()
