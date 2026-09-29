"""
AI Processor using Groq API (FREE & FAST!).
Analyzes raw text to extract deal information.
"""

import os
import json
from typing import List, Dict
from groq import Groq
from ..utils.logger import logger


def get_groq_client():
    """Get Groq client with API key from environment."""
    api_key = os.getenv('GROQ_API_KEY') or os.getenv('GOOGLE_API_KEY')  # Fallback to GOOGLE_API_KEY for compatibility
    if not api_key or api_key == 'sua_chave':
        logger.warning("GROQ_API_KEY not configured properly")
        return None
    
    try:
        client = Groq(api_key=api_key)
        logger.info("Groq API configured successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to configure Groq: {e}")
        return None


def extract_deals_from_text(raw_text: str) -> List[Dict]:
    """
    Analyze text using Groq AI to extract deal information.
    
    Args:
        raw_text: Raw markdown or text content from the source
        
    Returns:
        List of deal dictionaries with keys: title, old_price, new_price, image_url, original_url
    """
    client = get_groq_client()
    if not client:
        logger.error("Cannot process deals: Groq API not configured")
        return []
    
    # Truncate text if too large (Groq has token limits)
    MAX_CHARS = 30000  # Adjusted limit
    if len(raw_text) > MAX_CHARS:
        logger.warning(f"Text too large ({len(raw_text)} chars), truncating to {MAX_CHARS}")
        raw_text = raw_text[:MAX_CHARS]
    
    try:
        # Craft the prompt
        prompt = f"""
Analyze the following text and find the best promotional deals.
Extract information about products with significant discounts.

For each deal found, return a JSON object with these fields:
- title: Product name/title
- old_price: Original price (number only, without currency symbol)
- new_price: Promotional price (number only, without currency symbol)
- image_url: Product image URL (if available, otherwise null)
- original_url: Product page URL
- category: Classify into one of: [Eletrônicos, Casa, Moda, Games, Beleza, Outros]

Return ONLY a valid JSON array containing the deals. Do not include any explanation or markdown formatting.
If no deals are found, return an empty array [].

Text to analyze:
{raw_text}
"""
        
        logger.info("Sending request to Groq API...")
        
        # Use Groq's mixtral model (good balance of rate limits and performance)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.3,  # Lower temperature for more consistent JSON output
        )
        
        # Parse the response
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        # Parse JSON
        deals = json.loads(response_text)
        
        if not isinstance(deals, list):
            logger.warning("Groq response is not a list, wrapping it")
            deals = [deals] if deals else []
        
        logger.info(f"Extracted {len(deals)} deals from text")
        return deals
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Groq response as JSON: {e}")
        try:
            logger.debug(f"Response text: {response_text}")
        except:
            pass
        return []
    except Exception as e:
        logger.error(f"Error processing text with Groq: {e}")
        return []


TECH_CATEGORIES = {'Celulares', 'Informática', 'Eletrônicos', 'Games'}
CASA_CATEGORIES = {'Casa', 'Bebidas', 'Beleza'}
TARGET_CATEGORIES = TECH_CATEGORIES | CASA_CATEGORIES


def validate_deal(deal: Dict) -> bool:
    """
    Validate that a deal has all required fields, belongs to a target niche,
    meets minimum discount, and fits the ideal price ticket.
    
    Args:
        deal: Deal dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['title', 'new_price', 'original_url']
    
    for field in required_fields:
        if field not in deal or not deal[field]:
            logger.warning(f"Deal missing required field: {field}")
            return False

    category = deal.get('category', 'Outros')
    
    # 1. Niche Filter: Reject products from non-target categories (Pets, Moda, Ferramentas, etc.)
    if category not in TARGET_CATEGORIES and category != 'Outros':
        logger.info(f"Skipping out-of-niche deal: '{deal.get('title')[:35]}...' [{category}]")
        return False
            
    # Check minimum discount and ticket filters
    try:
        config_path = os.path.join(os.getcwd(), 'urls_config.json')
        min_discount = 25
        tech_min_price = 25.0
        tech_max_price = 450.0
        casa_min_price = 15.0
        casa_max_price = 300.0
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                min_discount = cfg.get('min_discount_percentage', 25)
                tech_min_price = float(cfg.get('tech_min_price', 25.0))
                tech_max_price = float(cfg.get('tech_max_price', 450.0))
                casa_min_price = float(cfg.get('casa_min_price', 15.0))
                casa_max_price = float(cfg.get('casa_max_price', 300.0))
                
        discount_pct = deal.get('discount_pct', 0)
        old_price = float(deal.get('old_price', 0) or 0)
        new_price = float(deal.get('new_price', 0) or 0)
        
        if discount_pct == 0 and old_price > new_price:
            discount_pct = round(((old_price - new_price) / old_price) * 100)
            deal['discount_pct'] = discount_pct
            
        # 2. Minimum Discount Filter
        if min_discount > 0 and discount_pct < min_discount:
            logger.info(f"Skipping '{deal.get('title')[:35]}...': discount {discount_pct}% is below minimum {min_discount}%")
            return False

        # 3. Ticket / Price Range Filter
        # Bypass max price if discount >= 50% (potential bug / super deal)
        is_super_deal = discount_pct >= 50
        
        if category in TECH_CATEGORIES:
            if new_price < tech_min_price:
                logger.info(f"Skipping Tech deal below min ticket (R$ {new_price} < R$ {tech_min_price}): '{deal.get('title')[:35]}...'")
                return False
            if new_price > tech_max_price and not is_super_deal:
                logger.info(f"Skipping Tech deal above max ticket (R$ {new_price} > R$ {tech_max_price}): '{deal.get('title')[:35]}...'")
                return False
        elif category in CASA_CATEGORIES:
            if new_price < casa_min_price:
                logger.info(f"Skipping Casa deal below min ticket (R$ {new_price} < R$ {casa_min_price}): '{deal.get('title')[:35]}...'")
                return False
            if new_price > casa_max_price and not is_super_deal:
                logger.info(f"Skipping Casa deal above max ticket (R$ {new_price} > R$ {casa_max_price}): '{deal.get('title')[:35]}...'")
                return False
                
    except Exception as e:
        logger.debug(f"Could not apply discount/ticket filter: {e}")
    
    return True
