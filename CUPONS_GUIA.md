
# 🎟️ GUIA: Como Criar Cupons no Mercado Livre

## ⚠️ IMPORTANTE: Processo Manual Necessário

O sistema **gera códigos únicos e rastreia cupons**, mas você precisa **criar os cupons manualmente** na plataforma do Mercado Livre.

---

## 📋 Passo a Passo

### 1. Execute o Bot Normalmente

```bash
python -m src.main
```

O bot irá:
- Encontrar ofertas
- Gerar links de afiliado
- **Gerar códigos de cupom** (salvos no banco de dados)
- Mostrar nos logs qual código foi gerado

### 2. Verifique os Logs

Procure por mensagens como:

```
INFO | Generated coupon code: CEL_01
INFO | Coupon CEL_01 saved to database (pending manual creation)
```

### 3. Acesse a Página de Cupons do ML

Abra: https://www.mercadolivre.com.br/afiliados/coupons#hub

### 4. Crie o Cupom Manualmente

1. Clique em **"Gerar código"** ou botão similar
2. **Nome do cupom**: Use EXATAMENTE o código gerado pelo bot (ex: `CEL_01`)
3. **Desconto**: Configure conforme `coupon_config.json`
   - Celulares: 10%
   - Eletrônicos: 8%
   - Outros: 5%
4. **Produtos**: Selecione os produtos aplicáveis
5. **Validade**: Configure conforme necessário (padrão: 30 dias)
6. Clique em **"Criar cupom"**

### 5. Verifique na Lista

O cupom deve aparecer em **"Códigos gerados"** na página do ML.

---

## 📊 Verificar Cupons Gerados pelo Bot

### Opção 1: Logs

```bash
# Ver últimos logs
tail -f logs/promobot.log | grep "coupon"
```

### Opção 2: Banco de Dados

```bash
# Testar e ver cupons
python test_coupon_generator.py
```

### Opção 3: Dashboard (futuro)

Em breve teremos um dashboard para visualizar todos os cupons gerados.

---

## 🎯 Exemplos de Códigos Gerados

Com `friendly_names: true` (recomendado):

- **Celulares**: `CEL_01`, `CEL_02`, `CEL_03`
- **Eletrônicos**: `ELET_01`, `ELET_02`
- **Computadores**: `COMP_01`, `COMP_02`
- **Suplementos**: `SUPLEM_01`
- **Outros**: `PROMO_01`, `PROMO_02`

Códigos **fáceis de lembrar e digitar**! ✅

---

## ⚙️ Configuração

### Ativar Nomes Amigáveis

Edite `coupon_config.json`:

```json
{
  "enabled": true,
  "friendly_names": true,  // ← Códigos simples como CEL_01
  "default_discount_percentage": 5
}
```

### Descontos por Categoria

```json
"categories": {
  "Celulares": {
    "discount_percentage": 10,  // ← 10% de desconto
    "enabled": true
  }
}
```

---

## 🔄 Fluxo Completo

```
1. Bot encontra oferta
   ↓
2. Gera link de afiliado
   ↓
3. Gera código de cupom (ex: CEL_01)
   ↓
4. Salva no banco de dados
   ↓
5. Aplica cupom ao link
   ↓
6. Envia para Telegram com código do cupom
   ↓
7. VOCÊ cria o cupom manualmente no ML
   ↓
8. Clientes usam o cupom e ganham desconto extra!
```

---

## ❓ FAQ

### Por que não cria automaticamente?

A API do Mercado Livre para cupons de afiliados não permite criação programática. Apenas vendedores têm essa funcionalidade via API.

### Posso usar outros nomes?

Sim! Basta criar o cupom no ML com o nome que preferir. O sistema é flexível.

### E se eu esquecer de criar um cupom?

Não tem problema! O link de afiliado continua funcionando normalmente, apenas sem o desconto extra do cupom.

### Como saber quais cupons preciso criar?

Verifique os logs ou rode `python test_coupon_generator.py` para ver os cupons pendentes no banco de dados.

---

## 📞 Suporte

Se tiver dúvidas, verifique:
1. Logs do bot
2. Banco de dados (`data/deals.db` - tabela `coupons`)
3. Página de cupons do ML

---

**Dica**: Crie os cupons em lote! Acesse a página do ML uma vez por dia e crie todos os cupons gerados de uma vez.
