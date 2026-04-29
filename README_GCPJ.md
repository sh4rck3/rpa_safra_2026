# RPA GCPJ - Sistema de Processamento em Lote

## 📋 Descrição

Sistema RPA para automatizar o acesso e processamento de dados no sistema GCPJ via extensão do Chrome.

**Diferencial:** Acessa o GCPJ através da extensão do Chrome ao invés de login tradicional.

## 🎯 Funcionalidades

- ✅ **Acesso via extensão do Chrome** - clica na extensão e seleciona GCPJ
- ✅ **Processamento em lote** - múltiplos CPFs/CNPJs
- ✅ **Sistema de coordenadas** - navegação resiliente
- ✅ **Logs detalhados** - acompanhamento completo
- ✅ **Relatórios CSV** - resultados organizados

## 🚀 Como Usar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Capturar Coordenadas (PRIMEIRA VEZ)

```bash
python src/gcpj_capturar_coordenadas.py
```

**Siga as instruções na tela:**
1. Abra o Chrome quando solicitado
2. Posicione o mouse sobre cada elemento pedido
3. Pressione ENTER para capturar
4. Coordenadas são salvas em `coordenadas_gcpj.json`

**Elementos a capturar:**
- ✓ Ícone da extensão GCPJ no Chrome
- ✓ Campo de busca/input da extensão
- ✓ Item "GCPJ" no menu suspenso

### 3. Preparar Arquivo de Entrada

Crie um arquivo CSV na pasta `input/`:

```csv
CONTRATO;NOME;CPFCNPJ
123456;JOAO DA SILVA;12345678901
789012;MARIA SANTOS;98765432100
```

### 4. Executar Processamento

```bash
python src/gcpj_processar_lote.py
```

## 📁 Estrutura

```
rpa_gcpj/
├── src/
│   ├── gcpj_capturar_coordenadas.py   # Captura coordenadas
│   ├── gcpj_processar_lote.py         # Processamento em lote
│   └── ... (outros scripts Safra)
├── input/                              # Arquivos CSV de entrada
├── output/                             # Relatórios de resultado
├── logs/                               # Logs de execução
├── coordenadas_gcpj.json              # Coordenadas salvas
└── README_GCPJ.md                     # Esta documentação
```

## 🔧 Status do Desenvolvimento

- ✅ Script de captura de coordenadas
- ✅ Estrutura base do processamento
- ✅ Acesso via extensão do Chrome
- ⏳ Lógica de processamento específica do GCPJ (próximo passo)

## 📝 Próximos Passos

1. Abra o sistema GCPJ via extensão
2. Identifique os elementos a serem capturados:
   - Campo de busca CPF/CNPJ
   - Botão pesquisar
   - Elementos de extração de dados
   - Botões de navegação
3. Execute novamente `gcpj_capturar_coordenadas.py` para adicionar novos elementos
4. Implemente a lógica em `processar_cpf()` no arquivo `gcpj_processar_lote.py`

## ⚠️ Importante

- Execute o Chrome **maximizado**
- A extensão GCPJ deve estar instalada e visível
- As coordenadas variam conforme resolução da tela
- Recapture coordenadas se mudar resolução ou monitores

## 🆘 Troubleshooting

| Problema | Solução |
|----------|---------|
| Coordenadas não funcionam | Execute `gcpj_capturar_coordenadas.py` novamente |
| Extensão não abre | Verifique se está instalada e visível |
| Chrome não maximiza | Ajuste manualmente antes de executar |
| Menu suspenso não aparece | Aguarde mais tempo após digitar "GCPJ" |

## 📞 Suporte

- Verifique os logs em `logs/gcpj_execucao_*.log`
- Teste as coordenadas manualmente com PyAutoGUI
- Recapture coordenadas em caso de problemas
