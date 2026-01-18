# 🚀 Integração Evolution API + WhatsApp - Guia Completo

## 📋 Resumo da Implementação

Foi adicionada integração completa com Evolution API para envio de ofertas via WhatsApp, com interface de configuração no dashboard.

## 🎯 Funcionalidades Implementadas

### 1. Backend
- ✅ Serviço Evolution API (`src/services/evolution_api.py`)
  - Envio de mensagens de texto
  - Envio de imagens com caption
  - Formatação automática de ofertas
  
- ✅ Endpoints na API (`api/app.py`)
  - `GET /groups-config` - Buscar configurações de grupos
  - `POST /groups-config` - Salvar configurações de grupos
  
- ✅ Arquivo de configuração (`groups_config.json`)
  - Mapeamento de categorias para grupos Telegram
  - Mapeamento de categorias para grupos WhatsApp
  - Controle de ativação por plataforma

### 2. Frontend
- ✅ Página de Configuração (`dashboard/config.html`)
  - Interface amigável para configurar grupos
  - Campos para Telegram e WhatsApp separados
  - Botão de teste para cada grupo WhatsApp
  - Configurações gerais (ativar/desativar plataformas)
  
- ✅ Link no Dashboard Principal
  - Botão "⚙️ Grupos" no cabeçalho
  - Acesso rápido às configurações

## ⚙️ Configuração

### Passo 1: Configurar Evolution API

Adicione as seguintes variáveis no arquivo `.env`:

```env
# Evolution API (WhatsApp)
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua_api_key_aqui
EVOLUTION_INSTANCE_NAME=promobot
```

**Como obter:**
1. Instale a Evolution API (https://github.com/EvolutionAPI/evolution-api)
2. Crie uma instância chamada "promobot"
3. Copie a API Key gerada
4. Configure a URL onde a Evolution API está rodando

### Passo 2: Obter IDs dos Grupos WhatsApp

**Formato do ID:** `5511999999999-1234567890@g.us`

**Como obter:**
1. Envie uma mensagem para o grupo
2. Use o endpoint da Evolution API: `/chat/findMessages/{instance}`
3. Ou use ferramentas como WA-JS Inspector

### Passo 3: Configurar Grupos no Dashboard

1. Acesse `http://localhost:8000`
2. Clique no botão "⚙️ Grupos" no cabeçalho
3. Configure:
   - ✅ Ative "Enviar para WhatsApp"
   - ✅ Preencha os IDs dos grupos
   - ✅ Clique em "Testar" para verificar conexão
   - ✅ Salve as configurações

## 📱 Mapeamento de Categorias

Você pode configurar grupos diferentes para cada categoria:

- **Grupo Padrão**: Recebe todas as ofertas
- **Celulares**: Apenas ofertas de celulares
- **Eletrônicos**: Apenas ofertas de eletrônicos
- **Informática**: Apenas ofertas de informática
- **Casa**: Apenas ofertas de casa

**Funciona para Telegram e WhatsApp separadamente!**

## 🧪 Testando

1. Configure um grupo no dashboard
2. Clique no botão "Testar" ao lado do campo
3. Verifique se a mensagem chegou no grupo
4. Se funcionou, salve as configurações

## 📝 Formato das Mensagens

As mensagens enviadas para WhatsApp seguem este formato:

```
🔥 *OFERTA IMPERDÍVEL!* 🔥

📦 Nome do Produto

💰 *De:* ~R$ 199,90~
💵 *Por:* R$ 149,90
🏷️ *Desconto:* 25% OFF

🛒 Link: https://...

⚡ Corre que é por tempo limitado!
```

## 🔧 Troubleshooting

### Mensagem não chega no WhatsApp
- ✅ Verifique se a Evolution API está rodando
- ✅ Confirme a API Key no `.env`
- ✅ Teste a conexão usando o botão "Testar"
- ✅ Verifique se o ID do grupo está correto

### Erro "Evolution API not configured"
- ✅ Adicione as variáveis no `.env`
- ✅ Reinicie a API: `taskkill /F /IM python.exe` e execute `iniciar_bot.bat`

### Grupo não recebe mensagens
- ✅ Verifique se o bot está no grupo
- ✅ Confirme que "Enviar para WhatsApp" está ativado
- ✅ Verifique os logs da Evolution API

## 🎨 Próximas Melhorias Sugeridas

- [ ] Adicionar preview de mensagem antes de enviar
- [ ] Histórico de mensagens enviadas
- [ ] Agendamento de envios
- [ ] Templates personalizáveis de mensagem
- [ ] Suporte a múltiplos grupos por categoria

## 📚 Arquivos Criados/Modificados

```
src/services/evolution_api.py          # Novo - Serviço WhatsApp
dashboard/config.html                  # Novo - Página de configuração
dashboard/config.js                    # Novo - Lógica da configuração
groups_config.json                     # Novo - Configurações de grupos
api/app.py                            # Modificado - Novos endpoints
dashboard/index.html                   # Modificado - Link para config
.env.example                          # Modificado - Variáveis Evolution
```

## ✅ Checklist de Implementação

- [x] Serviço Evolution API criado
- [x] Endpoints de configuração implementados
- [x] Interface de configuração criada
- [x] Botão de teste implementado
- [x] Link no dashboard adicionado
- [x] Documentação completa
- [x] Variáveis de ambiente documentadas

---

**Pronto para usar!** 🎉

Agora você pode configurar grupos diferentes para cada categoria e enviar ofertas tanto para Telegram quanto para WhatsApp automaticamente!
