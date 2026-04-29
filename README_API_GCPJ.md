# 🚀 Como Usar a API GCPJ

## 📋 Pré-requisitos

1. **Coordenadas capturadas**: Execute antes:
   ```bash
   python src/gcpj_capturar_coordenadas.py
   ```

2. **Extensão GCPJ instalada** no Chrome Profile

3. **Variáveis de ambiente** configuradas (opcional):
   ```env
   API_HOST=0.0.0.0
   API_PORT=8001
   TIMEOUT_INATIVIDADE=600  # 10 minutos
   ```

---

## ▶️ Iniciar API

```bash
# Ativar ambiente virtual
source .venv/Scripts/activate  # Git Bash
# ou
.venv\Scripts\activate  # CMD/PowerShell

# Iniciar API
python run_api_gcpj.py
```

A API estará disponível em: **http://localhost:8001**

Documentação interativa: **http://localhost:8001/docs**

---

## 🔌 Endpoints

### 1️⃣ **GET /health** - Verificar se está pronto

**SEMPRE consulte este endpoint antes de enviar GCPJ!**

```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "ok",
  "pronto_para_processar": true,
  "estado_sessao": "OCIOSO_LOGADO",
  "chrome_aberto": true,
  "uptime_seconds": 3600
}
```

✅ **pronto_para_processar: true** → Pode enviar GCPJ
❌ **pronto_para_processar: false** → Aguarde

---

### 2️⃣ **POST /processar-gcpj** - Processar GCPJ

```bash
curl -X POST http://localhost:8001/processar-gcpj \
  -H "Content-Type: application/json" \
  -d '{
    "gcpj": "1300285552",
    "callback_url": "https://seu-sistema.com/webhook"
  }'
```

**Response (Imediato):**
```json
{
  "status": "processando",
  "gcpj": "1300285552",
  "message": "GCPJ adicionado à fila de processamento"
}
```

**Callback (Quando terminar):**
```json
{
  "success": true,
  "gcpj": "1300285552",
  "timestamp": "2026-01-07 14:30:00",
  "processing_time": 45,
  "error": null,
  "data": {
    "dados_processo": {...},
    "classificacao": {...},
    "envolvidos": [...],
    "dados_dependencia": {...},
    "contratos": [...],
    "advogados": [...]
  }
}
```

---

### 3️⃣ **GET /status** - Status detalhado

```bash
curl http://localhost:8001/status
```

**Response:**
```json
{
  "estado": "OCIOSO_LOGADO",
  "chrome_aberto": true,
  "pronto_para_processar": true,
  "ultima_atividade": "2026-01-07 14:28:00",
  "tempo_inativo_segundos": 45,
  "fecha_em_segundos": 555,
  "total_processados": 10,
  "total_erros": 0
}
```

---

### 4️⃣ **POST /fechar-sessao** - Fechar Chrome

```bash
curl -X POST http://localhost:8001/fechar-sessao
```

**Response:**
```json
{
  "message": "Chrome fechado com sucesso"
}
```

---

## 🔄 Fluxo Completo

### **1ª Requisição (Chrome fechado)**
```
1. Consultar /health → pronto_para_processar: false
2. API abre Chrome e faz login automaticamente
3. Consultar /health novamente → pronto_para_processar: true
4. Enviar POST /processar-gcpj
5. Aguardar callback com resultado
6. Repetir para próximo GCPJ
```

### **2ª+ Requisições (Chrome logado)**
```
1. Consultar /health → pronto_para_processar: true
2. Enviar POST /processar-gcpj
3. Aguardar callback com resultado
4. Repetir
```

### **Timeout de Inatividade**
```
- Última requisição: 14:00:00
- Sem novas requisições por 10 minutos
- Às 14:10:00: Chrome fecha automaticamente
- Próxima requisição: faz login novamente
```

---

## ⚡ Exemplo de Uso em Python

```python
import requests
import time

API_URL = "http://localhost:8001"

def processar_gcpj(gcpj: str, callback_url: str = None):
    """Processa um GCPJ"""
    
    # 1. Verificar se está pronto
    while True:
        health = requests.get(f"{API_URL}/health").json()
        
        if health["pronto_para_processar"]:
            print("✅ API pronta para processar!")
            break
        
        print("⏳ Aguardando API ficar pronta...")
        time.sleep(5)
    
    # 2. Enviar GCPJ
    response = requests.post(
        f"{API_URL}/processar-gcpj",
        json={
            "gcpj": gcpj,
            "callback_url": callback_url
        }
    )
    
    print(f"📤 GCPJ enviado: {response.json()}")
    
    # 3. Aguardar callback (será enviado para callback_url)
    print("⏳ Aguardando processamento...")


# Processar múltiplos GCPJs
gcpjs = ["1300285552", "1300285553", "1300285554"]

for gcpj in gcpjs:
    processar_gcpj(gcpj, "https://webhook.site/seu-id")
    
    # Aguardar 5 segundos entre requisições
    time.sleep(5)
```

---

## 📊 Estados da Sessão

| Estado | Descrição | Chrome | Pode Processar? |
|--------|-----------|--------|-----------------|
| **FECHADO** | Chrome fechado | ❌ | ❌ |
| **LOGANDO** | Fazendo login | ✅ | ❌ |
| **OCIOSO_LOGADO** | Logado, esperando | ✅ | ✅ |
| **PROCESSANDO** | Processando GCPJ | ✅ | ❌ |

---

## 🐛 Troubleshooting

### **API não inicia**
```bash
# Verificar se porta 8001 está livre
netstat -ano | findstr :8001

# Mudar porta no .env
API_PORT=8002
```

### **Chrome não abre**
```bash
# Recapturar coordenadas
python src/gcpj_capturar_coordenadas.py

# Verificar permissões
ls -la chrome_profile/
```

### **Coordenadas não funcionam**
- Resolução da tela mudou
- Execute novamente: `python src/gcpj_capturar_coordenadas.py`

### **Chrome não fecha após 10 minutos**
```bash
# Verificar timeout no .env
TIMEOUT_INATIVIDADE=600

# Forçar fechamento
curl -X POST http://localhost:8001/fechar-sessao
```

---

## 🔒 Segurança

- ✅ Chrome Profile isolado (`chrome_profile/`)
- ✅ Extensão salva no profile (não precisa reinstalar)
- ✅ Thread-safe (processa um GCPJ por vez)
- ✅ Timeout automático de inatividade
- ✅ Graceful shutdown

---

## 📝 Logs

```
✓ SessionManager GCPJ inicializado
  Timeout de inatividade: 600s (10 minutos)
  Coordenadas carregadas: 11

🌐 Abrindo Chrome com perfil persistente...
✅ Chrome aberto!

🔑 Fazendo login no GCPJ...
   1. Clicando na extensão GCPJ...
   2. Clicando no campo de busca...
   3. Digitando 'GCPJ'...
   4. Clicando em 'GCPJ' no menu...
   5. Clicando em 'ACESSAR'...
   6. Clicando em 'Consulta de Processos'...
   ✅ Chegou na tela de consulta!
✅ Login completo! Estado: OCIOSO_LOGADO
   Pronto para processar GCPJs!

📥 Nova requisição recebida: GCPJ 1300285552

🔄 PROCESSANDO GCPJ: 1300285552
📝 Preenchendo campo de busca...
   ✅ GCPJ digitado: 1300285552
🔍 Clicando em BUSCAR...
   ✅ Busca realizada!
...
✅ GCPJ processado com sucesso! (45s)
🔙 Voltando para tela de consulta...
   ✅ Voltou para consulta!

⚠️  10 minutos de inatividade detectados
🔴 Fechando Chrome...
✅ Chrome fechado. Estado: FECHADO
```

---

**✅ API GCPJ implementada e pronta para uso!** 🚀
