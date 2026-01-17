"""
AI Processor using Google Gemini API.
Analyzes raw text to extract deal information.
"""

import os
import json
from typing import List, Dict, Optional
import google.generativeai as genai
from ..utils.logger import logger


def configure_gemini():
    """Configure Gemini API with the API key from environment."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key or api_key == 'sua_chave':
        logger.warning("GOOGLE_API_KEY not configured properly")
        return False
    
    genai.configure(api_key=api_key)
    logger.info("Gemini API configured successfully")
    return True


def extract_deals_from_text(raw_text: str) -> List[Dict]:
    """
    Analyze text using Google Gemini to extract deal information.
    
    Args:
        raw_text: Raw markdown or text content from the source
        
    Returns:
        List of deal dictionaries with keys: title, old_price, new_price, image_url, original_url
    """
    if not configure_gemini():
        logger.error("Cannot process deals: Gemini API not configured")
        return []
    
    try:
        # Create the model
        model = genai.GenerativeModel('gemini-pro')
        
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

Return ONLY a valid JSON array containing the deals. Do not include any explanation or markdown formatting.
If no deals are found, return an empty array [].

Text to analyze:
{raw_text}
"""
        
        logger.info("Sending request to Gemini API...")
        response = model.generate_content(prompt)
        
        # Parse the response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        # Parse JSON
        deals = json.loads(response_text)
        
        if not isinstance(deals, list):
            logger.warning("Gemini response is not a list, wrapping it")
            deals = [deals] if deals else []
        
        logger.info(f"Extracted {len(deals)} deals from text")
        return deals
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.debug(f"Response text: {response_text}")
        return []
    except Exception as e:
        logger.error(f"Error processing text with Gemini: {e}")
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
