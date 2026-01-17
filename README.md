# PromoBot MultiMarket Docker Gold 🤖

Automação Python Dockerizada para monitorar ofertas da Shopee e Mercado Livre. Inclui evasão de detecção (Stealth), gestão de sessão (Cookies), IA (Gemini), Banco de Dados (Deduplicação) e Modo Debug.

## 🚀 Características

- **🐳 Dockerizado**: Fácil deploy e isolamento completo
- **🕵️ Stealth Mode**: Evasão avançada de detecção de bots
- **🤖 IA Integrada**: Google Gemini para análise inteligente de ofertas
- **💾 Deduplicação**: SQLite com Peewee ORM para evitar ofertas repetidas
- **🔐 Gestão de Sessão**: Cookies persistentes para manter login
- **📱 Notificações Telegram**: Envio automático de ofertas
- **🐛 Modo Debug**: Teste sem enviar mensagens reais

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Chave da API do Google Gemini
- Bot do Telegram configurado (opcional para produção)

## ⚙️ Configuração

1. **Clone o repositório**
```bash
git clone <seu-repo>
cd auto-post-ofertas
```

2. **Configure as variáveis de ambiente**

Edite o arquivo `.env`:

```env
# Modo Debug (True = apenas loga, False = envia para Telegram)
DEBUG_MODE=True

# Google Gemini API
GOOGLE_API_KEY=sua_chave_aqui

# Telegram (necessário apenas em produção)
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# Credenciais Shopee (para geração de links de afiliado)
SHOPEE_LOGIN=seu_email@example.com
SHOPEE_PASS=sua_senha
```

3. **Obtenha sua chave do Google Gemini**
   - Acesse: https://makersuite.google.com/app/apikey
   - Crie uma nova chave API
   - Cole no `.env`

4. **Configure o Bot do Telegram** (opcional, apenas para produção)
   - Fale com [@BotFather](https://t.me/botfather)
   - Crie um novo bot com `/newbot`
   - Copie o token
   - Para obter o Chat ID, envie uma mensagem para seu bot e acesse:
     `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`

## 🐳 Executando com Docker

### Build e Start
```bash
docker-compose up --build
```

### Executar em background
```bash
docker-compose up -d
```

### Ver logs
```bash
docker-compose logs -f
```

### Parar
```bash
docker-compose down
```

## 💻 Executando Localmente (sem Docker)

1. **Instale as dependências**
```bash
pip install -r requirements.txt
```

2. **Instale o Chrome/Chromium**
   - Windows: Baixe o Chrome
   - Linux: `sudo apt-get install chromium chromium-driver`

3. **Execute**
```bash
python src/main.py
```

## 📁 Estrutura do Projeto

```
auto-post-ofertas/
├── src/
│   ├── browser/          # Setup do Selenium com Stealth
│   ├── database/         # Models Peewee (SQLite)
│   ├── services/         # IA, Links, Telegram
│   ├── utils/            # Logger, Session Manager
│   └── main.py           # Orquestrador principal
├── data/                 # Banco de dados e cookies (criado automaticamente)
├── logs/                 # Logs rotativos (criado automaticamente)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

## 🔧 Personalização

### Alterar URLs Monitoradas

Edite `src/main.py`, função `run_job()`:

```python
urls_to_monitor = [
    "https://shopee.com.br/flash_sale",
    "https://www.mercadolivre.com.br/ofertas",
    "https://sua-url-customizada.com",
]
```

### Alterar Frequência de Execução

Edite `src/main.py`, função `main()`:

```python
# Executar a cada 30 minutos
schedule.every(30).minutes.do(run_job)

# Executar a cada 2 horas
schedule.every(2).hours.do(run_job)

# Executar diariamente às 10:00
schedule.every().day.at("10:00").do(run_job)
```

## 🐛 Debug e Troubleshooting

### Modo Debug
Com `DEBUG_MODE=True`, as ofertas são apenas logadas, não enviadas ao Telegram.

### Ver logs detalhados
```bash
tail -f logs/bot.log
```

### Limpar banco de dados
```bash
rm data/deals.db
```

### Limpar cookies salvos
```bash
rm data/cookies.pkl
```

## 🛡️ Recursos de Stealth

O bot utiliza várias técnicas para evitar detecção:

1. **Headless moderno** (`--headless=new`)
2. **Flags de automação desabilitadas**
3. **User-Agent realista e rotativo**
4. **CDP Commands** para mascarar WebDriver
5. **Cookies persistentes** para simular usuário real

## 📊 Banco de Dados

O SQLite armazena:
- `external_id`: ID único da oferta (evita duplicatas)
- `title`: Título do produto
- `price`: Preço atual
- `original_url`: URL original
- `affiliate_url`: URL de afiliado gerada
- `sent_at`: Data/hora do envio

## 🤝 Contribuindo

Sinta-se à vontade para abrir issues ou pull requests!

## 📝 Licença

MIT License - use como quiser!

## 👨‍💻 Autor

**Thiago** - Senior Developer

---

**Nota**: Este projeto é para fins educacionais. Respeite os Termos de Serviço das plataformas que você está monitorando.
