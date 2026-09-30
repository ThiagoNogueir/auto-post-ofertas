"""
AI Semantic Classifier using Groq API.
Permanently eliminates rule-based keyword chasing by understanding the true semantics of e-commerce products.
"""

import os
import functools
from dotenv import load_dotenv
from ..utils.logger import logger

load_dotenv()

import time

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

PROMPT_TEMPLATE = """Classifique o produto para um dos 8 grupos de ofertas do WhatsApp:
- Tech: celulares, computadores, hardware, monitores, fones, smartwatch, tvs, consoles, videogames, cabos, eletronicos.
- Casa: eletrodomesticos (air fryer, cafeteira, liquidificador), panelas, moveis, decoracao, cama/mesa/banho.
- Beleza: perfumes, maquiagem, cosmeticos, cuidados com cabelo e pele, skincare, barbeadores.
- Mercado: bebidas, alimentos, cafes, suplementos nutricionais (whey, creatina, vitaminas).
- Moda: roupas, calçados, tenis, bolsas, carteiras, oculos de sol (adulto).
- Pets: racao, petiscos, brinquedos e medicamentos para animais.
- Bebes: roupas de bebe/infantil, fraldas, brinquedos infantis, carrinhos, maternidade.
- Ferramentas: ferramentas manuais e eletricas, construcao, autopecas, acessorios carro/moto.
- Outros: nao pertence a nenhum acima (bicicletas ergometricas/academia pesada, instrumentos musicais, livros, etc).

Responda APENAS: Tech, Casa, Beleza, Mercado, Moda, Pets, Bebes, Ferramentas ou Outros.
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

@functools.lru_cache(maxsize=3000)
def classify_with_ai(title: str) -> str:
    """
    Classifies a product title into one of the 8 canonical categories using Groq LLM.
    Results are cached in memory for zero latency on duplicate queries.
    """
    client = get_client()
    if not client:
        return ""

    prompt = PROMPT_TEMPLATE.format(title=title.strip())

    for attempt in range(3):
        try:
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
            err_str = str(e)
            if "429" in err_str or "rate_limit" in err_str.lower():
                wait_time = 3 + attempt * 2
                logger.info(f"Groq TPM limit reached, pausing {wait_time}s before retry (attempt {attempt+1}/3)...")
                time.sleep(wait_time)
                continue
            logger.error(f"Groq AI classification error for '{title}': {e}")
            return ""
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
