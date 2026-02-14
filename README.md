# 🤖 PromoBot MultiMarket - Bot de Ofertas Automatizado

Bot inteligente para monitoramento automático de ofertas no Mercado Livre e Shopee, com processamento via IA e envio para Telegram e WhatsApp.

## ✨ Funcionalidades

- 🔍 **Scraping Automatizado**: Monitora categorias específicas do Mercado Livre e Shopee
- 🤖 **Processamento com IA**: Usa Groq AI para analisar e categorizar ofertas
- 🔗 **Links de Afiliado Oficiais**: 
  - **Mercado Livre**: Gera links usando o Link Builder oficial do ML
  - **Shopee**: Gera links usando o Link Builder oficial da Shopee
- 🎟️ **Sistema de Cupons ML**: Geração automática de cupons de desconto para Mercado Livre
  - Cupons únicos por produto
  - Rastreamento em banco de dados
  - Configuração de desconto por categoria
  - Integração automática com links de afiliado
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

Na primeira vez que o bot gerar um link de afiliado do ML:
1. O Chrome vai abrir automaticamente
2. Faça login na sua conta do Mercado Livre
3. O bot vai salvar os cookies
4. Nas próximas execuções, não precisará fazer login novamente

### Primeira Execução - Login na Shopee

Na primeira vez que o bot gerar um link de afiliado da Shopee:
1. O Chrome vai abrir automaticamente
2. Faça login na sua conta de afiliado da Shopee
3. O bot vai salvar os cookies
4. Nas próximas execuções, não precisará fazer login novamente

### Testar Geração de Links

**Mercado Livre:**
```bash
python test_linkbuilder.py
```

**Shopee:**
```bash
python test_shopee_linkbuilder.py
```

### Configurar Grupos Específicos (Shopee)

Você pode configurar grupos diferentes para produtos da Shopee via Dashboard:

1. Acesse `http://localhost:5000/config.html`
2. Configure em **"🛍️ Grupos Shopee - Telegram"** e **"🛍️ Grupos Shopee - WhatsApp"**
3. Salve as configurações

**Hierarquia de grupos para Shopee:**
- `Shopee_Categoria` (ex: `Shopee_Celulares`) → Grupo específico Shopee
- `Shopee_Default` → Grupo padrão Shopee
- `Categoria` → Grupo geral da categoria
- `default` → Grupo padrão geral

**Exemplo:**
```json
{
  "telegram_groups": {
    "default": "-1001111111111",
    "Celulares": "-1002222222222",
    "Shopee_Default": "-1003333333333",
    "Shopee_Celulares": "-1004444444444"
  }
}
```

Resultado:
- Celular ML → Grupo `-1002222222222`
- Celular Shopee → Grupo `-1004444444444`
- Outros Shopee → Grupo `-1003333333333`


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
│   │   ├── ml_coupon_generator.py  # Gerador de cupons ML
│   │   ├── shopee_linkbuilder.py  # Gerador de links Shopee oficial
│   │   ├── parser.py           # Parser de produtos
│   │   ├── simple_affiliate.py # Gerenciador de afiliados (roteador)
│   │   ├── simple_scraper_selenium.py  # Scraper Selenium
│   │   └── telegram_bot.py     # Bot do Telegram
│   └── utils/
│       ├── helpers.py          # Funções auxiliares
│       └── logger.py           # Sistema de logs
├── api/                        # API REST (Flask)
├── dashboard/                  # Dashboard web
├── .env                        # Variáveis de ambiente
├── groups_config.json          # Configuração de grupos
├── coupon_config.json          # Configuração de cupons
├── ml_linkbuilder_cookies.pkl  # Cookies ML (gerado automaticamente)
├── shopee_linkbuilder_cookies.pkl  # Cookies Shopee (gerado automaticamente)
├── test_linkbuilder.py         # Teste do Link Builder ML
├── test_coupon_generator.py    # Teste do gerador de cupons
├── test_shopee_linkbuilder.py  # Teste do Link Builder Shopee
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

### 🎟️ Sistema de Cupons (Mercado Livre)

O bot pode gerar automaticamente cupons de desconto para produtos do Mercado Livre, aumentando a atratividade das ofertas.

#### Configuração de Cupons

Edite `coupon_config.json` para configurar o sistema de cupons:

```json
{
  "enabled": true,
  "default_discount_percentage": 5,
  "coupon_prefix": "PROMO",
  "max_coupons_per_day": 50,
  "coupon_expiry_days": 30,
  "categories": {
    "Celulares": {
      "discount_percentage": 10,
      "enabled": true
    },
    "Eletrônicos": {
      "discount_percentage": 8,
      "enabled": true
    }
  }
}
```

**Parâmetros:**
- `enabled`: Ativa/desativa o sistema de cupons
- `default_discount_percentage`: Desconto padrão (%)
- `coupon_prefix`: Prefixo dos códigos de cupom
- `max_coupons_per_day`: Limite diário de cupons
- `coupon_expiry_days`: Validade dos cupons em dias
- `categories`: Configuração específica por categoria

#### Como Funciona

1. **Geração Automática**: O bot gera um código único para cada produto (ex: `PROMO_20260214_A3F2`)
2. **Rastreamento**: Cupons são salvos no banco de dados para evitar duplicatas
3. **Integração**: Cupons são automaticamente adicionados aos links de afiliado
4. **Notificação**: Código do cupom é incluído nas mensagens do Telegram/WhatsApp

#### Testar Geração de Cupons

```bash
python test_coupon_generator.py
```

**Exemplo de Mensagem com Cupom:**
```
🔥 OFERTA IMPERDÍVEL 🔥

📦 Smartphone XYZ 128GB

~~R$ 1.999,00~~ ➡️ R$ 1.499,00

🎟️ CUPOM: PROMO_20260214_A3F2
💰 Desconto Extra: 10%

🔗 Clique aqui para comprar
```

> **⚠️ Nota Importante**: Atualmente, a criação de cupons na interface do Mercado Livre requer configuração manual. O sistema gera os códigos únicos e os rastreia no banco de dados, mas você precisará criar os cupons manualmente em: https://www.mercadolivre.com.br/afiliados/coupons#hub

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

1. **Scraping**: O bot acessa as páginas do Mercado Livre e Shopee usando Selenium
2. **Parsing**: Extrai informações dos produtos (título, preço, imagem, etc)
3. **IA**: Processa com Groq AI para categorizar e melhorar descrições
4. **Link de Afiliado**: 
   - **Mercado Livre**: Usa o Link Builder oficial do ML para gerar links rastreáveis
   - **Shopee**: Usa o Link Builder oficial da Shopee para gerar links rastreáveis
5. **Cupons (ML)**: Gera/recupera cupom de desconto único para o produto
6. **Encurtamento**: Encurta o link usando is.gd
7. **Verificação**: Checa no banco de dados se já foi enviado
8. **Envio**: Envia para Telegram e/ou WhatsApp conforme configuração

## 🔐 Segurança

- Nunca compartilhe seu arquivo `.env`
- Os cookies do ML são salvos localmente em `ml_linkbuilder_cookies.pkl`
- Os cookies da Shopee são salvos localmente em `shopee_linkbuilder_cookies.pkl`
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
