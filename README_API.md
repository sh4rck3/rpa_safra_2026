# API RPA Safra - Documentação

## 📋 Visão Geral

API REST para processamento distribuído de CPFs via automação web. Cada servidor Python processa **1 CPF por vez** e retorna o resultado via callback para o Laravel, que controla toda a orquestração.

## 🏗️ Arquitetura

```
Laravel (Orquestrador)
    ↓ POST /processar-cpf
Python API (Worker)
    ↓ processa assíncrono
    ↓ POST callback_url
Laravel (Recebe resultado)
    ↓ responde com próximo CPF
Python API (Processa próximo)
    ... ciclo continua
```

## 🚀 Instalação

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar .env

```env
# Credenciais do site
WEBSITE_URL=https://seu-site.com
SITE_USERNAME=seu_usuario
SITE_PASSWORD=sua_senha

# Configurações da API
API_HOST=0.0.0.0
API_PORT=8000
MACHINE_ID=MAQUINA_01
TIMEOUT_INATIVIDADE=600
```

**Importante**: Defina um `MACHINE_ID` único para cada máquina (ex: `MAQUINA_01`, `MAQUINA_02`, etc)

### 3. Iniciar Servidor

**Opção 1 - Script Python (Recomendado):**
```bash
python run_api.py
```

**Opção 2 - Windows Batch:**
```bash
start_api.bat
```

**Opção 3 - Uvicorn Direto:**
```bash
# Windows
set PYTHONPATH=%CD%
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Linux/Mac
PYTHONPATH=. python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 Endpoints

### POST /processar-cpf

Recebe um CPF para processamento.

**Request Body:**
```json
{
    "cpf_id": 123,
    "contrato": "123456",
    "nome": "João da Silva",
    "cpf": "12345678901",
    "callback_url": "https://seu-laravel.com/api/rpa/callback"
}
```

**Response 200 OK (Aceito):**
```json
{
    "status": "accepted",
    "cpf_id": 123,
    "message": "CPF aceito para processamento",
    "machine_id": "MAQUINA_01"
}
```

**Response 503 Service Unavailable (Ocupado):**
```json
{
    "status": "busy",
    "message": "Servidor ocupado processando outro CPF",
    "machine_id": "MAQUINA_01"
}
```

---

### GET /health

Verifica status do servidor.

**Response:**
```json
{
    "status": "healthy",
    "estado": "OCIOSO_LOGADO",
    "uptime": 3600,
    "cpf_atual": null,
    "machine_id": "MAQUINA_01",
    "timestamp": "2025-11-28 14:30:00"
}
```

**Estados possíveis:**
- `FECHADO`: Chrome fechado, servidor disponível
- `OCIOSO_LOGADO`: Chrome aberto/logado, pronto para processar
- `PROCESSANDO`: Ocupado processando um CPF

---

### GET /status

Informações detalhadas do servidor.

**Response:**
```json
{
    "machine_id": "MAQUINA_01",
    "uptime": 3600,
    "estado": "OCIOSO_LOGADO",
    "chrome_aberto": true,
    "cpf_atual": {
        "cpf_id": 123,
        "cpf": "12345678901",
        "nome": "João da Silva"
    },
    "total_processados": 45,
    "total_erros": 2,
    "timestamp": "2025-11-28 14:30:00"
}
```

---

### POST {callback_url} (Callback para Laravel)

Após processar, o Python envia resultado de volta.

**Request Body:**
```json
{
    "cpf_id": 123,
    "machine_id": "MAQUINA_01",
    "success": true,
    "cpf": "12345678901",
    "processing_time": 45,
    "timestamp": "2025-11-28 14:30:00",
    "data_processamento": "2025-11-28",
    "hora_processamento": "14:30:00",
    "error": null,
    "data": {
        "cliente": {
            "nome": "JOAO DA SILVA",
            "cpf": "123.456.789-01",
            "resultado": "SUCESSO",
            ...
        },
        "veiculo": { ... },
        "operacao": { ... },
        "resumo_proposta": { ... },
        "estimativa_venda": { ... }
    }
}
```

**Laravel pode responder com próximo CPF:**
```json
{
    "status": "success",
    "message": "Resultado salvo",
    "proximo_cpf": {
        "cpf_id": 124,
        "contrato": "654321",
        "nome": "Maria Santos",
        "cpf": "98765432100",
        "callback_url": "https://seu-laravel.com/api/rpa/callback"
    }
}
```

Se não houver próximo CPF:
```json
{
    "status": "success",
    "message": "Resultado salvo"
}
```

## 🔄 Fluxo de Processamento

### 1. Estado Inicial: FECHADO
```
- Chrome fechado
- Aguardando primeira requisição
```

### 2. Recebe POST /processar-cpf
```
- Retorna 200 (aceito)
- Abre Chrome em background
- Faz login
- Estado → PROCESSANDO
```

### 3. Processa CPF
```
- Navega na página
- Preenche formulários
- Captura dados
- Extrai informações
```

### 4. Envia Callback
```
- POST para callback_url com resultado
- Laravel salva no BD
- Laravel responde com próximo CPF (se houver)
```

### 5. Recebe Próximo CPF na Resposta
```
- Python processa imediatamente
- Estado → PROCESSANDO
- Ciclo se repete
```

### 6. Sem Próximo CPF
```
- Estado → OCIOSO_LOGADO
- Timer de 10min inicia
- Se passar 10min sem atividade → fecha Chrome
- Estado → FECHADO
```

## ⚙️ Gerenciamento de Sessão

### Timer de Inatividade
- **Padrão**: 10 minutos (600 segundos)
- **Configurável via**: `TIMEOUT_INATIVIDADE` no `.env`
- **Comportamento**: Fecha Chrome automaticamente após inatividade

### Estados da Máquina

| Estado | Descrição | Chrome | Aceita CPF? |
|--------|-----------|--------|-------------|
| `FECHADO` | Inicial/Inativo | Fechado | ✅ Sim (abre e loga) |
| `LOGANDO` | Abrindo Chrome | Abrindo | ❌ Não |
| `OCIOSO_LOGADO` | Disponível | Aberto | ✅ Sim |
| `PROCESSANDO` | Ocupado | Aberto | ❌ Não (503) |

## 🔧 Configuração Laravel

### 1. Lista de Servidores Python

Configure os IPs/URLs dos servidores Python:

```php
// config/rpa.php
return [
    'servers' => [
        'MAQUINA_01' => 'http://192.168.1.101:8000',
        'MAQUINA_02' => 'http://192.168.1.102:8000',
        'MAQUINA_03' => 'http://192.168.1.103:8000',
        'MAQUINA_04' => 'http://192.168.1.104:8000',
        'MAQUINA_05' => 'http://192.168.1.105:8000',
        'MAQUINA_06' => 'http://192.168.1.106:8000',
    ],
    'timeout' => 300, // 5 minutos
];
```

### 2. Verificar Servidor Disponível

```php
// Verificar health de cada servidor
foreach (config('rpa.servers') as $machineId => $url) {
    $response = Http::timeout(5)->get("$url/health");
    
    if ($response->successful()) {
        $data = $response->json();
        
        // Se está OCIOSO_LOGADO ou FECHADO, pode enviar CPF
        if (in_array($data['estado'], ['OCIOSO_LOGADO', 'FECHADO'])) {
            return $url; // Servidor disponível
        }
    }
}
```

### 3. Enviar CPF para Processar

```php
$cpf = Cpf::whereStatus('pending')->first();

$response = Http::timeout(10)->post("$serverUrl/processar-cpf", [
    'cpf_id' => $cpf->id,
    'contrato' => $cpf->contrato,
    'nome' => $cpf->nome,
    'cpf' => $cpf->cpf,
    'callback_url' => route('api.rpa.callback'),
]);

if ($response->successful()) {
    // Marcar como "em processamento"
    $cpf->update([
        'status' => 'processing',
        'machine_id' => $response['machine_id'],
    ]);
} else if ($response->status() === 503) {
    // Servidor ocupado, tentar outro
}
```

### 4. Receber Callback

```php
// routes/api.php
Route::post('/rpa/callback', [RpaController::class, 'callback']);

// RpaController.php
public function callback(Request $request)
{
    $cpfId = $request->cpf_id;
    $cpf = Cpf::find($cpfId);
    
    // Salvar resultado
    $cpf->update([
        'status' => $request->success ? 'completed' : 'error',
        'resultado' => $request->data,
        'processing_time' => $request->processing_time,
        'processed_at' => now(),
    ]);
    
    // Buscar próximo CPF da mesma batch
    $proximoCpf = Cpf::where('batch_id', $cpf->batch_id)
        ->whereStatus('pending')
        ->first();
    
    if ($proximoCpf) {
        // Retornar próximo CPF na resposta
        return response()->json([
            'status' => 'success',
            'message' => 'Resultado salvo',
            'proximo_cpf' => [
                'cpf_id' => $proximoCpf->id,
                'contrato' => $proximoCpf->contrato,
                'nome' => $proximoCpf->nome,
                'cpf' => $proximoCpf->cpf,
                'callback_url' => route('api.rpa.callback'),
            ],
        ]);
    }
    
    // Sem próximo CPF
    return response()->json([
        'status' => 'success',
        'message' => 'Resultado salvo',
    ]);
}
```

## 📊 Monitoramento

### Dashboard Laravel

Exibir status de cada máquina:

```php
$servidores = [];

foreach (config('rpa.servers') as $machineId => $url) {
    try {
        $response = Http::timeout(5)->get("$url/status");
        $servidores[$machineId] = $response->json();
    } catch (\Exception $e) {
        $servidores[$machineId] = [
            'estado' => 'OFFLINE',
            'error' => $e->getMessage(),
        ];
    }
}

return view('dashboard', compact('servidores'));
```

## 🐛 Troubleshooting

### Servidor não aceita conexões
```bash
# Verificar se está rodando
curl http://localhost:8000/health

# Verificar firewall
# Windows: permitir porta 8000
```

### Chrome não abre
- Verificar credenciais no `.env`
- Verificar se ChromeDriver está instalado
- Verificar logs da aplicação

### Timeout de inatividade muito curto/longo
- Ajustar `TIMEOUT_INATIVIDADE` no `.env`
- Valor em segundos (600 = 10 minutos)

### Callback não funciona
- Verificar se `callback_url` está acessível do servidor Python
- Verificar firewall entre Python e Laravel

## 📝 Logs

Os logs são exibidos no console onde o servidor está rodando.

Para redirecionar para arquivo:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1
```

## 🔐 Segurança

### Recomendações

1. **Não expor porta 8000 na internet** - Use VPN ou rede interna
2. **Implementar autenticação** - Adicionar token JWT se necessário
3. **HTTPS** - Use nginx como reverse proxy com SSL
4. **Validar callback_url** - Aceitar apenas URLs do Laravel

## 📦 Estrutura do Projeto

```
rpa/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app e endpoints
│   ├── worker.py            # Gerenciador de jobs
│   ├── session_manager.py   # Controle do Chrome
│   └── processor.py         # Lógica de processamento
├── src/
│   └── processar_lote.py    # Funções originais reutilizadas
├── .env                      # Configurações
├── requirements.txt          # Dependências
└── README_API.md            # Esta documentação
```

## 🚦 Exemplo Completo

### 1. Iniciar servidor Python
```bash
cd rpa
python -m api.main
```

### 2. Laravel envia CPF
```bash
curl -X POST http://192.168.1.101:8000/processar-cpf \
  -H "Content-Type: application/json" \
  -d '{
    "cpf_id": 1,
    "contrato": "123456",
    "nome": "João Silva",
    "cpf": "12345678901",
    "callback_url": "https://seu-laravel.com/api/rpa/callback"
  }'
```

### 3. Python processa e envia callback
```bash
# Python faz automaticamente
POST https://seu-laravel.com/api/rpa/callback
{
  "cpf_id": 1,
  "success": true,
  "data": { ... }
}
```

### 4. Laravel responde com próximo
```json
{
  "status": "success",
  "proximo_cpf": {
    "cpf_id": 2,
    "cpf": "98765432100",
    ...
  }
}
```

## 🎯 Benefícios desta Arquitetura

✅ **Controle centralizado** - Laravel gerencia tudo  
✅ **Auto-regulação** - Cada máquina no seu ritmo  
✅ **Resiliência** - Falha em uma não afeta outras  
✅ **Escalável** - Adicionar máquinas é trivial  
✅ **Zero ociosidade** - Processa continuamente  
✅ **Monitoramento fácil** - Status de todas as máquinas

---

**Versão:** 1.0.0  
**Data:** 28/11/2025
