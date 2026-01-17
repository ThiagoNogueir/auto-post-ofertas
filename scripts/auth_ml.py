
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

APP_ID = os.getenv('ML_APP_ID')
REDIRECT_URI = os.getenv('ML_REDIRECT_URI')

if not APP_ID:
    print("ERRO: ML_APP_ID não encontrado no .env")
    exit(1)

auth_url = f"https://auth.mercadolivre.com.br/authorization?response_type=code&client_id={APP_ID}&redirect_uri={REDIRECT_URI}"

print("\n=== AUTENTICAÇÃO MERCADO LIVRE ===")
print("1. Copie e acesse a URL abaixo no seu navegador:")
print(f"\n{auth_url}\n")
print("2. Faça login e autorize o aplicativo.")
print("3. Você será redirecionado para o Google.")
print("4. Copie o código que aparece na URL do Google após 'code='")
print("   Exemplo: https://www.google.com/?code=TB-1234...")
print("   O código é a parte: TG-1234...")
print("==================================\n")
