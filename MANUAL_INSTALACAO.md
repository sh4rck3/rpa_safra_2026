# Manual de Instalação e Uso - RPA Safra Financeira

## 📋 Índice
1. [Requisitos do Sistema](#requisitos-do-sistema)
2. [Instalação](#instalação)
3. [Configuração](#configuração)
4. [Como Usar](#como-usar)
5. [Estrutura de Dados](#estrutura-de-dados)
6. [Solução de Problemas](#solução-de-problemas)

---

## 🖥️ Requisitos do Sistema

### Software Necessário
- **Windows 10/11** (64-bit)
- **Python 3.10 ou superior** - [Download Python](https://www.python.org/downloads/)
- **Google Chrome** (versão atualizada)
- **Git** (opcional, para clonar o repositório)

### Hardware Recomendado
- 4GB RAM mínimo (8GB recomendado)
- Tela com resolução mínima 1920x1080
- Conexão estável com internet

---

## 📦 Instalação

### Passo 1: Obter o Projeto

#### Opção A: Via Git (Recomendado)
```bash
git clone https://github.com/sh4rck3/rpa_safra.git
cd rpa_safra
```

#### Opção B: Download ZIP
1. Acesse: https://github.com/sh4rck3/rpa_safra
2. Clique em "Code" → "Download ZIP"
3. Extraia para uma pasta (ex: `C:\rpa_safra`)
4. Abra o terminal na pasta extraída

### Passo 2: Instalar Python

1. Baixe Python 3.10+ em: https://www.python.org/downloads/
2. **IMPORTANTE**: Marque a opção "Add Python to PATH" durante instalação
3. Após instalar, verifique no terminal:
```bash
python --version
```
ou
```bash
py --version
```

### Passo 3: Instalar Dependências

Abra o terminal na pasta do projeto e execute:

```bash
py -m pip install -r requirements.txt
```

Ou instale manualmente:
```bash
py -m pip install selenium webdriver-manager python-dotenv pyautogui pyperclip requests
```

---

## ⚙️ Configuração

### 1. Configurar Credenciais

Crie um arquivo `.env` na raiz do projeto com suas credenciais:

```env
WEBSITE_URL=https://seu-site-safra.com.br
SITE_USERNAME=seu_usuario
SITE_PASSWORD=sua_senha
BROWSER_TIMEOUT=30
```

**⚠️ IMPORTANTE**: Nunca compartilhe o arquivo `.env` ou faça commit dele no Git!

### 2. Configurar Webhook (Opcional)

Edite o arquivo `src/processar_lote.py` na linha 29:

```python
WEBHOOK_URL = "https://seu-webhook-n8n.com/webhook/seu-id"
```

### 3. Preparar Arquivo de CPFs

Crie um arquivo CSV na pasta `input/` com o formato:

```csv
CONTRATO;NOME;CPFCNPJ
123456;JOAO DA SILVA;12345678901
789012;MARIA SANTOS;98765432100
```

**Formato obrigatório**:
- Separador: **ponto e vírgula (;)**
- 3 colunas: CONTRATO, NOME, CPFCNPJ
- CPF sem pontos ou traços (apenas números)

---

## 🚀 Como Usar

### Primeira Execução (Captura de Coordenadas)

Na primeira vez, o sistema vai pedir para você posicionar o mouse em cada elemento da tela:

```bash
py src/processar_lote.py
```

**Sequência de capturas**:
1. Campo de CPF
2. Botão Pesquisar
3. Botão Nova Proposta (após pesquisa)
4. Fechar Modal 1
5. Dropdown Modal 2
6. Opção do Dropdown
7. Botão Incluir
8. Botão Voltar/Menu Pesquisa

**Coordenadas especiais** (só aparecem quando necessário):
- **Fechar modal de erro**: Quando CPF não encontrado
- **4 cliques NEGADO**: Quando proposta está negada (click1, click2, click3, click4)

### Execução Normal

Após capturar todas as coordenadas:

```bash
py src/processar_lote.py
```

O sistema irá:
1. ✅ Fazer login automaticamente
2. ✅ Processar cada CPF do arquivo CSV
3. ✅ Enviar dados para o webhook
4. ✅ Gerar arquivo de resultado em `output/`
5. ✅ Criar logs em `logs/`

### Testar Webhook (Opcional)

Para testar o webhook sem processar CPFs reais:

```bash
py src/testar_webhook.py
```

Este script envia dados fictícios a cada 30 segundos. Pressione `Ctrl+C` para parar.

---

## 📊 Estrutura de Dados

### Tipos de Resultado

O sistema identifica 5 cenários e envia para o webhook:

#### 1. ✅ SUCESSO - Dados Completos
```json
{
  "success": true,
  "cpf": "12345678901",
  "timestamp": "2025-11-25 14:30:00",
  "data_processamento": "2025-11-25",
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

#### 2. ⚠️ CANCELADO
```json
{
  "success": true,
  "data": {
    "cliente": {
      "cpf": "123.456.789-01",
      "resultado": "CANCELADO",
      ... // outros campos vazios
    }
  }
}
```

#### 3. ⚠️ NEGADA (com dados completos)
```json
{
  "success": true,
  "data": {
    "cliente": {
      "resultado": "NEGADA",
      ... // todos os campos preenchidos
    },
    "veiculo": { ... },
    "operacao": { ... },
    "resumo_proposta": { ... },
    "estimativa_venda": { ... }
  }
}
```

#### 4. ⚠️ ACORDO FORMALIZADO
```json
{
  "success": true,
  "data": {
    "cliente": {
      "resultado": "ACORDO FORMALIZADO (EM CUMPRIMENTO)",
      ... // outros campos vazios
    }
  }
}
```

#### 5. ❌ CPF NÃO ENCONTRADO
```json
{
  "success": false,
  "error": "CPF não encontrado - Nenhum contrato localizado",
  "data": {
    "cliente": {
      "cpf": "123.456.789-01",
      "resultado": "CPF/CNPJ Não encontrado"
    }
  }
}
```

### Campos Extraídos

**Cliente** (10 campos):
- nome, tipo_proposta, correntista_safra, cpf, produto, endereco, cep, cidade, uf, resultado

**Veículo** (9 campos):
- marca, modelo, modalidade, tipo, combustivel, placa, chassi, ano_fabricacao_modelo, renavam

**Operação** (13 campos):
- contrato, data_contrato, valor_compra, plano, valor_parcelas_pagas, quantidade_parcelas_pagas, dias_atraso, data_parcela_vencida, saldo_contabil, saldo_gerencial, saldo_principal, saldo_contabil_cdi, plano_balao

**Resumo Proposta** (11 campos):
- data_entrada, validade, primeiro_pagamento, qtd_parcelas_acordo, repasse_banco, alvara, total_repasse_alvara, custas_banco, ho_escritorio, ho_politica, total_acordo

**Estimativa Venda** (3 campos):
- cadin, valor_molicar, honorarios

**Total**: 46 campos extraídos

---

## 📁 Estrutura do Projeto

```
rpa_safra/
├── src/
│   ├── processar_lote.py      # Script principal
│   ├── testar_webhook.py       # Teste de webhook
│   └── capturar_coordenadas.py # Utilitário de coordenadas
├── input/                      # Coloque arquivos CSV aqui
├── output/                     # Resultados processados
├── logs/                       # Logs de execução
├── downloads/                  # PDFs baixados (se houver)
├── coordenadas.json           # Coordenadas salvas (gerado automaticamente)
├── .env                       # Credenciais (criar manualmente)
├── .env.example               # Exemplo de configuração
├── requirements.txt           # Dependências Python
├── README.md                  # Documentação principal
└── MANUAL_INSTALACAO.md       # Este arquivo
```

---

## 🔧 Solução de Problemas

### Erro: "ModuleNotFoundError"
**Causa**: Dependências não instaladas
**Solução**:
```bash
py -m pip install -r requirements.txt
```

### Erro: "pip não é reconhecido"
**Causa**: Python não está no PATH
**Solução**: Use `py -m pip` em vez de apenas `pip`

### Erro: "Coordenadas incorretas"
**Causa**: Resolução da tela mudou ou coordenadas erradas
**Solução**: Delete o arquivo `coordenadas.json` e capture novamente

### Chrome/ChromeDriver não funciona
**Causa**: Versão incompatível do Chrome
**Solução**: 
1. Atualize o Chrome para última versão
2. O `webdriver-manager` baixará o driver correto automaticamente

### Sistema não detecta CPF encontrado
**Causa**: Layout do site mudou ou elemento não carregou
**Solução**:
1. Aumente o `BROWSER_TIMEOUT` no `.env` para 60
2. Verifique se o site está acessível manualmente
3. Recapture as coordenadas

### Webhook não recebe dados
**Causa**: URL incorreta ou webhook offline
**Solução**:
1. Teste o webhook com: `py src/testar_webhook.py`
2. Verifique a URL no arquivo `processar_lote.py`
3. Confirme que o N8N está rodando

### CSV não é encontrado
**Causa**: Arquivo não está na pasta `input/`
**Solução**:
1. Coloque o arquivo `.csv` ou `.txt` na pasta `input/`
2. Verifique o formato: separador `;` e colunas corretas

### Proposta NEGADA não captura dados
**Causa**: Faltam as 4 coordenadas de clique
**Solução**:
1. Delete as coordenadas de negado no `coordenadas.json`:
```json
"negado_click1": ...,
"negado_click2": ...,
"negado_click3": ...,
"negado_click4": ...
```
2. Execute novamente e capture os 4 cliques quando solicitado

---

## 📞 Suporte

**Repositório**: https://github.com/sh4rck3/rpa_safra
**Issues**: https://github.com/sh4rck3/rpa_safra/issues

---

## 📝 Notas Importantes

1. **Sessão Única**: O sistema mantém uma única sessão de login. Se desconectar, precisará reiniciar.

2. **Resolução de Tela**: As coordenadas são baseadas na resolução da tela. Se mudar a resolução ou usar outro monitor, recapture as coordenadas.

3. **Retry Automático**: Cada CPF tem 3 tentativas automáticas em caso de erro.

4. **Logs**: Todos os processamentos são registrados em `logs/execucao_YYYYMMDD.log`

5. **Backup**: O sistema não modifica o arquivo de entrada, apenas gera novos arquivos em `output/`

6. **Webhook Opcional**: O sistema funciona sem webhook, apenas não enviará dados para N8N.

---

**Última atualização**: 25/11/2025
**Versão**: 1.0.0
