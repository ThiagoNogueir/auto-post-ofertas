
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
                                  card.select_one('.ui-search-price__original-value .andes-money-amount__fraction') or
                                  card.select_one('.andes-money-amount--previous .andes-money-amount__fraction'))
            
            if old_price_container:
                old_price = parse_price(old_price_container.get_text().strip())

            # DISCOUNT PERCENTAGE EXTRACTION
            discount_container = (card.select_one('.poly-price__discount') or
                                 card.select_one('.ui-search-price__discount') or
                                 card.select_one('.andes-money-amount__discount') or
                                 card.select_one('[class*="discount"]'))
            
            discount_pct = 0
            if discount_container:
                disc_match = re.search(r'(\d+)%', discount_container.get_text())
                if disc_match:
                    discount_pct = int(disc_match.group(1))

            # Calculate or synchronize old price and discount percentage
            if discount_pct > 0 and (old_price == 0 or old_price <= new_price):
                old_price = round(new_price / (1 - (discount_pct / 100)), 2)
            elif old_price > new_price and discount_pct == 0:
                discount_pct = round(((old_price - new_price) / old_price) * 100)

            # Skip if no valid price
            if new_price == 0:
                logger.debug(f"Skipping '{title}': no valid price")
                continue
            
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

            logger.debug(f"Found deal: {title} - R$ {new_price} (Old: {old_price}, {discount_pct}% OFF) [{category}]")
            
            items.append({
                'title': title,
                'new_price': new_price,
                'old_price': old_price,
                'discount_pct': discount_pct,
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
    Accurately supports top selling e-commerce categories:
    Celulares, Informática, Eletrônicos, Games, Casa, Bebidas, Beleza, Moda, Ferramentas, Automotivo.
    """
    import unicodedata
    def strip_accents(text: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

    url_lower = url.lower()
    title_lower = title.lower()
    t_norm = strip_accents(title_lower)
    u_norm = strip_accents(url_lower)
    
    # 1. URL Based Detection (Strongest Signal)
    if 'celulares-telefones' in u_norm or 'celular' in u_norm or 'category=mlb1051' in u_norm:
        return 'Celulares'
    if 'informatica' in u_norm or 'computadores' in u_norm or 'category=mlb1648' in u_norm:
        return 'Informática'
    if 'consoles-video-games' in u_norm or '/games/' in u_norm or 'video-games' in u_norm or 'category=mlb1144' in u_norm:
        return 'Games'
    if 'category=mlb278123' in u_norm or 'category=mlb1403' in u_norm or '/bebidas/' in u_norm or '/alimentos-bebidas/' in u_norm:
        return 'Bebidas'
    if 'category=mlb1246' in u_norm or '/beleza-cuidado-pessoal/' in u_norm or '/beleza/' in u_norm:
        return 'Beleza'
    if 'category=mlb1430' in u_norm or '/calcados-roupas-bolsas/' in u_norm or '/moda/' in u_norm:
        return 'Moda'
    if 'category=mlb1500' in u_norm or '/ferramentas/' in u_norm:
        return 'Ferramentas'
    if 'category=mlb1743' in u_norm or '/acessorios-veiculos/' in u_norm or '/automotivo/' in u_norm:
        return 'Automotivo'
    if 'eletrodomesticos' in u_norm or 'casa-moveis' in u_norm or 'cama-mesa-banho' in u_norm or 'category=mlb1499' in u_norm:
        return 'Casa'
    if 'eletronicos-audio' in u_norm or 'tv-audio' in u_norm or 'category=mlb1000' in u_norm:
        return 'Eletrônicos'

    # 2. Bebidas & Alimentos / Mercado (Title Keywords)
    bebidas_keywords = [
        'vinho', 'espumante', 'prosecco', 'cerveja', 'chope', 'whisky', 'whiskey', 'vodka',
        'gin ', 'licor', 'tequila', 'rum ', 'cachaca', 'cachaça', 'refrigerante', 'coca-cola',
        'pepsi', 'guarana antarctica', 'energetico', 'energético', 'red bull', 'monster energy',
        'isotonico', 'isotônico', 'powerade', 'gatorade', 'agua mineral', 'água mineral',
        'azeite de oliva', 'azeite extra virgem', 'cafe em grao', 'café em grão',
        'capsulas de cafe', 'cápsulas de café', 'nespresso', 'dolce gusto',
        'whey protein', 'whey 100%', 'creatina monohidratada', 'creatina'
    ]
    if any(k in t_norm for k in bebidas_keywords):
        return 'Bebidas'

    # 3. Beleza & Perfumaria (Title Keywords)
    beleza_keywords = [
        'perfume', 'eau de parfum', 'eau de toilette', 'desodorante', 'hidratante corporal',
        'serum facial', 'sérum', 'protetor solar', 'shampoo', 'condicionador', 'mascara capilar',
        'secador de cabelo', 'prancha alisadora', 'chapinha', 'babyliss', 'modelador de cachos',
        'barbeador eletrico', 'aparador de pelos', 'maquiagem', 'batom', 'rimel', 'base facial',
        'esmalte', 'carolina herrera', 'paco rabanne', 'la roche-posay', 'cerave'
    ]
    if any(k in t_norm for k in beleza_keywords):
        return 'Beleza'

    # 4. Ferramentas & Construção (Title Keywords)
    ferramentas_keywords = [
        'furadeira', 'parafusadeira', 'esmerilhadeira', 'serra circular', 'serra tico-tico',
        'martelete', 'compressor de ar', 'lavadora de alta pressao', 'lavadora de alta pressão',
        'karcher', 'wap', 'maleta de ferramentas', 'caixa de ferramentas', 'jogo de chaves',
        'chave de fenda', 'chave philips', 'chave combinada', 'chave catraca', 'trena',
        'nivel laser', 'nível laser', 'alicate universal', 'inversora de solda', 'bosch',
        'dewalt', 'makita', 'vonder'
    ]
    if any(k in t_norm for k in ferramentas_keywords):
        return 'Ferramentas'

    # 5. Moda & Calçados (Title Keywords)
    moda_keywords = [
        'tenis', 'tênis', 'sapato', 'sapatilha', 'sandalia', 'sandália', 'chinelo',
        'bota', 'coturno', 'camisa polo', 'camiseta', 'calca jeans', 'calça jeans',
        'bermuda', 'shorts', 'jaqueta', 'moletom', 'vestido', 'saia', 'cueca', 'calcinha',
        'sutia', 'sutiã', 'mochila', 'bolsa feminina', 'carteira masculina',
        'oculos de sol', 'óculos de sol', 'relogio masculino', 'relogio feminino',
        'nike', 'adidas', 'olympikus', 'asics', 'mizuno'
    ]
    if any(k in t_norm for k in moda_keywords):
        return 'Moda'

    # 6. Automotivo (Title Keywords)
    automotivo_keywords = [
        'pneu ', 'pneus', 'som automotivo', 'central multimidia', 'central multimídia',
        'lampada led h4', 'lampada led h7', 'farol de milha', 'bateria de carro', 'bateria automotiva',
        'moura', 'heliar', 'oleo para motor', 'óleo para motor', 'oleo 5w30', 'oleo 15w40',
        'capacete para moto', 'capacete moto', 'capa para carro', 'alarme automotivo',
        'camera de re', 'câmera de ré', 'rastreador veicular', 'suporte veicular'
    ]
    if any(k in t_norm for k in automotivo_keywords):
        return 'Automotivo'

    # 7. Casa - Kits e Eletrodomésticos
    casa_kits = [
        'jogo de toalha', 'jogo de panela', 'jogo de cama', 'jogo de lencol',
        'jogo de taca', 'jogo de copo', 'jogo de prato', 'jogo de xicara',
        'jogo de faca', 'jogo de talher', 'jogo de tigela', 'jogo de pote',
        'jogo de sobremesa', 'jogo de banheiro', 'jogo de cozinha', 'jogo americano', 'sousplat'
    ]
    if any(k in t_norm for k in casa_kits):
        return 'Casa'

    casa_keywords = [
        'cafeteira', 'balanca', 'air fryer', 'fritadeira', 'liquidificador', 'batedeira',
        'sanduicheira', 'micro-ondas', 'microondas', 'fogao', 'cooktop', 'forno eletrico',
        'geladeira', 'refrigerador', 'freezer', 'purificador', 'bebedouro', 'chaleira',
        'panela de pressao', 'panela eletrica', 'torradeira', 'aspirador', 'robo aspirador',
        'ferro de passar', 'vaporizador', 'maquina de lavar', 'lava e seca', 'tanquinho',
        'ventilador', 'ar condicionado', 'climatizador', 'umidificador', 'toalha', 'edredom',
        'cobertor', 'lencol', 'travesseiro', 'manta', 'tapete', 'cortina', 'almofada',
        'colchao', 'cobre leito', 'panela', 'faqueiro', 'talher', 'garrafa termica',
        'pote hermetico', 'marmita', 'lixeira', 'varal', 'chuveiro', 'torneira', 'guarda-roupa',
        'sofa', 'poltrona'
    ]
    if any(k in t_norm for k in casa_keywords):
        return 'Casa'

    # 8. Games - Consoles, Gamer Gear, Gaming Titles
    games_keywords = [
        'playstation', 'ps5', 'ps4', 'ps3', 'xbox', 'nintendo switch', 'nintendo',
        'switch oled', 'switch lite', 'videogame', 'video game', 'console',
        'dualsense', 'dualshock', 'joy-con', 'joycon', 'gamepad', 'gamer',
        'volante g29', 'midia fisica'
    ]
    if any(k in t_norm for k in games_keywords):
        return 'Games'

    if 'jogo ' in t_norm or 'jogos ' in t_norm:
        if not any(f in t_norm for f in ['jogo de', 'jogos de', 'jogo americano']):
            if any(w in t_norm for w in ['ps5', 'ps4', 'xbox', 'switch', 'pc', 'rpg', 'fc 24', 'fc 25', 'fifa', 'gta', 'pokemon', 'mario', 'zelda', 'resident evil', 'spider-man', 'god of war']):
                return 'Games'

    # 9. Celulares
    celulares_keywords = [
        'iphone', 'smartphone', 'celular', 'galaxy s', 'galaxy a', 'galaxy m', 'galaxy z',
        'redmi', 'xiaomi', 'motorola', 'moto g', 'moto e', 'moto edge', 'poco ', 'realme', 'infinix'
    ]
    if any(k in t_norm for k in celulares_keywords):
        return 'Celulares'

    # 10. Informática
    informatica_keywords = [
        'notebook', 'laptop', 'macbook', 'computador', 'pc desktop', 'pc gamer', 'monitor',
        'mouse', 'teclado', 'mousepad', 'webcam', 'roteador', 'ssd', 'nvme', 'memoria ram',
        'placa de video', 'placa-mae', 'placa mae', 'processador ryzen', 'processador intel',
        'core i3', 'core i5', 'core i7', 'core i9', 'ryzen 5', 'ryzen 7', 'impressora'
    ]
    if any(k in t_norm for k in informatica_keywords):
        return 'Informática'

    # 11. Eletrônicos
    eletronicos_keywords = [
        'smart tv', 'televisao', 'tv 4k', 'tv 32', 'tv 43', 'tv 50', 'tv 55', 'tv 65',
        'soundbar', 'caixa de som', 'fone de ouvido', 'headphone', 'earbuds', 'airpods',
        'jbl', 'bluetooth', 'alexa', 'echo dot', 'echo pop', 'projetor', 'smartwatch',
        'kindle'
    ]
    if any(k in t_norm for k in eletronicos_keywords):
        return 'Eletrônicos'

    return 'Outros'

