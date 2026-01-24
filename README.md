# 🤖 PromoBot MultiMarket - Bot de Ofertas Automatizado

Bot inteligente para monitoramento automático de ofertas no Mercado Livre e Shopee, com processamento via IA e envio para Telegram e WhatsApp.

## ✨ Funcionalidades

- 🔍 **Scraping Automatizado**: Monitora categorias específicas do Mercado Livre
- 🤖 **Processamento com IA**: Usa Groq AI para analisar e categorizar ofertas
- 🔗 **Links de Afiliado Oficiais**: Gera links usando o Link Builder do Mercado Livre
- 📱 **Telegram**: Envio automático para grupos/canais configuráveis
- 💬 **WhatsApp**: Integração via Evolution API
- 🔄 **Encurtador de Links**: URLs compactas via is.gd
- 🗄️ **Banco de Dados**: SQLite para evitar duplicatas
- 📊 **Dashboard Web**: Interface para gerenciar configurações

## 🚀 Instalação

### 1. Requisitos
- Python 3.8+
- Google Chrome instalado
- Node.js (para Evolution API - WhatsApp)

### 2. Clone o repositório
```bash
git clone https://github.com/seu-usuario/auto-post-ofertas.git
cd auto-post-ofertas
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e preencha:

```env
# Debug Mode
DEBUG_MODE=False

# Groq AI
GROQ_API_KEY=sua_chave_groq

# Telegram
TELEGRAM_BOT_TOKEN=seu_token_bot
TELEGRAM_CHAT_ID=seu_chat_id

# Mercado Livre Afiliados
ML_AFFILIATE_ID=seu_id_afiliado

# Evolution API (WhatsApp)
EVOLUTION_API_URL=http://localhost:8070
EVOLUTION_API_KEY=sua_chave_api
EVOLUTION_INSTANCE_NAME=promobot
```

### 5. Configure os grupos de envio

Edite `groups_config.json` para definir para quais grupos cada categoria será enviada:

```json
{
  "telegram_groups": {
    "default": "-1003499671429",
    "Celulares": "-1003499671429",
    "Eletrônicos": "-1003499671429"
  },
  "whatsapp_groups": {
    "default": "120363XXXXX@g.us",
    "Celulares": "120363XXXXX@g.us"
  }
}
```

## 🎯 Como Usar

### Iniciar o Bot

```bash
# Windows
.\iniciar_bot.bat

# Linux/Mac
python -m src.main
```

### Primeira Execução - Login no Mercado Livre

Na primeira vez que o bot gerar um link de afiliado:
1. O Chrome vai abrir automaticamente
2. Faça login na sua conta do Mercado Livre
3. O bot vai salvar os cookies
4. Nas próximas execuções, não precisará fazer login novamente

### Testar Geração de Links

```bash
python test_linkbuilder.py
```

## 📁 Estrutura do Projeto

```
auto-post-ofertas/
├── src/
│   ├── main.py                 # Orquestrador principal
│   ├── models/                 # Modelos do banco de dados
│   ├── services/
│   │   ├── ai_processor.py     # Processamento com Groq AI
│   │   ├── evolution_api.py    # WhatsApp via Evolution API
│   │   ├── ml_linkbuilder.py   # Gerador de links ML oficial
│   │   ├── parser.py           # Parser de produtos
│   │   ├── simple_affiliate.py # Gerenciador de afiliados
│   │   ├── simple_scraper_selenium.py  # Scraper Selenium
│   │   └── telegram_bot.py     # Bot do Telegram
│   └── utils/
│       ├── helpers.py          # Funções auxiliares
│       └── logger.py           # Sistema de logs
├── api/                        # API REST (Flask)
├── dashboard/                  # Dashboard web
├── .env                        # Variáveis de ambiente
├── groups_config.json          # Configuração de grupos
├── ml_linkbuilder_cookies.pkl  # Cookies salvos (gerado automaticamente)
└── requirements.txt            # Dependências Python
```

## 🔧 Configuração Avançada

### Categorias Monitoradas

As URLs monitoradas estão em `src/main.py`:

```python
urls_to_monitor = [
    "https://lista.mercadolivre.com.br/celulares-telefones/_Orden_sold_quantity",
    "https://lista.mercadolivre.com.br/computadores/_Orden_sold_quantity",
    "https://lista.mercadolivre.com.br/saude/suplementos-alimentares/_Orden_sold_quantity",
    "https://lista.mercadolivre.com.br/animais/_Orden_sold_quantity",
    "https://lista.mercadolivre.com.br/calcados-roupas-bolsas/_Orden_sold_quantity"
]
```

### Intervalo de Execução

Por padrão, o bot executa a cada 30 minutos. Para alterar, edite em `src/main.py`:

```python
schedule.every(30).minutes.do(run_job)
```

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **Selenium** - Web scraping
- **Groq AI** - Processamento de linguagem natural
- **SQLite** - Banco de dados
- **Flask** - API REST
- **Telegram Bot API** - Notificações
- **Evolution API** - WhatsApp
- **BeautifulSoup4** - Parsing HTML

## 📝 Como Funciona

1. **Scraping**: O bot acessa as páginas do Mercado Livre usando Selenium
2. **Parsing**: Extrai informações dos produtos (título, preço, imagem, etc)
3. **IA**: Processa com Groq AI para categorizar e melhorar descrições
4. **Link de Afiliado**: Usa o Link Builder oficial do ML para gerar links rastreáveis
5. **Encurtamento**: Encurta o link usando is.gd
6. **Verificação**: Checa no banco de dados se já foi enviado
7. **Envio**: Envia para Telegram e/WhatsApp conforme configuração

## 🔐 Segurança

- Nunca compartilhe seu arquivo `.env`
- Os cookies do ML são salvos localmente em `ml_linkbuilder_cookies.pkl`
- Mantenha suas chaves de API seguras

## 📊 Dashboard

Acesse o dashboard em `http://localhost:5000` após iniciar a API:

```bash
cd api
python app.py
```

## 🐛 Solução de Problemas

### Chrome não abre
- Verifique se o Google Chrome está instalado
- Instale o ChromeDriver compatível com sua versão do Chrome

### Links de afiliado não rastreiam
- Certifique-se de estar logado no Mercado Livre
- Verifique se seu `ML_AFFILIATE_ID` está correto no `.env`

### Erro ao enviar para WhatsApp
- Verifique se a Evolution API está rodando
- Confirme as credenciais no `.env`

## 📄 Licença

MIT License - Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## 📧 Suporte

Para dúvidas e suporte, abra uma issue no GitHub.

---

**Desenvolvido com ❤️ para automatizar suas ofertas**
