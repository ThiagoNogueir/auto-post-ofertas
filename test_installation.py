"""
Quick test script to validate the installation.
Run this before starting the main bot.
"""

import sys
import os

print("=" * 60)
print("PromoBot - Installation Test")
print("=" * 60)

# Test 1: Python version
print("\n1. Checking Python version...")
if sys.version_info >= (3, 11):
    print(f"   ✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
else:
    print(f"   ✗ Python 3.11+ required, found {sys.version_info.major}.{sys.version_info.minor}")
    sys.exit(1)

# Test 2: Required packages
print("\n2. Checking required packages...")
required_packages = [
    'requests',
    'google.generativeai',
    'selenium',
    'dotenv',
    'schedule',
    'peewee',
    'fake_useragent',
    'loguru'
]

missing_packages = []
for package in required_packages:
    package_name = package.replace('.', '_')
    try:
        __import__(package)
        print(f"   ✓ {package}")
    except ImportError:
        print(f"   ✗ {package} - NOT FOUND")
        missing_packages.append(package)

if missing_packages:
    print(f"\n   Missing packages: {', '.join(missing_packages)}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Test 3: Environment variables
print("\n3. Checking environment variables...")
from dotenv import load_dotenv
load_dotenv()

env_vars = {
    'DEBUG_MODE': os.getenv('DEBUG_MODE'),
    'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
    'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
    'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID'),
}

for var, value in env_vars.items():
    if value and value not in ['sua_chave', 'seu_token', 'seu_chat_id', 'email', 'senha']:
        print(f"   ✓ {var} configured")
    else:
        if var == 'DEBUG_MODE':
            print(f"   ⚠ {var} using default (True)")
        elif var in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']:
            print(f"   ⚠ {var} not configured (OK in DEBUG mode)")
        else:
            print(f"   ✗ {var} not configured")

# Test 4: Database initialization
print("\n4. Testing database...")
try:
    from src.database import init_database
    db = init_database()
    print("   ✓ Database initialized successfully")
    db.close()
except Exception as e:
    print(f"   ✗ Database error: {e}")
    sys.exit(1)

# Test 5: Logger
print("\n5. Testing logger...")
try:
    from src.utils.logger import logger
    logger.info("Test log message")
    print("   ✓ Logger working")
except Exception as e:
    print(f"   ✗ Logger error: {e}")
    sys.exit(1)

# Test 6: Chrome/Chromium (optional)
print("\n6. Checking Chrome/Chromium...")
chrome_bin = os.getenv('CHROME_BIN')
if chrome_bin and os.path.exists(chrome_bin):
    print(f"   ✓ Chrome found at {chrome_bin}")
else:
    print("   ⚠ CHROME_BIN not set (will use system Chrome)")

print("\n" + "=" * 60)
print("✓ All tests passed! Ready to run PromoBot.")
print("=" * 60)
print("\nTo start the bot:")
print("  - Docker: docker-compose up")
print("  - Local:  python src/main.py")
print()
