# 📡 Documentação das Rotas da API RPA Safra

## 🎯 Visão Geral

API REST para processamento automatizado de CPFs via RPA (Robotic Process Automation) no sistema Safra.

**Base URL:** `http://localhost:8000`

---

## 🔄 Rotas de Processamento

### POST `/processar-cpf`

**Descrição:** Adiciona um CPF à fila de processamento (retorna 202 Accepted imediatamente)

**Tags:** `Processamento`

**Body (JSON):**
```json
{
  "cpf_id": 1,
  "contrato": "123456",
  "nome": "João Silva",
  "cpf": "12345678900",
  "callback_url": "https://seu-sistema.com/webhook/callback"
}
```

**Campos:**
- `cpf_id` *(int, obrigatório)* - ID único do CPF no sistema Laravel
- `contrato` *(string, obrigatório)* - Número do contrato
- `nome` *(string, obrigatório)* - Nome do cliente
- `cpf` *(string, obrigatório)* - CPF a ser processado (11 dígitos)
- `callback_url` *(string, obrigatório)* - URL para enviar o resultado do processamento

**Resposta (202 Accepted):**
```json
{
  "status": "accepted",
  "message": "CPF 12345678900 adicionado à fila de processamento",
  "cpf_id": 1,
  "machine_id": "abc-123-def",
  "timestamp": "2025-12-31 15:30:45"
}
```

**Como usar:**

**CMD:**
```cmd
curl -X POST "http://localhost:8000/processar-cpf" -H "Content-Type: application/json" -d "{\"cpf_id\": 1, \"contrato\": \"123456\", \"nome\": \"Teste\", \"cpf\": \"12345678900\", \"callback_url\": \"http://localhost:8000/test-callback\"}"
```

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/processar-cpf" -Method POST -ContentType "application/json" -Body '{"cpf_id": 1, "contrato": "123456", "nome": "Teste", "cpf": "12345678900", "callback_url": "http://localhost:8000/test-callback"}'
```

**Fluxo:**
1. ✅ API recebe requisição e retorna 202 imediatamente
2. 🔄 Processamento acontece em background
3. 🤖 RPA abre Chrome, faz login, busca CPF, extrai dados
4. 📤 Resultado é enviado para a `callback_url` fornecida

**Resultados Possíveis:**
- ✅ **Proposta processada** - Dados completos extraídos
- ⚠️ **"Nenhum contrato localizado"** - CPF não encontrado no sistema
- ⚠️ **Contrato CANCELADO** - Proposta foi cancelada
- ⚠️ **Contrato NEGADO** - Proposta foi negada
- 🔄 **Dias > 180** - Campo Repasse/Banco preenchido automaticamente

---

## 📊 Rotas de Monitoramento

### GET `/health`

**Descrição:** Health check do serviço (status, uptime, estado)

**Tags:** `Monitoramento`

**Resposta (200 OK):**
```json
{
  "status": "healthy",
  "estado": "OCIOSO_LOGADO",
  "uptime": 3600,
  "cpf_atual": "12345678900",
  "machine_id": "abc-123-def",
  "timestamp": "2025-12-31 15:30:45"
}
```

**Campos:** 
- `status` - Status do serviço (`healthy`)
- `estado` - Estado atual do Chrome:
  - `FECHADO` - Chrome fechado
  - `LOGANDO` - Fazendo login
  - `OCIOSO_LOGADO` - Chrome aberto, aguardando CPF
  - `PROCESSANDO` - Processando CPF
- `uptime` - Tempo em segundos desde que a API iniciou
- `cpf_atual` - CPF sendo processado no momento (ou `null`)
- `machine_id` - ID único desta instância do servidor
- `timestamp` - Data/hora atual

**Como usar:**
```bash
curl http://localhost:8000/health
```

---

### GET `/status`

**Descrição:** Informações detalhadas do servidor (estatísticas completas)

**Tags:** `Monitoramento`

**Resposta (200 OK):**
```json
{
  "machine_id": "abc-123-def",
  "uptime": 3600,
  "estado": "OCIOSO_LOGADO",
  "chrome_aberto": true,
  "cpf_atual": "12345678900",
  "total_processados": 42,
  "total_erros": 3,
  "timestamp": "2025-12-31 15:30:45"
}
```

**Campos adicionais:**
- `chrome_aberto` *(boolean)* - Se o Chrome está aberto
- `total_processados` - Total de CPFs processados desde o início
- `total_erros` - Total de erros encontrados

**Como usar:**
```bash
curl http://localhost:8000/status
```

---

## 🔧 Rotas de Administração

### POST `/restart`

**Descrição:** Reinicia o serviço RPA (fecha Chrome, reseta estados, limpa sessões)

**Tags:** `Administração`

**Resposta (200 OK):**
```json
{
  "status": "success",
  "message": "Serviço RPA reiniciado com sucesso",
  "estado": "FECHADO",
  "chrome_aberto": false,
  "timestamp": "2025-12-31 15:30:45"
}
```

**O que faz:**
1. 🌐 Fecha o Chrome se estiver aberto
2. 🔄 Reseta o estado para `FECHADO`
3. 🧹 Limpa o job atual
4. ✅ Prepara para receber novos CPFs

**Como usar:**

**CMD:**
```cmd
curl -X POST "http://localhost:8000/restart"
```

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/restart" -Method POST
```

**Quando usar:**
- Chrome travou ou ficou em estado inconsistente
- Erros de conexão persistentes
- Necessidade de limpar sessão e começar do zero
- Manutenção preventiva

---

## 🧪 Rotas de Debug/Teste

### GET `/`

**Descrição:** Página inicial da API (informações básicas)

**Tags:** `Root`

**Resposta (200 OK):**
```json
{
  "message": "RPA Safra API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

**Como usar:**
```bash
curl http://localhost:8000/
```

---

### POST `/test-json`

**Descrição:** Endpoint de teste para validar estrutura JSON

**Tags:** `Debug`

**Body:** Qualquer JSON válido

**Resposta (200 OK):**
```json
{
  "status": "ok",
  "message": "JSON recebido com sucesso",
  "data_received": { ... }
}
```

**Como usar:**
```bash
curl -X POST "http://localhost:8000/test-json" -H "Content-Type: application/json" -d '{"teste": "valor"}'
```

---

### POST `/test-callback`

**Descrição:** Simula callback do Laravel (apenas loga os dados recebidos no console)

**Tags:** `Debug`

**Body:** JSON com dados do processamento

**Resposta (200 OK):**
```json
{
  "status": "ok",
  "message": "Callback recebido com sucesso (simulação Laravel)",
  "data_received": true
}
```

**Uso:** Usado para testar processamento localmente sem precisar do Laravel. Os dados recebidos aparecem no console da API com formatação legível.

**Como usar:**
```bash
curl -X POST "http://localhost:8000/processar-cpf" -H "Content-Type: application/json" -d "{\"cpf_id\": 1, \"contrato\": \"123456\", \"nome\": \"Teste\", \"cpf\": \"12345678900\", \"callback_url\": \"http://localhost:8000/test-callback\"}"
```

---

## 📦 Estrutura do Callback

Quando o processamento é concluído, a API envia um POST para a `callback_url` fornecida:

### Callback de Sucesso

```json
{
  "cpf_id": 1,
  "machine_id": "abc-123-def",
  "success": true,
  "cpf": "12345678900",
  "processing_time": 45,
  "timestamp": "2025-12-31 15:30:45",
  "data_processamento": "2025-12-31",
  "hora_processamento": "15:30:45",
  "error": null,
  "data": {
    "cliente": {
      "nome": "João Silva",
      "tipo_proposta": "Refinanciamento",
      "correntista_safra": "Sim",
      "cpf": "12345678900",
      "produto": "Veículo",
      "endereco": "Rua Exemplo, 123",
      "cep": "12345-678",
      "cidade": "São Paulo",
      "uf": "SP",
      "resultado": "PROPOSTA INCLUÍDA"
    },
    "veiculo": {
      "marca": "VOLKSWAGEN",
      "modelo": "GOL",
      "ano_fabricacao": "2018",
      "ano_modelo": "2019",
      "placa": "ABC1D23",
      "chassi": "9BWAA05U0AP123456"
    },
    "operacao": {
      "contrato": "123456789",
      "data_contrato": "15/03/2023",
      "valor_compra": "45.000,00",
      "plano": "36 meses",
      "valor_parcelas_pagas": "15.000,00",
      "quantidade_parcelas_pagas": "12",
      "dias_atraso": "45",
      "data_parcela_vencida": "01/12/2025",
      "saldo_contabil": "30.000,00",
      "saldo_gerencial": "29.500,00",
      "saldo_principal": "28.000,00",
      "saldo_contabil_cdi": "30.500,00",
      "plano_balao": "Não"
    },
    "resumo_proposta": {
      "valor_veiculo": "35.000,00",
      "valor_financiado": "28.000,00",
      "entrada": "7.000,00",
      "prazo": "48 meses",
      "taxa_juros": "1,99% a.m.",
      "valor_parcela": "850,00"
    },
    "estimativa_venda": {
      "valor_fipe": "32.000,00",
      "valor_estimado": "30.000,00",
      "percentual_fipe": "93,75%"
    }
  }
}
```

### Callback de Erro

```json
{
  "cpf_id": 1,
  "machine_id": "abc-123-def",
  "success": false,
  "cpf": "12345678900",
  "processing_time": 15,
  "timestamp": "2025-12-31 15:30:45",
  "data_processamento": "2025-12-31",
  "hora_processamento": "15:30:45",
  "error": "Timeout ao buscar CPF",
  "data": {
    "cliente": {
      "cpf": "12345678900",
      "resultado": "ERRO NO PROCESSAMENTO"
    }
  }
}
```

### Callback "Nenhum Contrato Localizado"

```json
{
  "cpf_id": 1,
  "machine_id": "abc-123-def",
  "success": true,
  "cpf": "12345678900",
  "processing_time": 8,
  "timestamp": "2025-12-31 15:30:45",
  "data_processamento": "2025-12-31",
  "hora_processamento": "15:30:45",
  "error": null,
  "data": {
    "cliente": {
      "cpf": "12345678900",
      "resultado": "Nenhum contrato localizado"
    }
  }
}
```

---

## 🚀 Iniciando a API

```bash
python ./run_api.py
```

Ou com o Python do ambiente virtual:

```bash
C:/Users/Luccas/Documents/ProjetosDMA2025/rpa/.venv/Scripts/python.exe ./run_api.py
```

A API estará disponível em: **http://localhost:8000**

Documentação interativa (Swagger): **http://localhost:8000/docs**

---

## 🔍 Estados do Chrome

A API gerencia automaticamente o estado do Chrome:

| Estado | Descrição | Próxima Ação |
|--------|-----------|--------------|
| `FECHADO` | Chrome fechado | Abre Chrome + Login + Nova Proposta |
| `LOGANDO` | Fazendo login no sistema | Aguarda conclusão do login |
| `OCIOSO_LOGADO` | Chrome aberto, input CPF focado | Só digita o CPF (otimizado) |
| `PROCESSANDO` | Processando CPF atual | Aguarda conclusão |

### Otimização

- **1º CPF:** Abre Chrome → Login → Nova Proposta → Processa (±30s)
- **CPFs 2+:** Só digita no input já focado (±15s) - **Economia de 50%!**

---

## ⚙️ Funcionalidades Especiais

### 🔄 Preenchimento Automático Repasse/Banco

Se `dias_atraso > 180`, o campo "Repasse / Banco" é preenchido automaticamente com o valor do "Saldo Contábil".

### 🧹 Limpeza Automática de Input

Após enviar o callback, o sistema:
1. Clica no menu Pesquisa
2. Clica no input CPF
3. **Limpa o campo** (Ctrl+A + Delete)
4. Deixa focado e pronto para o próximo

### ⏱️ Timeout de Inatividade

Chrome fecha automaticamente após **10 minutos** de inatividade.

### 🔁 Recuperação de Erros

Se o Chrome travar ou fechar inesperadamente, o sistema detecta e reinicia automaticamente na próxima requisição.

---

## 📝 Notas Importantes

1. **Processamento Assíncrono:** A rota `/processar-cpf` retorna 202 imediatamente. O resultado chega via callback.

2. **Callback Obrigatório:** Sempre forneça uma `callback_url` válida para receber os resultados.

3. **Chrome em Background:** O Chrome fica aberto entre processamentos para otimizar performance.

4. **Coordenadas Salvas:** Todas as coordenadas são salvas automaticamente em `coordenadas.json`.

5. **Logs Detalhados:** Acompanhe o processamento em tempo real no console da API.

---

## 🆘 Troubleshooting

**Chrome não abre?**
- Use `/restart` para resetar o serviço

**Processamento travado?**
- Verifique `/status` para ver o estado atual
- Use `/restart` se necessário

**Erro 422 Unprocessable Entity?**
- Verifique se todos os campos obrigatórios estão presentes no JSON

**Callback não chegou?**
- Verifique a `callback_url` fornecida
- Veja logs no console da API para detalhes do erro

---

**Versão:** 1.0.0  
**Última atualização:** 31/12/2025
