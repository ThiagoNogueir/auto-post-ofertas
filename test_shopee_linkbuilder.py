"""
Test script for Shopee Link Builder
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.shopee_linkbuilder import generate_shopee_affiliate_link
from src.utils.logger import logger

def test_shopee_linkbuilder():
    """Test Shopee Link Builder with a sample product"""
    
    # URL de teste - substitua por uma URL real de produto da Shopee
    test_url = "https://shopee.com.br/product/123456789/987654321"
    
    logger.info("=" * 60)
    logger.info("Testing Shopee Link Builder")
    logger.info("=" * 60)
    logger.info(f"Input URL: {test_url}")
    logger.info("")
    
    # Generate affiliate link
    affiliate_link = generate_shopee_affiliate_link(test_url)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Result:")
    logger.info("=" * 60)
    logger.info(f"Affiliate Link: {affiliate_link}")
    logger.info("")
    
    # Verify result
    if affiliate_link != test_url:
        logger.info("✅ SUCCESS - Affiliate link generated!")
        logger.info("")
        logger.info("IMPORTANTE:")
        logger.info("1. Verifique se o link contém parâmetros de afiliado")
        logger.info("2. Teste o link no navegador para confirmar que rastreia corretamente")
        logger.info("3. Os cookies foram salvos em 'shopee_linkbuilder_cookies.pkl'")
    else:
        logger.warning("⚠️ WARNING - Link unchanged (may have failed)")
        logger.info("")
        logger.info("Possíveis causas:")
        logger.info("1. Não fez login quando solicitado")
        logger.info("2. A página da Shopee mudou de estrutura")
        logger.info("3. Erro de conexão")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    test_shopee_linkbuilder()
