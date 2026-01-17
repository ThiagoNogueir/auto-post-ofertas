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


def validate_deal(deal: Dict) -> bool:
    """
    Validate that a deal has all required fields.
    
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
    
    return True
