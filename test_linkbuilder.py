"""
Script de teste para geração de links usando ML Link Builder
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from src.services.ml_linkbuilder import generate_link_with_linkbuilder

def test_linkbuilder():
    print("=" * 60)
    print("TESTE DE GERAÇÃO DE LINK - ML LINK BUILDER")
    print("(Usando ferramenta oficial do Mercado Livre)")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANTE:")
    print("1. O Chrome vai abrir")
    print("2. Você precisará fazer LOGIN no ML se solicitado")
    print("3. O script vai usar o Link Builder automaticamente")
    print()
    
    # Solicitar URL do usuário
    product_url = input("Cole o link do produto aqui: ").strip()
    
    if not product_url:
        print("❌ URL vazia!")
        return
    
    print()
    print("🔄 Gerando link de afiliado com Link Builder...")
    print("   (Aguarde, pode demorar até 60s se precisar fazer login)")
    print()
    
    # Gerar link de afiliado
    affiliate_link = generate_link_with_linkbuilder(product_url)
    
    print()
    print("=" * 60)
    print("RESULTADO:")
    print("=" * 60)
    print()
    print("📦 URL Original:")
    print(product_url)
    print()
    print("🔗 Link de Afiliado Gerado:")
    print(affiliate_link)
    print()
    print("=" * 60)
    
    if affiliate_link != product_url:
        print("✅ Link de afiliado gerado com sucesso!")
        print()
        if 'reco_' in affiliate_link or 'tracking_id' in affiliate_link:
            print("✅ Link contém parâmetros de rastreamento!")
    else:
        print("⚠️ Não foi possível gerar o link")
    
    print()
    print("Teste este link e veja se rastreia comissão!")
    print()

if __name__ == "__main__":
    test_linkbuilder()
