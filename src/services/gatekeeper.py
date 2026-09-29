"""
Sanity Gatekeeper Service for WhatsApp Groups.
Acts as a strict bouncer right before message dispatch to guarantee zero cross-category posting.

Two-Tier Defense Architecture:
- Tier 1: Positive Classifier (parser.py) maps keywords/URL to a category.
- Tier 2: Gatekeeper (this module) validates the target WhatsApp group with strict negative & positive constraints.
  Even if a product is misclassified upstream or has ambiguous tags, the Gatekeeper drops it immediately.
"""

import re
import unicodedata
from typing import Tuple
from ..utils.logger import logger

def _strip_accents(text: str) -> str:
    """Normalize text removing accents for reliable keyword matching."""
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower()

def _match_word(keywords: list, text_norm: str) -> str:
    """Check if any keyword matches as a full word (with optional plural 's' or 'es'). Returns matched word or empty."""
    for kw in keywords:
        kn = _strip_accents(kw.strip())
        if not kn:
            continue
        pattern = r'\b' + re.escape(kn) + r'(?:s|es)?\b'
        if re.search(pattern, text_norm):
            return kw
    return ""

# WhatsApp Group IDs configured in production
GROUP_TECH = "120363411755738436@g.us"      # Tecnologia & Games
GROUP_CASA = "120363422429816674@g.us"      # Casa & Decoração
GROUP_BELEZA = "120363424046630673@g.us"    # Beleza & Perfumaria
GROUP_MERCADO = "120363429863221899@g.us"   # Mercado, Bebidas & Suplementos
GROUP_MODA = "120363430459431315@g.us"      # Moda, Tênis & Calçados
GROUP_PETS = "120363430335326142@g.us"      # Pet Shop
GROUP_BEBES = "120363431007870836@g.us"     # Bebês & Brinquedos
GROUP_AUTO = "120363431434606946@g.us"      # Ferramentas & Automotivo

# 1. MODA - Forbidden terms (NEVER allow supplements, tools, PC hardware, tires, pet food, heavy appliances)
MODA_FORBIDDEN = [
    # Suplementos, Vitaminas e Nutrição
    'omega', 'omega 3', 'caps', 'capsulas', 'suplemento', 'suplementos', 'vitamina', 'vitaminas',
    'multivitaminico', 'zinco', 'magnesio', 'melatonina', 'creatina', 'creapure', 'whey',
    'whey protein', 'bcaa', 'glutamina', 'albumina', 'colageno', 'hipercalorico', 'pre-treino',
    'termogenico', 'dark lab', 'max titanium', 'growth supplements', 'integralmedica',
    'black skull', 'probiotica', 'oleo de peixe', 'coenzima q10', 'feno grego', 'boro',
    'arginina', 'zma', 'massa muscular', 'dark mass', 'drenalinf', 'testo',
    # Bebidas & Alimentos
    'vinho', 'cerveja', 'whisky', 'vodka', 'gin', 'azeite', 'cafe em grao', 'capsulas de cafe', 'nespresso',
    # Ferramentas & Construção
    'furadeira', 'parafusadeira', 'esmerilhadeira', 'serra circular', 'martelete', 'compressor de ar',
    'lavadora alta pressao', 'jogo de chaves', 'alicate', 'trena', 'inversora de solda', 'makita', 'dewalt', 'vonder',
    # Pets
    'racao', 'premier pet', 'royal canin', 'whiskas', 'pedigree', 'bravecto', 'nexgard', 'simparic',
    'arranhador', 'areia para gato', 'pipicat', 'tapete higienico',
    # Automotivo
    'pneu', 'som automotivo', 'farol de milha', 'bateria de carro', 'bateria automotiva', 'oleo para motor', 'oleo 5w30',
    # Componentes de Computador & Consoles
    'placa de video', 'placa mae', 'rtx 30', 'rtx 40', 'rx 6', 'rx 7', 'ryzen 5', 'ryzen 7',
    'core i5', 'core i7', 'memoria ram', 'ssd nvme', 'playstation', 'ps5', 'xbox series', 'nintendo switch',
    # Móveis & Eletrodomésticos Grandes
    'fogao', 'geladeira', 'refrigerador', 'freezer', 'microondas', 'maquina de lavar', 'ar condicionado', 'sofa', 'colchao',
    # Aparelhos de Academia
    'bicicleta ergometrica', 'bicicleta ergométrica', 'spinning', 'velocron', 'esteira ergometrica', 'esteira ergométrica', 'esteira eletrica', 'banco de supino',
    # Bebês, Crianças & Maternidade (NUNCA em Moda Adulto)
    'bebe', 'bebes', 'bebê', 'bebês', 'infantil', 'recem nascido', 'recem-nascido', 'recém nascido',
    'recém-nascido', 'maternidade', 'enxoval bebe', 'body bebe', 'macacao bebe', 'vestido bebe',
    'fralda', 'chupeta', 'mamadeira'
]

# 2. CASA & DECORAÇÃO - Forbidden terms (NEVER allow apparel/fashion, supplements, PC hardware, auto parts)
CASA_FORBIDDEN = [
    # Moda e Vestuário
    'vestido', 'saia', 'cueca', 'calcinha', 'sutia', 'lingerie', 'biquini', 'maio', 'sunga',
    'camisa polo', 'camiseta masculina', 'camiseta feminina', 'calca jeans', 'bermuda jeans',
    'salto alto', 'sapatilha feminina', 'scarpin', 'cropped', 'regata fitness',
    # Suplementos
    'whey', 'whey protein', 'creatina', 'creapure', 'omega', 'omega 3', 'bcaa', 'glutamina',
    'pre-treino', 'hipercalorico', 'dark lab', 'max titanium',
    # Hard Tech & Componentes
    'placa de video', 'placa mae', 'rtx', 'geforce', 'radeon', 'ryzen', 'core i7', 'core i9',
    'memoria ram', 'ssd nvme', 'ps5', 'playstation 5', 'xbox series', 'nintendo switch',
    'smartwatch', 'smart watch', 'apple watch', 'galaxy watch',
    # Automotivo
    'pneu aro', 'pastilha de freio', 'amortecedor', 'oleo 5w30', 'bateria automotiva', 'escapamento',
    # Pets
    'racao para', 'racao cachorro', 'racao gato', 'bravecto', 'nexgard', 'simparic', 'pipicat',
    # Aparelhos de Academia Pesados
    'bicicleta ergometrica', 'bicicleta ergométrica', 'spinning', 'velocron', 'esteira ergometrica', 'esteira ergométrica'
]

# 3. TECNOLOGIA & GAMES - Forbidden terms (NEVER allow clothing, food, grocery, cleaning, cosmetics)
TECH_FORBIDDEN = [
    'vestido', 'saia', 'cueca', 'calcinha', 'sutia', 'lingerie', 'biquini', 'maio', 'sunga',
    'calca jeans', 'bermuda jeans', 'sandalia salto', 'sapatilha', 'whey', 'creatina', 'omega 3',
    'cerveja', 'vinho', 'whisky', 'azeite', 'cafe em grao', 'racao', 'lencol', 'edredom',
    'toalha de banho', 'faqueiro', 'cortina blecaute', 'jogo de cama', 'perfume', 'batom',
    'esmalte', 'rimel', 'base facial', 'shampoo', 'condicionador', 'furadeira', 'pneu'
]

# 4. BELEZA & PERFUMARIA - Forbidden terms (NEVER allow tools, auto parts, tech hardware, appliances)
BELEZA_FORBIDDEN = [
    'furadeira', 'parafusadeira', 'martelete', 'pneu', 'oleo motor', 'bateria de carro',
    'smartphone', 'iphone', 'notebook', 'placa de video', 'mouse gamer', 'teclado mecanico',
    'monitor gamer', 'ps5', 'xbox', 'geladeira', 'fogao', 'sofa', 'colchao', 'racao',
    'furadeira', 'esmerilhadeira', 'cerveja', 'whisky', 'vinho'
]

# 5. MERCADO & BEBIDAS - Forbidden terms (NEVER allow clothing, tech hardware, tools, furniture, gym equipment)
MERCADO_FORBIDDEN = [
    # Roupas e Calçados
    'vestido', 'saia', 'cueca', 'calcinha', 'sutia', 'calca jeans', 'bermuda jeans',
    'tenis casual', 'sapato social', 'chinelo slide', 'bolsa feminina', 'carteira couro',
    # Informática & Eletrônicos
    'notebook', 'smartphone', 'iphone', 'placa de video', 'smart tv', 'teclado gamer',
    'monitor 144hz', 'mousepad',
    # Ferramentas & Casa Pesada
    'furadeira', 'parafusadeira', 'esmerilhadeira', 'sofa', 'fogao',
    # Aparelhos de Academia & Equipamentos Esportivos (NUNCA em Mercado)
    'bicicleta ergometrica', 'bicicleta ergométrica', 'spinning', 'velocron', 'esteira ergometrica',
    'esteira ergométrica', 'esteira eletrica', 'esteira elétrica', 'halteres', 'anilha', 'kettlebell',
    'banco de supino', 'estacao de musculacao', 'estação de musculação', 'barra fixa', 'patins',
    'skate', 'mountain bike', 'bola de futebol', 'bola de basquete', 'raquete de tenis', 'beach tennis'
]

# 6. PET SHOP - STRICT REQUIREMENT: Must contain an animal / pet term
PET_POSITIVE_KEYWORDS = [
    'pet', 'pets', 'cao', 'cão', 'caes', 'cães', 'cachorro', 'cachorros', 'cadela',
    'filhote', 'gato', 'gatos', 'gata', 'felino', 'felinos', 'racao', 'ração', 'antipulgas',
    'bravecto', 'simparic', 'nexgard', 'arranhador', 'caminha pet', 'cama pet',
    'cama para cachorro', 'tapete higienico', 'tapete higiênico', 'areia gato', 'areia para gato',
    'areia higienica', 'pipicat', 'churu', 'aquario', 'aquário', 'coleira', 'peitoral pet',
    'guia cachorro', 'focinheira', 'comedouro pet', 'bebedouro pet', 'fonte pet', 'petisco',
    'shampoo pet', 'granulado sanitario', 'whiskas', 'pedigree', 'royal canin', 'premier pet',
    'golden especial', 'quatree', 'brinquedo para cachorro', 'brinquedo pet', 'brinquedo para gato'
]

# 7. BEBÊS & BRINQUEDOS - Forbidden terms (NEVER allow alcohol, adult supplements, adult lingerie, auto/tools)
BEBES_FORBIDDEN = [
    'cerveja', 'vinho', 'whisky', 'vodka', 'gin', 'cachaca', 'licor', 'whey', 'creatina',
    'pre-treino', 'lingerie', 'sutia', 'calcinha adulto', 'cueca boxer', 'pneu', 'oleo motor',
    'furadeira', 'esmerilhadeira'
]

# 8. FERRAMENTAS & AUTOMOTIVO - Forbidden terms (NEVER allow clothing, makeup, diapers, groceries)
AUTO_FORBIDDEN = [
    'vestido', 'saia', 'salto alto', 'lingerie', 'biquini', 'batom', 'esmalte', 'rimel',
    'fralda descartavel', 'mamadeira', 'chupeta', 'whey', 'creatina', 'azeite', 'vinho', 'cerveja'
]


def validate_deal_for_whatsapp_group(group_id: str, title: str, category: str = "") -> Tuple[bool, str]:
    """
    Validates whether a deal is safe and appropriate to post to the given WhatsApp group.
    
    Args:
        group_id: The target WhatsApp JID (e.g. '120363430459431315@g.us')
        title: The product title
        category: The category inferred by parser.py
        
    Returns:
        Tuple[bool, str]: (is_allowed, reason)
    """
    if not group_id or not title:
        return False, "Missing group_id or title"

    t_norm = _strip_accents(title)

    # 1. MODA Group Validation
    if group_id == GROUP_MODA:
        forbidden_match = _match_word(MODA_FORBIDDEN, t_norm)
        if forbidden_match:
            return False, f"Moda Group BLOCKED: Title contains forbidden term '{forbidden_match}'"
        return True, "Moda OK"

    # 2. CASA & DECORAÇÃO Group Validation
    if group_id == GROUP_CASA:
        forbidden_match = _match_word(CASA_FORBIDDEN, t_norm)
        if forbidden_match:
            return False, f"Casa Group BLOCKED: Title contains forbidden term '{forbidden_match}'"
        return True, "Casa OK"

    # 3. TECNOLOGIA & GAMES Group Validation
    if group_id == GROUP_TECH:
        forbidden_match = _match_word(TECH_FORBIDDEN, t_norm)
        if forbidden_match:
            return False, f"Tech Group BLOCKED: Title contains forbidden term '{forbidden_match}'"
        return True, "Tech OK"

    # 4. BELEZA & PERFUMARIA Group Validation
    if group_id == GROUP_BELEZA:
        forbidden_match = _match_word(BELEZA_FORBIDDEN, t_norm)
        if forbidden_match:
            return False, f"Beleza Group BLOCKED: Title contains forbidden term '{forbidden_match}'"
        return True, "Beleza OK"

    # 5. MERCADO & BEBIDAS Group Validation
    if group_id == GROUP_MERCADO:
        forbidden_match = _match_word(MERCADO_FORBIDDEN, t_norm)
        if forbidden_match:
            return False, f"Mercado Group BLOCKED: Title contains forbidden term '{forbidden_match}'"
        return True, "Mercado OK"

    # 6. PET SHOP Group Validation (STRICT POSITIVE SIGNAL REQUIRED)
    if group_id == GROUP_PETS:
        pet_signal = _match_word(PET_POSITIVE_KEYWORDS, t_norm)
        if not pet_signal:
            return False, "Pet Shop Group BLOCKED: No explicit pet keyword found in title"
        return True, f"Pet OK (Matched: '{pet_signal}')"

    # 7. BEBÊS & BRINQUEDOS Group Validation
    if group_id == GROUP_BEBES:
        forbidden_match = _match_word(BEBES_FORBIDDEN, t_norm)
        if forbidden_match:
            return False, f"Bebês Group BLOCKED: Title contains forbidden term '{forbidden_match}'"
        return True, "Bebês OK"

    # 8. FERRAMENTAS & AUTOMOTIVO Group Validation
    if group_id == GROUP_AUTO:
        forbidden_match = _match_word(AUTO_FORBIDDEN, t_norm)
        if forbidden_match:
            return False, f"Auto Group BLOCKED: Title contains forbidden term '{forbidden_match}'"
        return True, "Auto OK"

    # Any other unrecognized group passes by default, but logs a notice
    return True, "Default OK"
