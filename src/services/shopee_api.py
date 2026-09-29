"""
Shopee Affiliate API Service
Supports Shopee Affiliate Open API (GraphQL) for link generation and deal fetching.
Documentation: https://affiliate.shopee.com.br/open_api
"""

import os
import time
import json
import hashlib
import requests
from typing import Optional, List, Dict
from dotenv import load_dotenv
from ..utils.logger import logger

load_dotenv()


class ShopeeAffiliateAPI:
    """
    Client for Shopee Affiliate Open API (GraphQL).
    Requires SHOPEE_APP_ID and SHOPEE_SECRET from affiliate.shopee.com.br/open_api.
    """
    
    BASE_URL = "https://open-api.affiliate.shopee.com.br/graphql"
    
    def __init__(self):
        self.app_id = os.getenv("SHOPEE_APP_ID", "").strip()
        self.secret = os.getenv("SHOPEE_SECRET", "").strip()
        self.affiliate_id = os.getenv("SHOPEE_AFFILIATE_ID", "").strip()
        
    def is_configured(self) -> bool:
        """Check if Open API credentials are set"""
        return bool(self.app_id and self.secret)
        
    def _generate_signature(self, timestamp: str, payload_str: str) -> str:
        """
        Shopee Signature: SHA256(AppId + Timestamp + Payload + Secret)
        """
        raw = f"{self.app_id}{timestamp}{payload_str}{self.secret}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
        
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """
        Executes a GraphQL query/mutation against Shopee Affiliate Open API.
        """
        if not self.is_configured():
            logger.warning("Shopee Open API credentials not configured (SHOPEE_APP_ID, SHOPEE_SECRET)")
            return None
            
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables
                
            payload_json = json.dumps(payload, separators=(',', ':'))
            timestamp = str(int(time.time()))
            signature = self._generate_signature(timestamp, payload_json)
            
            headers = {
                "Authorization": f"SHA256 Credential={self.app_id}, Timestamp={timestamp}, Signature={signature}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.BASE_URL, data=payload_json, headers=headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    logger.error(f"Shopee API GraphQL error: {data['errors']}")
                    return None
                return data.get("data")
            else:
                logger.error(f"Shopee API HTTP error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Shopee API request failed: {e}")
            return None

    def generate_affiliate_link(self, origin_url: str, sub_ids: Optional[List[str]] = None) -> Optional[str]:
        """
        Converts a Shopee product URL into an official affiliate short link (s.shopee.com.br).
        """
        if not self.is_configured():
            return None
            
        sub_ids = sub_ids or ["promobot"]
        
        mutation = """
        mutation ($originUrl: String!, $subIds: [String]) {
          generateShortLink(input: { originUrl: $originUrl, subIds: $subIds }) {
            shortLink
          }
        }
        """
        variables = {
            "originUrl": origin_url,
            "subIds": sub_ids
        }
        
        result = self._execute_query(mutation, variables)
        if result and "generateShortLink" in result:
            short_link = result["generateShortLink"].get("shortLink")
            if short_link:
                logger.info(f"Shopee API generated short link: {short_link}")
                return short_link
                
        return None

    def fetch_offers(self, keyword: str, limit: int = 20, page: int = 0) -> List[Dict]:
        """
        Fetches deals directly from Shopee Affiliate productOfferV2 query.
        Returns a normalized list of deals ready for PromoBot pipeline.
        """
        if not self.is_configured():
            return []
            
        query = """
        query ($keyword: String, $page: Int, $limit: Int) {
          productOfferV2(keyword: $keyword, page: $page, limit: $limit, sortType: 2) {
            nodes {
              itemId
              shopId
              productName
              price
              priceMin
              priceMax
              priceDiscountRate
              imageUrl
              productLink
              offerLink
            }
          }
        }
        """
        variables = {
            "keyword": keyword,
            "page": page,
            "limit": limit
        }
        
        result = self._execute_query(query, variables)
        deals = []
        
        if result and "productOfferV2" in result:
            nodes = result["productOfferV2"].get("nodes", [])
            for node in nodes:
                try:
                    price = float(node.get("price") or node.get("priceMin") or 0)
                    discount_rate = float(node.get("priceDiscountRate") or 0)
                    
                    old_price = 0.0
                    if discount_rate > 0 and price > 0:
                        old_price = round(price / (1 - (discount_rate / 100)), 2)
                        
                    deals.append({
                        "title": node.get("productName", ""),
                        "new_price": price,
                        "old_price": old_price,
                        "discount_pct": int(discount_rate),
                        "original_url": node.get("productLink", ""),
                        "affiliate_url": node.get("offerLink", node.get("productLink", "")),
                        "image_url": node.get("imageUrl", ""),
                        "store": "Shopee"
                    })
                except Exception as e:
                    logger.debug(f"Error parsing Shopee offer node: {e}")
                    continue
                    
        logger.info(f"Shopee API found {len(deals)} offers for keyword '{keyword}'")
        return deals


def generate_shopee_link(url: str) -> str:
    """
    Main entrypoint for generating Shopee affiliate links.
    1. Try official Shopee Affiliate Open API (fastest, most reliable).
    2. Fallback to Selenium LinkBuilder if cookies/session available.
    3. Fallback to Shopee universal tracking ID if configured.
    4. Return original URL if none succeeded.
    """
    # 1. Open API (GraphQL)
    api = ShopeeAffiliateAPI()
    if api.is_configured():
        link = api.generate_affiliate_link(url)
        if link:
            return link
            
    # 2. Selenium LinkBuilder (only if cookies/session exist)
    try:
        from .shopee_linkbuilder import generate_shopee_affiliate_link, SHOPEE_COOKIES_FILE
        if os.path.exists(SHOPEE_COOKIES_FILE) or os.getenv("SHOPEE_COOKIES_BASE64"):
            link = generate_shopee_affiliate_link(url, timeout=20)
            if link and link != url:
                return link
    except Exception as e:
        logger.debug(f"Selenium Shopee LinkBuilder fallback failed: {e}")

    # 3. Universal Affiliate ID / official Shopee tracking parameters
    affiliate_id = os.getenv("SHOPEE_AFFILIATE_ID", "").strip()
    if affiliate_id:
        separator = "&" if "?" in url else "?"
        # Shopee affiliate tracking: utm_source=an_{aff_id}&utm_medium=affiliates
        tracking_url = f"{url}{separator}utm_source=an_{affiliate_id}&utm_medium=affiliates&utm_campaign=-&utm_content=promobot&aff_id={affiliate_id}"
        logger.info(f"Generated Shopee tracking link with AID: {affiliate_id}")
        return tracking_url
        
    return url
