# 🤖 PromoBot MultiMarket - Automação de Ofertas com IA

Bot automatizado para monitorar ofertas da **Shopee** e **Mercado Livre**, processar com **IA (Groq)** e enviar notificações via **Telegram**.

## ✨ Características

- 🤖 **IA Integrada** - Groq AI (gratuito e rápido) para análise de ofertas
- 🐳 **Dockerizado** - Deploy fácil e isolado
- 💾 **Deduplicação** - SQLite + Peewee ORM evita ofertas repetidas
- 📱 **Telegram** - Notificações automáticas
- 🔐 **Stealth Mode** - Navegador com anti-detecção
- 📊 **Dashboard Web** - Estatísticas em tempo real
- 🔗 **Links de Afiliado** - Geração automática para Mercado Livre
- 🐛 **Modo Debug** - Teste sem enviar mensagens

## 🚀 Início Rápido

### 1. Configure a API do Groq (GRATUITA!)

1. Acesse: https://console.groq.com/
2. Crie uma conta (sem cartão de crédito)
3. Gere uma API Key: https://console.groq.com/keys
4. Copie a chave (começa com `gsk_...`)

### 2. Configure o .env

```env
DEBUG_MODE=True
GROQ_API_KEY=gsk_SUA_CHAVE_AQUI
TELEGRAM_BOT_TOKEN=seu_token  # Opcional para testes
TELEGRAM_CHAT_ID=seu_chat_id  # Opcional para testes
```

### 3. Execute com Docker

```bash
docker-compose up --build
```

Pronto! O bot está rodando e encontrando ofertas! 🎉

## 📊 Dashboard Web

### Iniciar o Dashboard

```bash
# Instalar dependências (se não estiver usando Docker)
pip install flask flask-cors

# Iniciar API
python api/app.py
```

Acesse: **http://localhost:8000**

### Recursos do Dashboard

- 📈 Estatísticas em tempo real
- 📋 Lista das últimas 20 ofertas
- ⚙️ Status do bot (Debug, Telegram, IA)
- 🔄 Atualização automática a cada 30s
- 🎨 Design moderno dark mode

## 🔧 Configuração Avançada

### Telegram (Para Produção)

1. Fale com [@BotFather](https://t.me/botfather)
2. Crie um bot: `/newbot`
3. Copie o token
4. Obtenha o Chat ID: `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Atualize o `.env`:
   ```env
   DEBUG_MODE=False
   TELEGRAM_BOT_TOKEN=seu_token_real
   TELEGRAM_CHAT_ID=seu_chat_id_real
   ```

### Links de Afiliado Mercado Livre

Adicione ao `.env`:
```env
ML_ACCESS_TOKEN=seu_token_ml  # Opcional
ML_TAG_ID=SEU_TAG_ID          # Seu ID de afiliado
```

### Personalizar URLs Monitoradas

Edite `src/main.py`, linha ~120:
```python
urls_to_monitor = [
    "https://shopee.com.br/flash_sale",
    "https://www.mercadolivre.com.br/ofertas",
    "https://sua-url-customizada.com",
]
```

### Alterar Frequência

Edite `src/main.py`, linha ~180:
```python
schedule.every(30).minutes.do(run_job)  # A cada 30 min
schedule.every(2).hours.do(run_job)     # A cada 2 horas
```

## 📁 Estrutura do Projeto

```
auto-post-ofertas/
├── src/                    # Código fonte
│   ├── browser/           # Selenium + Stealth
│   ├── database/          # SQLite + Peewee
│   ├── services/          # IA, Links, Telegram, ML Affiliate
│   └── utils/             # Logger, Sessões
├── api/                   # API REST Flask
├── dashboard/             # Dashboard Web
├── data/                  # Banco de dados
├── logs/                  # Logs rotativos
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🛠️ Comandos Úteis

```bash
# Docker
docker-compose up --build        # Build e start
docker-compose up -d             # Background
docker-compose logs -f           # Ver logs
docker-compose down              # Parar

# Local
python src/main.py               # Executar bot
python api/app.py                # Executar API
python test_installation.py     # Testar instalação

# Limpeza
rm data/deals.db                 # Limpar banco
rm data/cookies.pkl              # Limpar cookies
```

## 📊 API Endpoints

### GET `/stats`
Estatísticas gerais
```json
{
  "total_deals": 10,
  "sent_deals": 10,
  "total_savings": 500.50,
  "avg_discount": 35
}
```

### GET `/deals`
Lista de ofertas (últimas 20)
```json
[{
  "id": 1,
  "title": "Produto X",
  "price": 99.90,
  "old_price": 149.90,
  "affiliate_url": "https://...",
  "sent_at": "2026-01-17T01:54:19"
}]
```

### GET `/config`
Status do bot
```json
{
  "debug_mode": true,
  "telegram_configured": false,
  "ai_configured": true,
  "last_run": "2026-01-17T01:54:19"
}
```

## 🎯 Tecnologias

- **Python 3.11**
- **Docker & Docker Compose**
- **Groq AI** (LLaMA 3.3 70B)
- **Selenium WebDriver** (Stealth)
- **SQLite + Peewee ORM**
- **Flask + Flask-CORS**
- **Telegram Bot API**
- **Loguru** (Logging)
- **Schedule** (Agendamento)

## 🐛 Troubleshooting

### "GROQ_API_KEY not configured"
→ Configure a chave no `.env`

### "Chrome not found"
→ Use Docker (já inclui Chrome) ou instale localmente

### "No deals found"
→ Normal! Nem sempre há ofertas. Teste com URLs diferentes

### Dashboard não carrega
→ Verifique se a API está rodando: `python api/app.py`

## 📈 Resultados Reais

O bot já encontrou ofertas como:
- **Relógio Casio G-Shock**: R$ 499 → R$ 299 (40% OFF)
- **Tênis Kappa**: R$ 169 → R$ 99 (41% OFF)
- **Whey Protein**: R$ 104 → R$ 78 (24% OFF)

## 🤝 Contribuindo

Sinta-se à vontade para abrir issues ou pull requests!

## 📝 Licença

MIT License - use como quiser!

## 👨‍💻 Autor

**Thiago Nogueira** - Senior Developer

---

**⚠️ Aviso**: Este projeto é para fins educacionais. Respeite os Termos de Serviço das plataformas que você está monitorando.

**🌟 Dica**: Mantenha `DEBUG_MODE=True` até ter certeza que tudo está funcionando!
