"""
Pinterest API v5 Integration
Handles automatic publishing of Pins with generated promotional banners and affiliate links.
"""

import os
import base64
import requests
from ..utils.logger import logger
from .pinterest_banner import create_pinterest_pin

class PinterestAPI:
    def __init__(self):
        self.access_token = os.getenv("PINTEREST_ACCESS_TOKEN", "")
        self.default_board_id = os.getenv("PINTEREST_BOARD_ID", "")
        self.base_url = "https://api.pinterest.com/v5"

    def is_configured(self) -> bool:
        """Check if Pinterest token is configured"""
        return bool(self.access_token)

    def get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def list_boards(self) -> list:
        """Fetch all boards belonging to the authenticated account"""
        if not self.is_configured():
            logger.warning("Pinterest API token not configured")
            return []
        try:
            url = f"{self.base_url}/boards"
            res = requests.get(url, headers=self.get_headers(), timeout=15)
            if res.status_code == 200:
                data = res.json()
                items = data.get("items", [])
                logger.info(f"Pinterest: {len(items)} boards found")
                return items
            else:
                logger.error(f"Pinterest list_boards error: {res.status_code} - {res.text}")
                return []
        except Exception as e:
            logger.error(f"Pinterest list_boards exception: {e}")
            return []

    def create_board(self, name: str, description: str = "Melhores achadinhos e ofertas com desconto!") -> str:
        """Creates a board and returns its board_id"""
        try:
            url = f"{self.base_url}/boards"
            payload = {
                "name": name,
                "description": description,
                "privacy": "PUBLIC"
            }
            res = requests.post(url, json=payload, headers=self.get_headers(), timeout=15)
            if res.status_code == 201 or res.status_code == 200:
                board_id = res.json().get("id")
                logger.info(f"Pinterest: Board '{name}' created with ID: {board_id}")
                return board_id
            else:
                logger.error(f"Pinterest create_board error: {res.status_code} - {res.text}")
                return ""
        except Exception as e:
            logger.error(f"Pinterest create_board exception: {e}")
            return ""

    def create_pin(
        self,
        title: str,
        price: float,
        affiliate_url: str,
        old_price: float = None,
        image_url: str = None,
        category: str = "Achadinhos",
        store: str = "Mercado Livre",
        coupon_code: str = None,
        board_id: str = None
    ) -> bool:
        """
        Generates a 1000x1500 Pin banner and publishes it to Pinterest.
        """
        if not self.is_configured():
            logger.warning("Pinterest API not configured. Skipping Pin creation.")
            return False

        target_board = board_id or self.default_board_id
        if not target_board:
            # Fallback: try to find an existing board
            boards = self.list_boards()
            if boards:
                target_board = boards[0].get("id")
            else:
                # Create a default board if none exists
                target_board = self.create_board("Achadinhos e Ofertas Imperdíveis")

        if not target_board:
            logger.error("Pinterest: No target board ID available to create Pin.")
            return False

        try:
            # 1. Generate the Pin image in memory
            pin_img = create_pinterest_pin(
                title=title,
                price=price,
                old_price=old_price,
                image_url=image_url,
                category=category,
                store=store,
                coupon_code=coupon_code
            )

            # Convert to base64
            import io
            buf = io.BytesIO()
            pin_img.save(buf, format="PNG", quality=95)
            img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            # 2. Build Description with high-converting Pinterest SEO tags
            desc_parts = [
                f"🔥 {title}",
                f"💰 Preço com Desconto: R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            ]
            if old_price and old_price > price:
                desc_parts.append(f"❌ De: R$ {old_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            if coupon_code:
                desc_parts.append(f"🎟️ Cupom Extra: {coupon_code}")

            desc_parts.append(f"\n🛒 Compre direto na {store} pelo link do Pin!")
            desc_parts.append(f"\n#achadinhos #ofertas #desconto #{category.lower().replace(' ', '')} #{store.lower().replace(' ', '')} #compras")

            pin_description = "\n".join(desc_parts)

            # 3. Create Pin via Pinterest API v5
            url = f"{self.base_url}/pins"
            payload = {
                "link": affiliate_url,
                "title": title[:100], # Max 100 chars
                "description": pin_description[:800], # Max 800 chars
                "board_id": target_board,
                "media_source": {
                    "source_type": "image_base64",
                    "content_type": "image/png",
                    "data": img_b64
                }
            }

            res = requests.post(url, json=payload, headers=self.get_headers(), timeout=25)
            if res.status_code in [200, 201]:
                pin_data = res.json()
                pin_id = pin_data.get("id")
                logger.info(f"Pinterest: Pin created successfully! ID: {pin_id} | Link: {affiliate_url}")
                return True
            else:
                logger.error(f"Pinterest create_pin error: {res.status_code} - {res.text}")
                return False

        except Exception as e:
            logger.error(f"Pinterest create_pin exception: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
