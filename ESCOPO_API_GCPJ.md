# 📋 ESCOPO - API GCPJ com Sessão Persistente

## 🎯 Objetivo
Criar uma API FastAPI que processa números GCPJ mantendo o Chrome logado e a sessão ativa, fechando o navegador apenas após 10 minutos de inatividade.

---

## 🏗️ Arquitetura

### **Estrutura de Arquivos**
```
gcpj/
├── run_api_gcpj.py           # Script principal para iniciar a API
├── api_gcpj/
│   ├── __init__.py
│   ├── main.py               # Endpoints FastAPI
│   ├── session_manager.py    # Gerenciador de sessão do Chrome
│   ├── processor.py          # Lógica de processamento GCPJ
│   └── models.py            # Modelos Pydantic
└── coordenadas_gcpj.json     # Coordenadas já capturadas
```

---

## 🔧 Componentes

### **1. SessionManager (session_manager.py)**

#### **Estados da Sessão**
- `FECHADO` - Chrome fechado, nenhuma sessão ativa
- `LOGANDO` - Abrindo Chrome e fazendo login inicial
- `OCIOSO_LOGADO` - Chrome aberto, logado, na tela de consulta esperando
- `PROCESSANDO` - Processando um GCPJ

#### **Responsabilidades**
- ✅ Abrir Chrome com perfil persistente
- ✅ Fazer login inicial no GCPJ (via extensão)
- ✅ Manter rastreamento de última atividade
- ✅ Monitorar inatividade (thread em background)
- ✅ Fechar Chrome após 10 minutos sem requisição
- ✅ Verificar se Chrome está aberto
- ✅ Verificar se está logado (na tela de consulta)

#### **Métodos Principais**
```python
class SessionManager:
    def __init__(self):
        # Configurações
        self.timeout_inatividade = 600  # 10 minutos
        self.estado = "FECHADO"
        self.driver = None
        self.last_activity = None
        
    def abrir_chrome_e_logar(self):
        """Abre Chrome e faz login completo até a tela de consulta"""
        
    def verificar_sessao_ativa(self) -> bool:
        """Verifica se Chrome está aberto e logado"""
        
    def atualizar_atividade(self):
        """Atualiza timestamp da última atividade"""
        
    def fechar_chrome(self):
        """Fecha o Chrome gracefully"""
        
    def _monitor_inatividade(self):
        """Thread que monitora inatividade e fecha Chrome após 10 min"""
        
    def voltar_para_consulta(self):
        """Volta para a tela de consulta (após processar um GCPJ)"""
```

---

### **2. Processor (processor.py)**

#### **Responsabilidades**
- ✅ Processar número GCPJ recebido
- ✅ Usar coordenadas já capturadas (coordenadas_gcpj.json)
- ✅ Preencher campo de busca
- ✅ Clicar em BUSCAR
- ✅ Extrair todos os dados (envolvidos, contratos, etc)
- ✅ Retornar JSON estruturado
- ✅ Voltar para tela de consulta

#### **Fluxo de Processamento**
```
1. Recebe GCPJ (ex: "1300285552")
2. Campo de busca já está visível (sessão ativa)
3. Digita GCPJ
4. Clica BUSCAR
5. Aguarda carregamento
6. Copia dados da tela (Ctrl+A, Ctrl+C)
7. Clica no primeiro envolvido
8. Extrai dados da dependência
9. Clica em Contratos
10. Extrai contratos
11. Volta para tela de consulta (2 cliques)
12. Retorna dados estruturados
```

#### **Função Principal**
```python
def processar_gcpj(session_manager: SessionManager, gcpj: str) -> dict:
    """
    Processa um número GCPJ e retorna dados estruturados
    
    Args:
        session_manager: Gerenciador de sessão
        gcpj: Número do GCPJ (ex: "1300285552")
        
    Returns:
        {
            "success": True/False,
            "gcpj": "1300285552",
            "timestamp": "2026-01-07 14:30:00",
            "error": None ou mensagem de erro,
            "data": {
                "dados_processo": {...},
                "classificacao": {...},
                "envolvidos": [...],
                "dados_dependencia": {...},
                "contratos": [...],
                "advogados": [...]
            }
        }
    """
```

---

### **3. API Main (main.py)**

#### **Endpoints**

##### **POST /processar-gcpj**
Recebe número GCPJ para processar

**Request:**
```json
{
    "gcpj": "1300285552",
    "callback_url": "https://seu-sistema.com/webhook" (opcional)
}
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
    "data": {
        "dados_processo": {...},
        "envolvidos": [...],
        "contratos": [...]
    }
}
```

##### **GET /status**
Retorna status da sessão

**Response:**
```json
{
    "estado": "OCIOSO_LOGADO",
    "chrome_aberto": true,
    "ultima_atividade": "2026-01-07 14:28:00",
    "tempo_inativo_segundos": 45,
    "fecha_em_segundos": 555,
    "total_processados": 10
}
```

##### **POST /fechar-sessao**
Força fechamento do Chrome

**Response:**
```json
{
    "message": "Chrome fechado com sucesso"
}
```

##### **GET /health**
Health check

**Response:**
```json
{
    "status": "ok",
    "uptime_seconds": 3600
}
```

---

## 🔄 Fluxo de Funcionamento

### **Cenário 1: Primeira Requisição (Chrome Fechado)**
```
1. POST /processar-gcpj com GCPJ "1300285552"
2. SessionManager detecta: estado = FECHADO
3. Abre Chrome com perfil persistente
4. Clica na extensão GCPJ
5. Digita "GCPJ" no campo
6. Clica em "GCPJ" no menu
7. Clica em "ACESSAR"
8. Clica em "Consulta de Processos"
9. Agora está na tela de consulta (estado = OCIOSO_LOGADO)
10. Processa o GCPJ
11. Volta para tela de consulta
12. Atualiza last_activity
13. Envia callback com resultado
```

### **Cenário 2: Requisições Subsequentes (Chrome Aberto)**
```
1. POST /processar-gcpj com GCPJ "1300285553"
2. SessionManager detecta: estado = OCIOSO_LOGADO
3. Chrome JÁ ESTÁ na tela de consulta
4. Processa o GCPJ diretamente
5. Volta para tela de consulta
6. Atualiza last_activity
7. Envia callback com resultado
```

### **Cenário 3: Timeout de Inatividade**
```
1. Última requisição foi às 14:00:00
2. Thread de monitoramento verifica a cada 30 segundos
3. Às 14:10:00 (10 minutos depois):
   - Detecta inatividade >= 600 segundos
   - Fecha Chrome gracefully
   - Estado = FECHADO
4. Próxima requisição vai fazer login completo novamente
```

---

## ⚙️ Configurações (.env)

```env
# API
API_HOST=0.0.0.0
API_PORT=8001

# Timeout (segundos)
TIMEOUT_INATIVIDADE=600  # 10 minutos

# Chrome
BROWSER_TIMEOUT=30

# Machine ID (identificador único)
MACHINE_ID=gcpj-machine-01
```

---

## 📦 Dependências (requirements.txt)

Já existem no projeto:
- ✅ fastapi
- ✅ uvicorn
- ✅ pydantic
- ✅ selenium
- ✅ webdriver-manager
- ✅ pyautogui
- ✅ pyperclip
- ✅ Pillow
- ✅ pyscreeze
- ✅ python-dotenv
- ✅ requests

---

## 🚀 Como Executar

```bash
# 1. Ativar ambiente virtual
source .venv/Scripts/activate  # Git Bash
# ou
.venv\Scripts\activate  # CMD/PowerShell

# 2. Instalar dependências (se necessário)
pip install -r requirements.txt

# 3. Iniciar API
python run_api_gcpj.py
```

---

## 🔍 Monitoramento

### **Logs da API**
```
✓ SessionManager inicializado
  Timeout de inatividade: 600s (10 minutos)
  
🌐 Abrindo Chrome...
🔑 Fazendo login no GCPJ...
   1. Clicando na extensão...
   2. Digitando GCPJ...
   3. Clicando em ACESSAR...
✅ Login completo! Estado: OCIOSO_LOGADO

📥 Nova requisição: GCPJ 1300285552
🔄 Processando...
✅ Processado com sucesso! (45s)
↩️  Voltando ao menu de consulta...

⏱️  Última atividade: há 2 minutos
⏱️  Última atividade: há 5 minutos
⚠️  10 minutos de inatividade detectados
🔴 Fechando Chrome...
✅ Chrome fechado. Estado: FECHADO
```

---

## 🧪 Testes

### **Teste Manual 1: Primeira Requisição**
```bash
curl -X POST http://localhost:8001/processar-gcpj \
  -H "Content-Type: application/json" \
  -d '{"gcpj": "1300285552", "callback_url": "https://webhook.site/..."}'
```

### **Teste Manual 2: Requisições Consecutivas**
```bash
# Enviar 3 requisições com 30 segundos de intervalo
curl -X POST http://localhost:8001/processar-gcpj \
  -H "Content-Type: application/json" \
  -d '{"gcpj": "1300285552"}'

# Aguardar 30 segundos

curl -X POST http://localhost:8001/processar-gcpj \
  -H "Content-Type: application/json" \
  -d '{"gcpj": "1300285553"}'
```

### **Teste Manual 3: Timeout de Inatividade**
```bash
# Enviar requisição
curl -X POST http://localhost:8001/processar-gcpj \
  -H "Content-Type: application/json" \
  -d '{"gcpj": "1300285552"}'

# Aguardar 11 minutos (Chrome deve fechar)

# Verificar status
curl http://localhost:8001/status
# Deve retornar: "estado": "FECHADO", "chrome_aberto": false
```

### **Teste Manual 4: Status da Sessão**
```bash
curl http://localhost:8001/status
```

---

## ✅ Checklist de Implementação

### **Fase 1: SessionManager**
- [ ] Criar classe SessionManager
- [ ] Implementar estados (FECHADO, LOGANDO, OCIOSO_LOGADO, PROCESSANDO)
- [ ] Implementar abrir_chrome_e_logar()
- [ ] Implementar thread de monitoramento de inatividade
- [ ] Implementar fechar_chrome() após 10 minutos
- [ ] Implementar voltar_para_consulta()

### **Fase 2: Processor**
- [ ] Criar função processar_gcpj()
- [ ] Carregar coordenadas de coordenadas_gcpj.json
- [ ] Implementar preenchimento do campo GCPJ
- [ ] Implementar extração de dados (envolvidos, contratos)
- [ ] Implementar volta para tela de consulta

### **Fase 3: API Endpoints**
- [ ] Criar endpoint POST /processar-gcpj
- [ ] Implementar processamento em background
- [ ] Implementar callback quando terminar
- [ ] Criar endpoint GET /status
- [ ] Criar endpoint POST /fechar-sessao
- [ ] Criar endpoint GET /health

### **Fase 4: Testes**
- [ ] Testar primeira requisição (login completo)
- [ ] Testar requisições consecutivas (sessão mantida)
- [ ] Testar timeout de 10 minutos
- [ ] Testar callback funcionando
- [ ] Testar múltiplos GCPJs em sequência

### **Fase 5: Documentação**
- [ ] Atualizar README.md
- [ ] Criar exemplos de uso
- [ ] Documentar variáveis de ambiente
- [ ] Criar guia de troubleshooting

---

## 🎯 Diferenças vs API Safra

| Característica | API Safra | API GCPJ |
|---|---|---|
| **Login** | Usuário/senha em site | Extensão Chrome + cliques |
| **Tela inicial** | Pesquisa de CPF | Consulta de Processos |
| **Entrada** | CPF (11 dígitos) | GCPJ (10 dígitos) |
| **Coordenadas** | Não usa | Usa coordenadas_gcpj.json |
| **Dados extraídos** | Cliente, veículo, operação | Processo, envolvidos, contratos |
| **Volta ao início** | Link "Nova Pesquisa" | 2 cliques (coordenadas) |

---

## 🔐 Segurança

- ✅ Chrome Profile isolado (chrome_profile/)
- ✅ Extensão salva no profile (não precisa reinstalar)
- ✅ Login mantido na extensão
- ✅ Sem credenciais em código (apenas coordenadas)
- ✅ Thread-safe com locks
- ✅ Graceful shutdown do Chrome

---

## 🐛 Troubleshooting

### **Chrome não abre**
- Verificar se ChromeDriver está instalado
- Verificar permissões da pasta chrome_profile/

### **Coordenadas não funcionam**
- Executar: `python src/gcpj_capturar_coordenadas.py`
- Recapturar coordenadas

### **Chrome não fecha após 10 minutos**
- Verificar logs da thread de monitoramento
- Verificar variável TIMEOUT_INATIVIDADE no .env

### **Extensão pede login toda vez**
- Chrome Profile não está persistindo
- Verificar pasta chrome_profile/
- Logar na extensão e salvar credenciais

---

**Status**: 📋 **ESCOPO COMPLETO - PRONTO PARA IMPLEMENTAÇÃO**
