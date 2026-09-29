"""
AI Semantic Classifier using Groq API.
Permanently eliminates rule-based keyword chasing by understanding the true semantics of e-commerce products.
"""

import os
import functools
from dotenv import load_dotenv
from ..utils.logger import logger

load_dotenv()

# Canonical 8 WhatsApp Group Categories + Outros
VALID_CATEGORIES = {
    'Tech': 'Tech',
    'Casa': 'Casa',
    'Beleza': 'Beleza',
    'Mercado': 'Mercado',
    'Moda': 'Moda',
    'Pets': 'Pets',
    'Bebes': 'Bebês',
    'Bebês': 'Bebês',
    'Ferramentas': 'Ferramentas',
    'Outros': 'Outros'
}

PROMPT_TEMPLATE = """Voce e um classificador semantico de produtos de e-commerce brasileiro para 8 grupos especializados do WhatsApp:
- Tech: Celulares, notebooks, informatica, hardware, fones, smartwatch, tvs, consoles, videogames, cabos, eletronicos.
- Casa: Eletrodomesticos (air fryer, cafeteira, liquidificador, geladeira), panelas, moveis, decoracao, cama, mesa, banho, limpeza da casa.
- Beleza: Perfumes, maquiagem, cosmeticos, cuidados com cabelo e pele, skincare, barbeadores.
- Mercado: Bebidas (alcoolicas e nao alcoolicas), alimentos, azeites, cafes, suplementos nutricionais e vitaminas (Whey, Creatina, Omega 3, BCAA).
- Moda: Roupas adultas, calcados adultos, tenis adultos, bolsas, carteiras, relogios comuns, oculos de sol.
- Pets: Racoes, petiscos, brinquedos e medicamentos para caes, gatos e animais domesticos.
- Bebes: Roupas de bebe/infantil (vestidos de bebe, bodies, macacoes), fraldas, brinquedos infantis, bonecas, carrinhos de bebe, itens de maternidade.
- Ferramentas: Ferramentas eletricas e manuais, construcao, autopecas, pneus, acessorios para carros e motos.
- Outros: Produtos que NAO pertencem a nenhum dos 8 nichos acima (ex: bicicletas ergometricas, equipamentos pesados de academia, instrumentos musicais, livros, etc).

Responda APENAS o nome exato de UMA categoria: [Tech, Casa, Beleza, Mercado, Moda, Pets, Bebes, Ferramentas, Outros].

Produto: {title}
Categoria:"""

_groq_client = None

def get_client():
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        return None
    try:
        from groq import Groq
        _groq_client = Groq(api_key=api_key)
        return _groq_client
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None

@functools.lru_cache(maxsize=2000)
def classify_with_ai(title: str) -> str:
    """
    Classifies a product title into one of the 8 canonical categories using Groq LLM.
    Results are cached in memory for zero latency on duplicate queries.
    """
    client = get_client()
    if not client:
        return ""

    try:
        prompt = PROMPT_TEMPLATE.format(title=title.strip())
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        raw_cat = response.choices[0].message.content.strip().replace('.', '').strip()
        # Find match in valid categories
        for key, canonical in VALID_CATEGORIES.items():
            if key.lower() == raw_cat.lower():
                return canonical
        logger.warning(f"AI returned unexpected category: '{raw_cat}' for '{title}'")
        return ""
    except Exception as e:
        logger.error(f"Groq AI classification error for '{title}': {e}")
        return ""

def classify_deal(title: str, fallback_category: str = "") -> str:
    """
    Primary categorization interface.
    Uses AI semantic comprehension first, with seamless fallback to regex rules.
    """
    if not title:
        return fallback_category or "Outros"

    ai_result = classify_with_ai(title)
    if ai_result:
        logger.info(f"[AI Classifier] '{title[:50]}...' -> [{ai_result}]")
        return ai_result

    # Fallback to local rule engine if AI is unavailable
    logger.debug(f"Using fallback category for '{title[:50]}...': {fallback_category}")
    return fallback_category or "Outros"
