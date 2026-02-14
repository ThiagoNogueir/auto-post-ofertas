"""
Exibe QR Code WhatsApp no terminal
"""
import os
import requests
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8070')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')
EVOLUTION_INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME', 'promobot')

def display_qr_in_terminal():
    """Exibe QR Code no terminal usando caracteres ASCII"""
    try:
        # Obter QR Code da API
        url = f"{EVOLUTION_API_URL}/instance/connect/{EVOLUTION_INSTANCE_NAME}"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print("🔄 Obtendo QR Code...\n")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extrair base64
            qr_base64 = data.get('base64') or data.get('code')
            
            if not qr_base64:
                if 'qrcode' in data:
                    qr_data = data['qrcode']
                    if isinstance(qr_data, dict):
                        qr_base64 = qr_data.get('base64') or qr_data.get('code')
                    else:
                        qr_base64 = qr_data
            
            if qr_base64:
                # Remover prefixo se existir
                if 'base64,' in qr_base64:
                    qr_base64 = qr_base64.split('base64,')[1]
                
                # Decodificar
                qr_bytes = base64.b64decode(qr_base64)
                img = Image.open(BytesIO(qr_bytes))
                
                # Converter para preto e branco
                img = img.convert('L')
                
                # Redimensionar para caber no terminal (50x50 caracteres)
                img = img.resize((50, 50))
                
                # Converter para ASCII
                print("="*60)
                print("📱 QR CODE WHATSAPP - ESCANEIE COM SEU CELULAR")
                print("="*60)
                print()
                
                # Usar blocos Unicode para melhor visualização (SEM ESPAÇOS)
                for y in range(0, img.height, 2):
                    line = ""
                    for x in range(img.width):
                        # Pegar 2 pixels verticais
                        pixel_top = img.getpixel((x, y))
                        pixel_bottom = img.getpixel((x, min(y + 1, img.height - 1)))
                        
                        # Escolher caractere baseado nos pixels (SEM ESPAÇOS EXTRAS)
                        if pixel_top < 128 and pixel_bottom < 128:
                            line += "█"  # Ambos pretos
                        elif pixel_top < 128:
                            line += "▀"  # Top preto
                        elif pixel_bottom < 128:
                            line += "▄"  # Bottom preto
                        else:
                            line += " "  # Ambos brancos
                    
                    print(line)
                
                print()
                print("="*60)
                print("📱 INSTRUÇÕES:")
                print("1. Abra WhatsApp no celular")
                print("2. Vá em Configurações ⚙️")
                print("3. Toque em 'Aparelhos conectados'")
                print("4. Toque em 'Conectar um aparelho'")
                print("5. Escaneie o QR Code acima ☝️")
                print("="*60)
                
                # Também salvar como arquivo
                filename = "qrcode_whatsapp.png"
                with open(filename, 'wb') as f:
                    f.write(qr_bytes)
                print(f"\n💾 QR Code também salvo em: {filename}")
                
                return True
            else:
                print("❌ QR Code não encontrado na resposta")
                return False
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" * 2)  # Espaço no topo
    display_qr_in_terminal()
    print("\n" * 2)  # Espaço no final
