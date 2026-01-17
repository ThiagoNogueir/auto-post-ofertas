
import os
import requests
import time
from ..utils.logger import logger

class MLAuthService:
    def __init__(self):
        self.app_id = os.getenv('ML_APP_ID')
        self.client_secret = os.getenv('ML_CLIENT_SECRET')
        self.refresh_token = os.getenv('ML_REFRESH_TOKEN')
        self.access_token = None
        self.expires_at = 0

    def get_token(self):
        """Retorna um access_token válido, renovando se necessário."""
        if not self.refresh_token:
            logger.warning("ML Refresh Token not found. Cannot auth.")
            return None

        if self.access_token and time.time() < self.expires_at:
            return self.access_token
        
        return self._refresh_access_token()

    def _refresh_access_token(self):
        try:
            url = "https://api.mercadolibre.com/oauth/token"
            payload = {
                'grant_type': 'refresh_token',
                'client_id': self.app_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token
            }
            
            response = requests.post(url, data=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                self.refresh_token = data['refresh_token'] # Atualiza o refresh (rolling refresh)
                self.expires_at = time.time() + data['expires_in'] - 60 # Margem de segurança
                
                # Opcional: Atualizar .env com novo refresh_token para persistência
                self._update_env_file(self.refresh_token)
                
                logger.info("ML Access Token refreshed successfully")
                return self.access_token
            else:
                logger.error(f"Failed to refresh token: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None

    def _update_env_file(self, new_refresh_token):
        # Implementação simplista para atualizar o arquivo .env
        # Em produção, usar banco de dados ou secrets manager é melhor
        try:
            with open('.env', 'r') as f:
                lines = f.readlines()
            
            with open('.env', 'w') as f:
                for line in lines:
                    if line.startswith('ML_REFRESH_TOKEN='):
                        f.write(f"ML_REFRESH_TOKEN={new_refresh_token}\n")
                    else:
                        f.write(line)
        except:
            pass

ml_auth = MLAuthService()
