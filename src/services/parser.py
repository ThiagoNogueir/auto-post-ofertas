
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from ..utils.logger import logger

def parse_price(price_str: str) -> float:
    """Extrai valor numérico de string de preço (ex: 'R$ 1.200,00' -> 1200.0)"""
    try:
        # Remove R$, pontos e espaços
        clean = re.sub(r'[^\d,]', '', price_str)
        # Troca vírgula por ponto
        clean = clean.replace(',', '.')
        return float(clean)
    except:
        return 0.0

def extract_deals_from_html(html_content: str, source_url: str) -> List[Dict]:
    """
    Parser determinístico para extrair ofertas do HTML do Mercado Livre e Shopee.
    Substitui a IA, sendo mais rápido e sem custos.
    """
    deals = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    try:
        if 'mercadolivre.com' in source_url:
            deals = parse_mercadolivre(soup)
        elif 'shopee.com' in source_url:
            deals = parse_shopee(soup)
            
        logger.info(f"Parser extracted {len(deals)} deals from {source_url}")
        return deals
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        return []

def parse_mercadolivre(soup: BeautifulSoup) -> List[Dict]:
    items = []
    
    # Debug: Log HTML snippet to understand structure
    logger.debug(f"HTML length: {len(str(soup))}")
    
    # Try multiple selectors - ML uses React components now (POLYCARD)
    # Priority order: newest -> oldest
    cards = (soup.select('div[id="POLYCARD"]') or  # React component (2024+)
             soup.select('li.ui-search-layout__item') or 
             soup.select('div.ui-search-result__wrapper') or
             soup.select('div.poly-card') or
             soup.select('li[class*="ui-search"]') or
             soup.select('div[class*="poly-card"]') or
             soup.select('ol.ui-search-layout li') or
             soup.select('div.andes-card'))
    
    logger.info(f"Found {len(cards)} potential product cards in ML HTML")
    
    if len(cards) == 0:
        # Debug: print first 1000 chars to see what we got
        html_sample = str(soup)[:1000]
        logger.warning(f"No cards found. HTML sample: {html_sample}")
    
    for card in cards:
        try:
            # TITLE - try multiple selectors
            title_tag = (card.select_one('.ui-search-item__title') or
                        card.select_one('.poly-component__title') or
                        card.select_one('h2.ui-search-item__title') or
                        card.select_one('h2') or
                        card.select_one('a[class*="title"]'))
            
            if not title_tag:
                logger.debug("Skipping card: no title found")
                continue
            title = title_tag.get_text().strip()
            
            # LINK - must have a product link
            link_tag = (card.select_one('a.ui-search-link') or
                       card.select_one('a.poly-component__title') or
                       card.select_one('a[href*="/MLB-"]') or  # ML product URLs contain MLB-
                       card.select_one('a'))
            
            if not link_tag or not link_tag.get('href'):
                logger.debug(f"Skipping card '{title}': no valid link")
                continue
                
            original_url = link_tag.get('href')
            
            # Skip if not a product URL
            if 'mercadolivre.com.br' not in original_url and not original_url.startswith('/'):
                logger.debug(f"Skipping non-ML URL: {original_url}")
                continue
            
            # Make URL absolute if relative
            if original_url.startswith('/'):
                original_url = f"https://www.mercadolivre.com.br{original_url}"
            
            # PRICE EXTRACTION (Improved)
            # Strategy: Try to find specific "current price" container first
            
            # 1. Try Specific Current Price Selectors (New Layout)
            current_price_container = (card.select_one('.poly-price__current .andes-money-amount__fraction') or
                                     card.select_one('.ui-search-price__second-line .andes-money-amount__fraction') or 
                                     card.select_one('.price-tag-amount .price-tag-fraction')) # Generic fallback
            
            new_price = 0.0
            
            if current_price_container:
                new_price = parse_price(current_price_container.get_text().strip())
            
            # 2. Fallback: Parse ALL prices and use heuristics
            if new_price == 0:
                all_prices = []
                price_elements = card.select('.andes-money-amount__fraction')
                for p in price_elements:
                    val = parse_price(p.get_text().strip())
                    if val > 0: all_prices.append(val)
                
                if all_prices:
                    # Heuristic: 
                    # If 2 prices: usually [Old Price, New Price] -> take lower
                    # If 3 prices: usually [Old Price, New Price, Installment] -> take middle or lower but > installment
                    # Let's take the minimum value that matches a reasonable deal price logic
                    # For now, let's take the smallest value that is likely not an installment (heuristic > 20 reais? risky)
                    # Safest for now: take the *last* price found if multiple, as usually current price is below old price
                    new_price = all_prices[-1]  # Often current price is last or second
                    
                    # Refinement: if we have 2 distinct prices, smaller is likely current
                    if len(set(all_prices)) >= 2:
                        sorted_prices = sorted(list(set(all_prices)))
                        # If the smallest is very small compared to largest (e.g. < 15%), it might be installment
                        if sorted_prices[0] < sorted_prices[-1] * 0.15:
                             # Skip the installment, take the next smallest
                             if len(sorted_prices) > 1:
                                 new_price = sorted_prices[1]
                        else:
                             new_price = sorted_prices[0]

            # OLD PRICE EXTRACTION
            old_price = 0.0
            old_price_container = (card.select_one('.poly-price__old .andes-money-amount__fraction') or
                                  card.select_one('.ui-search-price__original-value .andes-money-amount__fraction'))
            
            if old_price_container:
                old_price = parse_price(old_price_container.get_text().strip())
            elif new_price > 0:
                old_price = new_price * 1.3 # Fake if not found

            # Skip if no valid price
            if new_price == 0:
                logger.debug(f"Skipping '{title}': no valid price")
                continue
            
            # Final sanity check: if old price < new price, swap them or fix
            if old_price > 0 and old_price < new_price:
                 old_price = new_price * 1.2 # Fix weird data
            
            # CENTS Handling (optional - append cents if found separately)
            # Some layouts have cents in a separate superscrit tag
            # We can improve this later if needed. For now main fraction is usually enough.
            
            # IMAGE - Improved extraction logic
            image_url = None
            img_tag = card.select_one('img')
            if img_tag:
                # Prioritize lazy loading attributes which usually hold high-res real images
                image_url = img_tag.get('data-src') or img_tag.get('data-lazy')
                
                # If not found, fall back to src, but avoid small base64 placeholders
                if not image_url:
                    src = img_tag.get('src')
                    if src and not src.startswith('data:image'):
                        image_url = src

            # CATEGORY DETECTION
            category = detect_category(title, original_url)

            logger.debug(f"Found deal: {title} - R$ {new_price} (Old: {old_price}) [{category}]")
            
            items.append({
                'title': title,
                'new_price': new_price,
                'old_price': old_price,
                'original_url': original_url,
                'image_url': image_url,
                'category': category
            })
            
        except Exception as e:
            logger.debug(f"Error parsing card: {e}")
            continue
    
    logger.info(f"Successfully parsed {len(items)} deals from Mercado Livre")
    return items

def parse_shopee(soup: BeautifulSoup) -> List[Dict]:
    items = []
    # Generic selectors for Shopee item cards
    cards = soup.select('li[data-sqe="item"]') or \
            soup.select('.col-xs-2-4') or \
            soup.select('.shopee-search-item-result__item') or \
            soup.select('div[class*="item-card"]') # Generic fallback
            
    for card in cards:
        try:
            # LINK
            link_tag = card.select_one('a[data-sqe="link"]') or card.select_one('a')
            if not link_tag: continue
            url_suffix = link_tag.get('href')
            original_url = f"https://shopee.com.br{url_suffix}" if url_suffix.startswith('/') else url_suffix
            
            # TITLE
            title_tag = card.select_one('div[data-sqe="name"]') or \
                        card.select_one('.ie3A+n') or \
                        card.select_one('.Cve6sh') or \
                        card.select_one('[class*="name"]') # Generic fallback
            
            # Fallback title from image alt
            if not title_tag:
                 imgs = card.select('img')
                 if imgs: title = imgs[-1].get('alt', 'Oferta Shopee')
                 else: title = "Oferta Shopee"
            else:
                 title = title_tag.get_text().strip()

            # PRICE
            price_tag = card.select_one('span[data-sqe="price"]') or \
                        card.select_one('.ZEgDH9') or \
                        card.select_one('[class*="price"]')
            new_price = 0.0
            if price_tag:
                new_price = parse_price(price_tag.get_text())
                
            # IMAGE
            img_tag = card.select_one('img')
            image_url = img_tag.get('src') if img_tag else None
            
            # CATEGORY
            category = detect_category(title, original_url)
            
            items.append({
                'title': title,
                'new_price': new_price,
                'old_price': 0,
                'original_url': original_url,
                'image_url': image_url,
                'category': category,
                'store': 'Shopee'
            })
        except:
            continue
            
    return items

def detect_category(title: str, url: str) -> str:
    """
    Infers category from URL segments and title keywords.
    Prioritizes URL context.
    """
    url_lower = url.lower()
    title_lower = title.lower()
    
    # 1. URL Based Detection (Strongest Signal)
    if 'celulares-telefones' in url_lower or 'celular' in url_lower:
        return 'Celulares'
    if 'informatica' in url_lower or 'notebook' in url_lower or 'computad' in url_lower:
        return 'Informática'
    if 'games' in url_lower or 'game' in url_lower or 'console' in url_lower or 'videogame' in url_lower:
        return 'Games'
    if 'eletrodomesticos' in url_lower:
        return 'Casa'
    if 'tv' in url_lower and 'audio' in url_lower:
        return 'Eletrônicos'
        
    # 2. Title Keyword Fallback
    if any(k in title_lower for k in ['iphone', 'samsung galaxy', 'motorola', 'xiaomi', 'redmi', 'smartphone']):
        return 'Celulares'
    if any(k in title_lower for k in ['notebook', 'laptop', 'macbook', 'dell', 'lenovo', 'acer', 'monitor', 'mouse', 'teclado']):
        return 'Informática'
    if any(k in title_lower for k in ['ps5', 'playstation', 'xbox', 'nintendo', 'switch', 'game', 'jogo']):
        return 'Games'
    if any(k in title_lower for k in ['tv', 'smart tv', 'som', 'fones', 'bluetooth']):
        return 'Eletrônicos'
    if any(k in title_lower for k in ['geladeira', 'fogão', 'microondas', 'aspirador', 'fritadeira', 'air fryer']):
        return 'Casa'
        
    return 'Outros'
