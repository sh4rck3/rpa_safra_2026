# RPA Safra Financeira - Processamento em Lote

## 📋 Descrição

Sistema de automação RPA (Robotic Process Automation) para processamento em lote de consultas de CPF no portal Safra Financeira. O sistema realiza login automático, pesquisa múltiplos CPFs, extrai dados estruturados e envia para webhook N8N.

## 🎯 Funcionalidades Principais

### Processamento em Lote (`processar_lote.py`)

- ✅ **Leitura automática de arquivo CSV** com lista de CPFs da pasta `input/`
- ✅ **Login único** - mantém sessão durante todo o processamento
- ✅ **Processamento sequencial** de todos os CPFs da lista
- ✅ **Detecção automática** de CPFs não encontrados
- ✅ **Sistema de retry** - até 3 tentativas por CPF em caso de erro
- ✅ **Envio automático** para webhook N8N (success/error)
- ✅ **Geração de relatório CSV** com status de cada CPF
- ✅ **Sistema de logs** detalhado com timestamp
- ✅ **Navegação por coordenadas** - sistema resiliente a mudanças de DOM

## 📁 Estrutura do Projeto

```
phyton/
├── input/              # Arquivos CSV com CPFs para processar
├── output/             # Relatórios CSV com resultados
├── logs/               # Logs de execução
├── downloads/          # JSONs individuais (backup)
├── src/
│   ├── processar_lote.py      # Script principal de processamento em lote
│   ├── test_login.py           # Script de teste individual
│   └── testar_webhook.py       # Script de teste do webhook N8N
├── coordenadas.json    # Coordenadas dos elementos salvos
├── .env                # Credenciais (não commitado)
├── requirements.txt    # Dependências Python
└── README.md           # Este arquivo
```

## � Como Usar

### 1. Preparar Ambiente

```bash
# Clonar repositório
git clone https://github.com/sh4rck3/rpa_safra.git
cd rpa_safra

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Credenciais

Criar arquivo `.env` na raiz do projeto:

```env
WEBSITE_URL=https://wwws.jsafra.com.br/FinanceiraVeiculos/LoginForm
SITE_USERNAME=seu_usuario
SITE_PASSWORD=sua_senha
BROWSER_TIMEOUT=30
```

### 3. Preparar Arquivo de Entrada

Criar arquivo CSV na pasta `input/` com o formato:

```csv
CONTRATO;NOME;CPFCNPJ
90000633100;ANTONIA IRANEIDE MORAES ELIAS;90000633100
53088247115;MARLON MILHOMEN DOS SANTOS;00053088247115
43892701172;NAGAI RODRIGUES REIS DO NASCIMENTO;43892701172
```

**Importante:** A coluna `CPFCNPJ` (terceira coluna) é usada para a pesquisa.

### 4. Executar Processamento

```bash
venv/Scripts/python.exe src/processar_lote.py
```

### 5. Primeira Execução - Captura de Coordenadas

Na primeira execução, o sistema solicitará que você posicione o mouse sobre os elementos da tela:

1. **Campo CPF** - onde digitar o CPF
2. **Botão Pesquisar** - botão de pesquisa
3. **Botão Nova Proposta** (após pesquisa)
4. **Botão Fechar Modal** (primeiro modal)
5. **Dropdown Modal** (segundo modal)
6. **Opção do Dropdown**
7. **Botão Incluir**
8. **Botão Voltar/Pesquisa** - para retornar à tela de pesquisa
9. **Botão Fechar Modal de Erro** - quando CPF não é encontrado

Após capturar, as coordenadas são salvas em `coordenadas.json` e reutilizadas automaticamente.

## 📊 Resultado do Processamento

### Arquivo CSV de Saída (`output/`)

Formato: `lote_cpfs_processado_YYYYMMDD_HHMMSS.csv`

```csv
CONTRATO;NOME;CPFCNPJ;STATUS;MENSAGEM
90000633100;ANTONIA...;90000633100;SUCCESS;Dados enviados ao webhook
53088247115;MARLON...;00053088247115;ERROR;CPF não encontrado - Nenhum contrato localizado
```

### Logs (`logs/`)

Formato: `execucao_YYYYMMDD.log`

```
[20251114_190953] ============================================================
[20251114_190953] INÍCIO DA EXECUÇÃO
[20251114_190953] Arquivo encontrado: lote_cpfs.txt
[20251114_190953] CPFs carregados: 19
[20251114_190953] PROCESSAMENTO CONCLUÍDO - Sucessos: 15, Erros: 4
[20251114_190953] Arquivo de saída: output\lote_cpfs_processado_20251114_190953.csv
[20251114_190953] ============================================================
```

## 🔌 Integração com Webhook N8N

### Formato de Envio (Sucesso)

```json
{
  "success": true,
  "cpf": "00012345678",
  "timestamp": "2025-11-14T19:30:00",
  "error": null,
  "data": {
    "cliente": {
      "nome": "JOAO DA SILVA",
      "cpf": "000.123.456-78",
      "endereco": "RUA TESTE, 123",
      "cidade": "BRASILIA",
      "uf": "DF"
    },
    "veiculo": {
      "marca": "VOLKSWAGEN",
      "modelo": "GOL 1.0",
      "placa": "ABC1234"
    },
    "operacao": {
      "contrato": "123456789",
      "valor_compra": "R$ 50.000,00",
      "saldo_contabil": "R$ 20.000,00"
    },
    "resumo_proposta": { },
    "estimativa_venda": { }
  }
}
```

### Formato de Envio (Erro)

```json
{
  "success": false,
  "cpf": "99999999999",
  "timestamp": "2025-11-14T19:30:00",
  "error": "CPF não encontrado - Nenhum contrato localizado",
  "data": null
}
```

## 🧪 Testar Webhook

Use o script `testar_webhook.py` para validar a integração:

```bash
venv/Scripts/python.exe src/testar_webhook.py
```

- Envia dados fictícios a cada 30 segundos
- Alterna entre sucesso e erro (2 sucessos, 1 erro)
- Pressione **Ctrl+C** para parar

## �️ Tecnologias Utilizadas

- **Python 3.10+**
- **Selenium** - Automação web
- **PyAutoGUI** - Controle de mouse/teclado por coordenadas
- **PyPerclip** - Captura de conteúdo da área de transferência
- **Requests** - Envio de dados para webhook
- **ChromeDriver** - Driver do navegador Chrome

## ⚙️ Detalhes Técnicos

### Sistema de Coordenadas

O sistema utiliza coordenadas de tela para interagir com elementos, tornando-o resiliente a mudanças no DOM Angular do portal Safra. As coordenadas são capturadas uma vez e reutilizadas.

### Detecção de CPF Não Encontrado

Após clicar em "Pesquisar", o sistema:
1. Captura todo o conteúdo da tela (Ctrl+A + Ctrl+C)
2. Verifica se contém a mensagem "Nenhum contrato localizado"
3. Se encontrar, fecha o modal e registra como ERROR
4. Se não encontrar, continua o fluxo normal

### Sistema de Retry

Cada CPF tem até 3 tentativas de processamento. Se falhar nas 3 tentativas:
- Envia `success: false` para o webhook
- Registra ERROR no CSV
- Continua processando os próximos CPFs

### Manutenção de Sessão

O sistema faz login uma única vez e mantém a sessão durante todo o processamento, navegando entre as telas usando o botão "Voltar/Pesquisa".

## � Observações Importantes

1. **Resolução de Tela**: As coordenadas são específicas para a resolução da tela onde foram capturadas
2. **Janela Maximizada**: O navegador é aberto maximizado para consistência
3. **Não Mover Janela**: Não mova ou redimensione o navegador durante o processamento
4. **Arquivo Input**: Apenas o primeiro arquivo encontrado em `input/` será processado
5. **Backup**: Os dados também são salvos como JSON individual em `downloads/`

## 🐛 Troubleshooting

### Erro: "Coordenada não encontrada"
- Delete `coordenadas.json` e execute novamente para recapturar

### Erro: "Nenhum arquivo encontrado em input/"
- Verifique se há arquivo `.csv` ou `.txt` na pasta `input/`

### Webhook não responde
- Verifique a URL do webhook no código
- Use `testar_webhook.py` para validar a conexão

### ChromeDriver incompatível
- O `webdriver-manager` baixa automaticamente a versão correta
- Se persistir, atualize: `pip install --upgrade webdriver-manager`

## 📄 Licença

Este projeto é de uso interno para automação de processos.

## 👤 Autor

Desenvolvido com GitHub Copilot
