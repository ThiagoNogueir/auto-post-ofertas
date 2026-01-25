"""
Test HTTPS validation for affiliate links
"""

from src.services.simple_affiliate import generate_simple_link

# Test cases
test_urls = [
    "http://mercadolivre.com.br/produto-teste",
    "https://mercadolivre.com.br/produto-teste",
    "http://shopee.com.br/produto-teste",
    "https://shopee.com.br/produto-teste",
    "http://example.com/produto",
    "https://example.com/produto",
]

print("=" * 60)
print("Testing HTTPS Validation")
print("=" * 60)

for url in test_urls:
    result = generate_simple_link(url)
    is_https = result.startswith('https://')
    status = "[OK] HTTPS" if is_https else "[FAIL] HTTP"
    
    print(f"\n{status}")
    print(f"Input:  {url}")
    print(f"Output: {result}")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)

