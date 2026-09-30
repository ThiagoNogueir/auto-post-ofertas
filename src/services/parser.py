
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
            deals = parse_mercadolivre(soup, source_url=source_url)
        elif 'shopee.com' in source_url:
            deals = parse_shopee(soup, source_url=source_url)
            
        logger.info(f"Parser extracted {len(deals)} deals from {source_url}")
        return deals
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        return []

def parse_mercadolivre(soup: BeautifulSoup, source_url: str = "") -> List[Dict]:
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
            category = detect_category(title, original_url, source_url=source_url)

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

def parse_shopee(soup: BeautifulSoup, source_url: str = "") -> List[Dict]:
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
            category = detect_category(title, original_url, source_url=source_url)
            
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

def detect_category(title: str, url: str, source_url: str = "") -> str:
    """
    Infers category from URL segments and title keywords with regex word boundaries.
    Prevents cross-category substring collisions (e.g. 'geração' matching 'ração', 'autônomo' matching 'omo').
    Supports all 24 Mercado Livre sidebar categories and routes to proper groups.
    """
    import unicodedata
    import re

    def strip_accents(text: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

    def match_any(keywords: list, text: str) -> bool:
        for k in keywords:
            kn = strip_accents(k.lower()).strip()
            if not kn:
                continue
            pattern = r'\b' + re.escape(kn) + r'(?:s|es)?\b'
            if re.search(pattern, text):
                return True
        return False

    url_lower = url.lower()
    source_lower = source_url.lower()
    combined_url = f"{url_lower} {source_lower}"
    t_norm = strip_accents(title.lower())
    u_norm = strip_accents(combined_url)

    # 1. Tech Primaries: TV Box, Smart TV, Smartwatch, Streaming -> Eletrônicos (Tech & Games)
    tech_primary_kw = [
        'smartwatch', 'smart watch', 'apple watch', 'galaxy watch', 'relogio smartwatch',
        'relógio smartwatch', 'pulseira inteligente', 'mi band', 'amazfit', 'haylou',
        'huawei watch', 'fitbit', 'garmin', 'relogio inteligente', 'relógio inteligente',
        'tv box', 'smart tv box', 'aquario stv', 'aquário stv', 'stv-3000', 'stv-2000',
        'smart tv', 'chromecast', 'fire stick', 'firetv', 'tv stick', 'conversor digital'
    ]
    if match_any(tech_primary_kw, t_norm):
        return 'Eletrônicos'

    # 2. Bebês & Maternidade (Checked before Moda to prevent baby/kids clothes from going to adult fashion)
    bebes_kw = [
        'bebe', 'bebê', 'bebes', 'bebês', 'infantil', 'infantis', 'recem nascido', 'recem-nascido',
        'recém nascido', 'recém-nascido', 'maternidade', 'enxoval', 'fralda', 'fraldas',
        'pampers', 'huggies', 'mamadeira', 'chupeta', 'mordedor', 'lenco umedecido', 'lenço umedecido',
        'toalha umedecida', 'carrinho de bebe', 'carrinho de bebê', 'carrinho de passeio bebe',
        'bebe conforto', 'bebê conforto', 'berco', 'berço', 'chiqueirinho', 'banheira bebe',
        'aspirador nasal', 'babador', 'body bebe', 'body infantil', 'macacao bebe', 'macacão bebê',
        'macacao infantil', 'vestido bebe', 'vestido infantil', 'cueiro', 'ninho redutor',
        'mochila maternidade', 'bolsa maternidade', 'trocador portatil', 'porta chupeta',
        'copo de transicao', 'esterilizador de mamadeira', 'cadeirinha para auto', 'pagaozinho',
        'mijaozinho', 'mijãozinho', 'tapa fralda', 'culote bebe', 'pantufa bebe', 'sapatinho bebe'
    ]
    if match_any(bebes_kw, t_norm):
        return 'Bebês'

    # 3. Brinquedos & Hobbies (Checked before Moda to prevent Barbie dresses/shoes from going to adult fashion)
    brinquedos_kw = [
        'boneca', 'boneco', 'barbie', 'baby alive', 'polly pocket', 'hot wheels', 'lego',
        'playmobil', 'nerf', 'massinha play-doh', 'play-doh', 'carrinho de controle remoto',
        'carrinho controle remoto', 'pista hot wheels', 'quebra-cabeca', 'quebra-cabeça',
        'jogo de tabuleiro', 'banco imobiliario', 'cara a cara', 'pelucia', 'pelúcia',
        'ursinho de pelucia', 'patinete infantil', 'triciclo infantil', 'slime', 'figura de acao',
        'action figure', 'funko pop', 'pixtoy', 'magic the gathering', 'pokemon tcg'
    ]
    if match_any(brinquedos_kw, t_norm):
        return 'Brinquedos'

    # 4. Pets & Animais (Word boundary eliminates 'geração', 'duração', 'refrigeração', etc.)
    pets_kw = [
        'racao', 'ração', 'premier pet', 'royal canin', 'golden especial', 'whiskas', 'pedigree',
        'quatree', 'bravecto', 'nexgard', 'simparic', 'antipulgas', 'antipulga', 'carrapato',
        'vermifugo', 'vermífugo', 'tapete higienico', 'tapete higiênico', 'caminha pet', 'cama pet',
        'cama para cachorro', 'arranhador', 'areia para gato', 'areia higienica', 'pipicat',
        'comedouro pet', 'bebedouro pet', 'fonte pet', 'coleira', 'guia para cachorro',
        'peitoral cachorro', 'peitoral pet', 'brinquedo para cachorro', 'brinquedo pet',
        'brinquedo para gato', 'gaiola', 'shampoo pet', 'filhote cao',
        'filhote cachorro', 'gatos castrados', 'petisco', 'petiscos', 'churu', 'pet shop',
        'focinheira', 'mordedor pet', 'granulado sanitario'
    ]
    if match_any(pets_kw, t_norm):
        return 'Pets'

    # 5. Automotivo (Checked before Tools/Informatica to catch car chargers, battery jumpers, etc.)
    automotivo_kw = [
        'pneu', 'pneus', 'som automotivo', 'central multimidia', 'central multimídia',
        'farol de milha', 'lampada led h4', 'lampada led h7', 'bateria de carro', 'bateria automotiva',
        'moura', 'heliar', 'oleo para motor', 'óleo para motor', 'oleo 5w30', 'oleo 15w40',
        'capacete para moto', 'capacete moto', 'capa para carro', 'alarme automotivo',
        'camera de re', 'câmera de ré', 'rastreador veicular', 'suporte veicular',
        'carregador automotivo', 'carregador veicular', 'carregador de bateria automotivo',
        'carregador bateria carro', 'palheta parabrisa', 'tapete automotivo', 'calota',
        'aditivo radiador'
    ]
    if match_any(automotivo_kw, t_norm):
        return 'Automotivo'

    # 6. Casa - Aspiradores & Eletrodomésticos (Checked BEFORE Ferramentas so WAP/Kärcher vacuums go to Casa)
    casa_eletro_kw = [
        'aspirador de po', 'aspirador de pó', 'aspirador po', 'aspirador vertical', 'robo aspirador',
        'robô aspirador', 'aspirador wap', 'aspirador karcher', 'cafeteira', 'air fryer',
        'fritadeira sem oleo', 'fritadeira eletrica', 'liquidificador', 'batedeira',
        'sanduicheira', 'micro-ondas', 'microondas', 'fogao', 'fogão', 'cooktop',
        'forno eletrico', 'forno elétrico', 'geladeira', 'refrigerador', 'freezer',
        'purificador de agua', 'purificador de água', 'bebedouro de agua', 'chaleira eletrica',
        'panela de pressao eletrica', 'panela eletrica', 'torradeira', 'ferro de passar',
        'vaporizador de roupas', 'maquina de lavar', 'máquina de lavar', 'lava e seca',
        'tanquinho', 'ventilador', 'ar condicionado', 'climatizador de ar', 'umidificador de ar'
    ]
    if match_any(casa_eletro_kw, t_norm):
        return 'Casa'

    # 7. Ferramentas & Construção
    ferramentas_kw = [
        'kit ferramentas', 'kit de ferramentas', 'furadeira', 'parafusadeira', 'esmerilhadeira',
        'serra circular', 'serra tico-tico', 'martelete', 'compressor de ar',
        'lavadora de alta pressao', 'lavadora alta pressao', 'maleta de ferramentas',
        'caixa de ferramentas', 'jogo de chaves', 'chave de fenda', 'chave philips',
        'chave combinada', 'chave catraca', 'trena', 'nivel laser', 'nível laser',
        'alicate universal', 'alicate de pressao', 'inversora de solda', 'motosserra',
        'rocadeira', 'disco de corte', 'broca', 'jogo de brocas', 'bosch', 'dewalt', 'makita', 'vonder'
    ]
    if match_any(ferramentas_kw, t_norm):
        return 'Ferramentas'

    # 8. Bebidas, Alimentos & Suplementos Nutricionais (Ofertas de Mercado & Bebidas)
    # Suplementos, Vitaminas e Ômega vão para Mercado & Bebidas (NUNCA para Moda)
    bebidas_kw = [
        'vinho', 'espumante', 'prosecco', 'cerveja', 'chope', 'whisky', 'whiskey', 'vodka',
        'gin', 'licor', 'tequila', 'rum', 'cachaca', 'cachaça', 'refrigerante', 'coca-cola',
        'pepsi', 'guarana antarctica', 'energetico', 'energético', 'red bull', 'monster energy',
        'isotonico', 'isotônico', 'powerade', 'gatorade', 'agua mineral', 'água mineral',
        'azeite de oliva', 'azeite extra virgem', 'cafe em grao', 'café em grão',
        'capsulas de cafe', 'cápsulas de café', 'nespresso', 'dolce gusto',
        'omega', 'ômega', 'omega 3', 'ômega 3', 'caps', 'capsulas', 'cápsulas',
        'suplemento', 'suplementos', 'suplemento alimentar', 'vitamina', 'vitaminas',
        'multivitaminico', 'multivitamínico', 'zinco', 'magnesio', 'magnésio', 'melatonina',
        'coenzima q10', 'feno grego', 'boro', 'arginina', 'zma', 'creapure', 'dark lab',
        'max titanium', 'growth supplements', 'integralmedica', 'black skull', 'probiotica',
        'probiotico', 'probiótico', 'oleo de peixe', 'óleo de peixe', 'whey', 'whey protein',
        'creatina', 'creatina monohidratada', 'bcaa', 'glutamina', 'albumina', 'colageno',
        'colágeno', 'hipercalorico', 'hipercalórico', 'pre-treino', 'pré-treino', 'testo',
        'drenalinf', 'termogenico', 'termogênico', 'dark mass', 'massa muscular'
    ]
    if match_any(bebidas_kw, t_norm):
        return 'Bebidas'

    # 9. Esportes & Fitness (Equipamentos e Acessórios Esportivos)
    esportes_kw = [
        'halteres', 'haltere', 'anilha', 'kettlebell', 'barra fixa', 'barra macica',
        'banco de supino', 'esteira ergometrica', 'esteira ergométrica', 'bicicleta ergometrica',
        'bicicleta aro', 'mountain bike', 'corda de pular', 'faixa elastica', 'caneleira peso',
        'luva de boxe', 'saco de pancada', 'bola de futebol', 'bola de basquete', 'bola de volei',
        'raquete de tenis', 'raquete de beach tennis', 'patins', 'skate'
    ]
    if match_any(esportes_kw, t_norm):
        return 'Esportes'

    # 10. Beleza & Perfumaria
    beleza_kw = [
        'perfume', 'eau de parfum', 'eau de toilette', 'desodorante', 'hidratante corporal',
        'serum facial', 'sérum facial', 'protetor solar', 'shampoo', 'condicionador',
        'mascara capilar', 'máscara capilar', 'secador de cabelo', 'prancha alisadora',
        'chapinha', 'babyliss', 'modelador de cachos', 'barbeador eletrico', 'aparador de pelos',
        'maquiagem', 'batom', 'rimel', 'rímel', 'base facial', 'esmalte', 'carolina herrera',
        'paco rabanne', 'la roche-posay', 'cerave'
    ]
    if match_any(beleza_kw, t_norm):
        return 'Beleza'

    # 11. Informática - Mochila para Notebook / Acessórios (Checked before general Moda)
    if 'mochila para notebook' in t_norm or 'mochila notebook' in t_norm:
        return 'Informática'

    # 12. Moda & Calçados (Roupas, Calçados e Acessórios de Vestir)
    moda_kw = [
        'tenis', 'tênis', 'sapato', 'sapatilha', 'sandalia', 'sandália', 'chinelo',
        'bota', 'coturno', 'camisa', 'camisa polo', 'camisa termica', 'camisa térmica',
        'camiseta', 'calca', 'calça', 'calca jeans', 'calca moletom', 'calça moletom',
        'bermuda', 'shorts', 'short', 'jaqueta', 'moletom', 'vestido', 'saia',
        'cueca', 'cuecas', 'calcinha', 'calcinhas', 'sutia', 'sutiã', 'mochila',
        'bolsa feminina', 'carteira masculina', 'oculos de sol', 'óculos de sol',
        'relogio masculino', 'relogio feminino', 'relogio de pulso', 'meia', 'legging',
        'top fitness', 'sunga', 'biquini', 'maiô', 'cinto', 'bone', 'boné',
        'nike', 'adidas', 'olympikus', 'asics', 'mizuno', 'kappa'
    ]
    if match_any(moda_kw, t_norm):
        return 'Moda'

    # 13. Casa - Móveis, Cama, Mesa, Banho e Limpeza
    casa_kw = [
        'jogo de toalha', 'jogo de panela', 'jogo de cama', 'jogo de lencol',
        'jogo de taca', 'jogo de copo', 'jogo de prato', 'jogo de xicara',
        'jogo de faca', 'jogo de talher', 'toalha de banho', 'edredom', 'cobertor',
        'lencol', 'lençol', 'travesseiro', 'manta', 'tapete de sala', 'tapete',
        'cortina', 'almofada', 'colchao', 'colchão', 'cobre leito', 'panela',
        'faqueiro', 'talher', 'garrafa termica', 'garrafa térmica', 'pote hermetico',
        'marmita', 'lixeira', 'varal', 'chuveiro', 'torneira', 'guarda-roupa',
        'sofa', 'sofá', 'poltrona', 'cadeira gamer', 'mesa gamer', 'sabao em po',
        'sabão em pó', 'sabao liquido', 'sabão líquido', 'amaciante comfort',
        'amaciante downy', 'detergente ype', 'detergente finish', 'tablete finish',
        'desinfetante', 'lava roupas omo', 'sabao omo', 'multiuso veja', 'limpador veja'
    ]
    if match_any(casa_kw, t_norm):
        return 'Casa'

    # 14. Games
    games_kw = [
        'playstation', 'ps5', 'ps4', 'ps3', 'xbox', 'nintendo switch', 'nintendo',
        'switch oled', 'switch lite', 'videogame', 'video game', 'console',
        'dualsense', 'dualshock', 'joy-con', 'joycon', 'gamepad', 'volante g29', 'midia fisica'
    ]
    if match_any(games_kw, t_norm):
        return 'Games'

    if 'jogo ' in t_norm or 'jogos ' in t_norm:
        if not any(f in t_norm for f in ['jogo de', 'jogos de', 'jogo americano']):
            if any(w in t_norm for w in ['ps5', 'ps4', 'xbox', 'switch', 'pc', 'rpg', 'fc 24', 'fc 25', 'fifa', 'gta', 'pokemon', 'mario', 'zelda', 'resident evil', 'spider-man', 'god of war']):
                return 'Games'

    # 15. Celulares
    celulares_kw = [
        'iphone', 'ipad', 'tablet', 'smartphone', 'celular', 'galaxy s', 'galaxy a', 'galaxy m', 'galaxy z',
        'redmi', 'xiaomi', 'motorola', 'moto g', 'moto e', 'moto edge', 'poco', 'realme', 'infinix'
    ]
    if match_any(celulares_kw, t_norm):
        return 'Celulares'

    # 16. Informática
    informatica_kw = [
        'notebook', 'laptop', 'macbook', 'computador', 'pc desktop', 'pc gamer', 'monitor',
        'mouse', 'teclado', 'mousepad', 'webcam', 'roteador', 'ssd', 'nvme', 'memoria ram',
        'memória ram', 'placa de video', 'placa de vídeo', 'placa-mae', 'placa mae',
        'processador ryzen', 'processador intel', 'core i3', 'core i5', 'core i7', 'core i9',
        'ryzen 5', 'ryzen 7', 'impressora', 'baseus', 'ugreen', 'lenovo', 'qcy',
        'cabo usb', 'cabo tipo c', 'cabo lightning', 'hub usb'
    ]
    if match_any(informatica_kw, t_norm):
        return 'Informática'

    # 17. Eletrônicos
    eletronicos_kw = [
        'smart tv', 'televisao', 'televisão', 'tv 4k', 'tv 32', 'tv 43', 'tv 50', 'tv 55', 'tv 65',
        'soundbar', 'caixa de som', 'fone de ouvido', 'headphone', 'earbuds', 'airpods', 'airpod',
        'jbl', 'bluetooth', 'alexa', 'echo dot', 'echo pop', 'projetor', 'kindle'
    ]
    if match_any(eletronicos_kw, t_norm):
        return 'Eletrônicos'

    # 18. URL Category Fallback (Only if Title didn't match specific consumer product keywords!)
    # Prevents sponsored/cross-category products on category pages from being misclassified
    if 'category=mlb1071' in u_norm or '/animais/' in u_norm or '/pets/' in u_norm or '/pet-shop/' in u_norm:
        return 'Pets'
    if 'category=mlb1384' in u_norm or '/bebes/' in u_norm:
        return 'Bebês'
    if 'category=mlb1132' in u_norm or '/brinquedos-hobbies/' in u_norm or '/brinquedos/' in u_norm:
        return 'Brinquedos'
    if 'category=mlb1051' in u_norm or 'celulares-telefones' in u_norm or '/loja/apple' in u_norm:
        return 'Celulares'
    if 'category=mlb1648' in u_norm or 'informatica' in u_norm or 'computadores' in u_norm:
        return 'Informática'
    if 'category=mlb1144' in u_norm or 'consoles-video-games' in u_norm or '/games/' in u_norm:
        return 'Games'
    if 'category=mlb278123' in u_norm or 'category=mlb1403' in u_norm or '/bebidas/' in u_norm or '/alimentos-bebidas/' in u_norm:
        return 'Bebidas'
    if 'category=mlb1246' in u_norm or '/beleza-cuidado-pessoal/' in u_norm or '/beleza/' in u_norm:
        return 'Beleza'
    if 'category=mlb409431' in u_norm or '/saude/' in u_norm:
        return 'Saúde'
    if 'category=mlb1430' in u_norm or '/calcados-roupas-bolsas/' in u_norm or '/moda/' in u_norm:
        return 'Moda'
    if 'category=mlb1276' in u_norm or '/esportes-fitness/' in u_norm:
        return 'Esportes'
    if 'category=mlb1500' in u_norm or '/ferramentas/' in u_norm:
        return 'Ferramentas'
    if 'category=mlb1743' in u_norm or '/acessorios-veiculos/' in u_norm or '/automotivo/' in u_norm:
        return 'Automotivo'
    if 'category=mlb1512' in u_norm or '/construcao/' in u_norm:
        return 'Construção'
    if 'category=mlb1499' in u_norm or 'category=mlb1574' in u_norm or 'category=mlb5726' in u_norm or 'eletrodomesticos' in u_norm or 'casa-moveis' in u_norm or 'cama-mesa-banho' in u_norm:
        return 'Casa'
    if 'category=mlb1000' in u_norm or 'category=mlb1039' in u_norm or 'eletronicos-audio' in u_norm or 'tv-audio' in u_norm:
        return 'Eletrônicos'

    return 'Outros'

