"""
Sistema de Processamento em Lote - GCPJ
========================================

Processa múltiplos CPFs/CNPJs do sistema GCPJ usando automação web.
Utiliza coordenadas de tela para navegação resiliente.

Fluxo:
1. Abre Chrome
2. Acessa GCPJ via extensão do Chrome
3. Processa cada CPF do arquivo CSV
4. Extrai dados e envia para webhook
5. Gera relatório final
"""

import os
import json
import time
import pyautogui
import pyperclip
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# ============================================================
# CONFIGURAÇÕES
# ============================================================

# Arquivo de coordenadas
ARQUIVO_COORDENADAS = Path(__file__).parent.parent / "coordenadas_gcpj.json"

# Pastas do projeto
PASTA_INPUT = Path(__file__).parent.parent / "input"
PASTA_OUTPUT = Path(__file__).parent.parent / "output"
PASTA_LOGS = Path(__file__).parent.parent / "logs"
PASTA_DOWNLOADS = Path(__file__).parent.parent / "downloads"

# Criar pastas se não existirem
PASTA_INPUT.mkdir(exist_ok=True)
PASTA_OUTPUT.mkdir(exist_ok=True)
PASTA_LOGS.mkdir(exist_ok=True)
PASTA_DOWNLOADS.mkdir(exist_ok=True)

# Configurações do .env
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "30"))

# Desabilitar failsafe
pyautogui.FAILSAFE = False

# ============================================================
# VARIÁVEIS GLOBAIS
# ============================================================

driver = None
coordenadas = {}
log_file = None

# ============================================================
# FUNÇÕES DE LOG
# ============================================================

def log(mensagem: str, nivel: str = "INFO"):
    """Registra mensagem no console e arquivo de log."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    linha = f"[{timestamp}] [{nivel}] {mensagem}"
    print(linha)
    
    if log_file:
        log_file.write(linha + "\n")
        log_file.flush()

def log_separador(titulo: str = ""):
    """Cria separador visual no log."""
    if titulo:
        log("=" * 60)
        log(titulo)
        log("=" * 60)
    else:
        log("=" * 60)

# ============================================================
# FUNÇÕES DE COORDENADAS
# ============================================================

def carregar_coordenadas():
    """Carrega coordenadas do arquivo JSON."""
    global coordenadas
    
    if not ARQUIVO_COORDENADAS.exists():
        log(f"❌ Arquivo de coordenadas não encontrado: {ARQUIVO_COORDENADAS}", "ERROR")
        log("⚠️  Execute primeiro: python src/gcpj_capturar_coordenadas.py", "ERROR")
        raise FileNotFoundError(f"Coordenadas não encontradas. Execute o script de captura primeiro.")
    
    with open(ARQUIVO_COORDENADAS, "r", encoding="utf-8") as f:
        coordenadas = json.load(f)
    
    log(f"✅ Coordenadas carregadas: {len(coordenadas)} elementos")

def click_coord(nome_elemento: str, delay: float = 1.0):
    """
    Clica em uma coordenada específica.
    
    Args:
        nome_elemento: Nome do elemento nas coordenadas
        delay: Tempo de espera após o clique (segundos)
    """
    if nome_elemento not in coordenadas:
        raise KeyError(f"Coordenada '{nome_elemento}' não encontrada!")
    
    coord = coordenadas[nome_elemento]
    log(f"🖱️  Clicando em: {nome_elemento} (X={coord['x']}, Y={coord['y']})")
    
    pyautogui.click(coord["x"], coord["y"])
    time.sleep(delay)

# ============================================================
# FUNÇÕES DO CHROME
# ============================================================

def iniciar_chrome():
    """Inicializa o navegador Chrome."""
    global driver
    
    log("🌐 Iniciando Chrome com perfil dedicado...")
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Perfil dedicado para o Selenium (mesma pasta usada na captura)
    profile_dir = Path(__file__).parent.parent / "chrome_profile"
    profile_dir.mkdir(exist_ok=True)
    chrome_options.add_argument(f"--user-data-dir={profile_dir.absolute()}")
    
    log(f"📁 Perfil: {profile_dir}")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    log("✅ Chrome iniciado")
    time.sleep(2)

def acessar_gcpj():
    """Acessa o sistema GCPJ via extensão do Chrome."""
    log_separador("ACESSANDO GCPJ VIA EXTENSÃO")
    
    # Abre uma página em branco
    log("📄 Abrindo Chrome...")
    driver.get("about:blank")
    time.sleep(2)
    
    # Passo 1: Clicar na extensão
    log("🔌 Clicando na extensão GCPJ...")
    click_coord("extensao_chrome", delay=1.5)
    
    # Passo 2: Clicar no campo de busca
    log("🔍 Clicando no campo de busca...")
    click_coord("input_busca", delay=0.5)
    
    # Passo 3: Digitar GCPJ
    log("⌨️  Digitando 'GCPJ'...")
    pyautogui.write("GCPJ", interval=0.1)
    time.sleep(1.5)
    
    # Passo 4: Clicar no item do menu
    log("📋 Selecionando GCPJ no menu...")
    click_coord("item_gcpj_menu", delay=3.0)
    
    log("✅ Acesso ao GCPJ realizado")
    log("⏳ Aguardando carregamento do sistema...")
    time.sleep(5)

# ============================================================
# FUNÇÕES DE PROCESSAMENTO
# ============================================================

def processar_cpf(cpf: str, nome: str, contrato: str):
    """
    Processa um CPF/CNPJ no sistema GCPJ.
    
    Args:
        cpf: CPF/CNPJ a ser processado
        nome: Nome do cliente
        contrato: Número do contrato
    
    Returns:
        dict com resultado do processamento
    """
    log_separador(f"PROCESSANDO: {cpf} - {nome}")
    
    try:
        # TODO: Implementar lógica de processamento do GCPJ
        # Aqui você vai adicionar as coordenadas específicas do GCPJ:
        # - Campo de busca CPF
        # - Botão pesquisar
        # - Extração de dados
        # - etc.
        
        log("⚠️  Função processar_cpf() ainda não implementada")
        log("💡 Execute novamente gcpj_capturar_coordenadas.py para capturar mais elementos")
        
        return {
            "status": "PENDENTE",
            "mensagem": "Processamento ainda não implementado",
            "cpf": cpf,
            "dados": None
        }
        
    except Exception as e:
        log(f"❌ Erro ao processar CPF {cpf}: {e}", "ERROR")
        return {
            "status": "ERROR",
            "mensagem": str(e),
            "cpf": cpf,
            "dados": None
        }

def processar_lote(arquivo_csv: Path):
    """
    Processa um lote de CPFs do arquivo CSV.
    
    Args:
        arquivo_csv: Caminho do arquivo CSV com os CPFs
    """
    log_separador(f"INICIANDO PROCESSAMENTO EM LOTE")
    log(f"📄 Arquivo: {arquivo_csv.name}")
    
    # Ler arquivo CSV
    with open(arquivo_csv, "r", encoding="utf-8") as f:
        linhas = f.readlines()
    
    # Processar cabeçalho
    if not linhas:
        log("❌ Arquivo vazio!", "ERROR")
        return
    
    cabecalho = linhas[0].strip()
    dados = [linha.strip().split(";") for linha in linhas[1:] if linha.strip()]
    
    log(f"📊 Total de registros: {len(dados)}")
    
    # Processar cada CPF
    resultados = []
    
    for idx, registro in enumerate(dados, 1):
        if len(registro) < 3:
            log(f"⚠️  Registro {idx} inválido (faltam colunas): {registro}", "WARNING")
            continue
        
        contrato, nome, cpf = registro[0], registro[1], registro[2]
        
        log(f"\n📋 [{idx}/{len(dados)}] Processando: {cpf}")
        
        resultado = processar_cpf(cpf, nome, contrato)
        resultados.append({
            "contrato": contrato,
            "nome": nome,
            "cpf": cpf,
            **resultado
        })
        
        time.sleep(2)  # Delay entre processamentos
    
    # Gerar relatório
    gerar_relatorio(resultados, arquivo_csv.stem)
    
    log_separador("PROCESSAMENTO CONCLUÍDO")
    log(f"✅ Total processado: {len(resultados)}")

def gerar_relatorio(resultados: list, nome_base: str):
    """Gera arquivo CSV com relatório do processamento."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_saida = PASTA_OUTPUT / f"{nome_base}_processado_{timestamp}.csv"
    
    log(f"💾 Gerando relatório: {arquivo_saida.name}")
    
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write("CONTRATO;NOME;CPFCNPJ;STATUS;MENSAGEM\n")
        
        for r in resultados:
            linha = f"{r['contrato']};{r['nome']};{r['cpf']};{r['status']};{r['mensagem']}\n"
            f.write(linha)
    
    log(f"✅ Relatório salvo: {arquivo_saida}")

# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main():
    """Função principal do processamento em lote."""
    global log_file
    
    # Configurar log
    timestamp = datetime.now().strftime("%Y%m%d")
    arquivo_log = PASTA_LOGS / f"gcpj_execucao_{timestamp}.log"
    log_file = open(arquivo_log, "a", encoding="utf-8")
    
    log_separador("🚀 INICIANDO SISTEMA RPA GCPJ")
    log(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    try:
        # Carregar coordenadas
        carregar_coordenadas()
        
        # Iniciar Chrome
        iniciar_chrome()
        
        # Acessar GCPJ
        acessar_gcpj()
        
        # Buscar arquivo de entrada
        arquivos = list(PASTA_INPUT.glob("*.txt")) + list(PASTA_INPUT.glob("*.csv"))
        
        if not arquivos:
            log("❌ Nenhum arquivo encontrado em input/", "ERROR")
            log("💡 Crie um arquivo CSV/TXT com os CPFs a processar", "INFO")
            return
        
        arquivo = arquivos[0]
        log(f"📂 Arquivo encontrado: {arquivo.name}")
        
        # Processar lote
        processar_lote(arquivo)
        
    except Exception as e:
        log(f"❌ ERRO CRÍTICO: {e}", "ERROR")
        import traceback
        traceback.print_exc()
    
    finally:
        log_separador("🏁 FINALIZANDO")
        
        if driver:
            log("🔴 Fechando Chrome...")
            driver.quit()
        
        if log_file:
            log_file.close()
        
        log("✅ Sistema finalizado")

if __name__ == "__main__":
    main()
