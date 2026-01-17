# 🚀 Guia Rápido de Início

## Configuração Inicial (5 minutos)

### 1. Configure a API do Google Gemini
```bash
# Acesse: https://makersuite.google.com/app/apikey
# Copie sua chave e cole no .env
```

### 2. Edite o arquivo .env
```bash
# Abra o arquivo .env e configure:
GOOGLE_API_KEY=SUA_CHAVE_AQUI
DEBUG_MODE=True  # Mantenha True para testar
```

### 3. Teste a instalação (Opcional - apenas local)
```bash
pip install -r requirements.txt
python test_installation.py
```

### 4. Execute com Docker
```bash
docker-compose up --build
```

## ✅ Verificação

Você deve ver logs como:
```
PromoBot MultiMarket Docker Gold - Starting...
Initializing database...
Running in DEBUG MODE - deals will not be sent to Telegram
Running initial job...
```

## 🎯 Próximos Passos

### Para Produção:

1. **Configure o Telegram Bot**
   - Fale com @BotFather no Telegram
   - Crie um bot com `/newbot`
   - Copie o token para `.env`

2. **Obtenha o Chat ID**
   - Envie uma mensagem para seu bot
   - Acesse: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Copie o `chat.id` para `.env`

3. **Desative o Debug Mode**
   ```env
   DEBUG_MODE=False
   ```

4. **Reinicie o bot**
   ```bash
   docker-compose restart
   ```

## 🔧 Personalização

### Alterar URLs Monitoradas
Edite `src/main.py`, linha ~100:
```python
urls_to_monitor = [
    "https://shopee.com.br/flash_sale",
    "https://www.mercadolivre.com.br/ofertas",
]
```

### Alterar Frequência
Edite `src/main.py`, linha ~150:
```python
schedule.every(1).hours.do(run_job)  # A cada 1 hora
```

## 📊 Monitoramento

### Ver logs em tempo real
```bash
docker-compose logs -f
```

### Ver banco de dados
```bash
# Instale sqlite3
sqlite3 data/deals.db "SELECT * FROM deals;"
```

## 🐛 Problemas Comuns

### "GOOGLE_API_KEY not configured"
- Verifique se você configurou a chave no `.env`
- A chave não pode ser "sua_chave"

### "Chrome not found"
- No Docker: já está incluído
- Local: instale o Chrome/Chromium

### "No deals found"
- Normal! Nem sempre há ofertas
- Teste com URLs diferentes
- Verifique os logs para mais detalhes

## 📚 Documentação Completa
Veja `README.md` para documentação detalhada.

---
**Dica**: Mantenha `DEBUG_MODE=True` até ter certeza que tudo está funcionando!
