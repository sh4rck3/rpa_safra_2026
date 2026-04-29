#!/usr/bin/env python3
"""
Script de processamento em lote de CPFs
Lê arquivo CSV da pasta input/, processa cada CPF e salva resultado em output/
"""

import os
import time
import json
import csv
import re
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# Constantes
COORDENADAS_FILE = Path('coordenadas.json')
INPUT_DIR = Path('input')
OUTPUT_DIR = Path('output')
DOWNLOADS_DIR = Path('downloads')
LOGS_DIR = Path('logs')
WEBHOOK_URL = "http://10.9.0.11:5678/webhook/c4affbf4-e187-4320-acc0-bd69476cd47b"
MAX_TENTATIVAS = 3


def carregar_coordenadas():
    """Carrega coordenadas salvas anteriormente."""
    if COORDENADAS_FILE.exists():
        with open(COORDENADAS_FILE, 'r') as f:
            return json.load(f)
    return {}


def salvar_coordenadas(coordenadas):
    """Salva coordenadas para uso futuro."""
    with open(COORDENADAS_FILE, 'w') as f:
        json.dump(coordenadas, f, indent=2)
    print(f"   💾 Coordenadas salvas em {COORDENADAS_FILE}")


def registrar_log(mensagem):
    """Registra mensagem no arquivo de log."""
    LOGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"execucao_{datetime.now().strftime('%Y%m%d')}.log"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {mensagem}\n")


def capturar_posicao(nome_elemento, pyautogui, coordenadas_salvas, chave_json):
    """Captura posição do mouse ou usa coordenada salva."""
    if chave_json in coordenadas_salvas:
        x = coordenadas_salvas[chave_json]['x']
        y = coordenadas_salvas[chave_json]['y']
        print(f"   ✓ Usando posição salva: X={x}, Y={y}")
        return x, y
    
    print(f"\n" + "=" * 60)
    print(f"CAPTURA DE POSIÇÃO: {nome_elemento.upper()}")
    print("=" * 60)
    print("\nInstruções:")
    print(f"1. Posicione o mouse SOBRE {nome_elemento}")
    print(f"2. DEIXE o mouse parado lá")
    print(f"3. Aguarde a contagem regressiva")
    print("\nIniciando captura em 3 segundos...")
    time.sleep(3)
    
    print("\nCapturando posição em 5 segundos...")
    print(f"POSICIONE O MOUSE AGORA!")
    
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    
    x, y = pyautogui.position()
    print(f"\n✓ Posição capturada: X={x}, Y={y}")
    
    return x, y


def ler_cpfs_csv(arquivo_csv):
    """Lê arquivo CSV e retorna lista de linhas com CPFs."""
    linhas = []
    
    with open(arquivo_csv, 'r', encoding='utf-8') as f:
        # Detectar delimitador (ponto e vírgula)
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            # Coluna CPFCNPJ é a terceira coluna
            cpf = row.get('CPFCNPJ', '').strip()
            if cpf:
                linhas.append({
                    'contrato': row.get('CONTRATO', ''),
                    'nome': row.get('NOME', ''),
                    'cpf': cpf,
                    'status': '',
                    'mensagem': ''
                })
    
    return linhas


def salvar_csv_resultado(arquivo_saida, linhas):
    """Salva resultado processado em CSV."""
    with open(arquivo_saida, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['CONTRATO', 'NOME', 'CPFCNPJ', 'STATUS', 'MENSAGEM']
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        
        writer.writeheader()
        for linha in linhas:
            writer.writerow({
                'CONTRATO': linha['contrato'],
                'NOME': linha['nome'],
                'CPFCNPJ': linha['cpf'],
                'STATUS': linha['status'],
                'MENSAGEM': linha['mensagem']
            })


def enviar_webhook(success, cpf, data=None, error=None):
    """Envia dados para o webhook do n8n."""
    agora = datetime.now()
    payload = {
        "success": success,
        "cpf": cpf,
        "data": data,
        "timestamp": agora.strftime("%Y-%m-%d %H:%M:%S"),
        "data_processamento": agora.strftime("%Y-%m-%d"),
        "hora_processamento": agora.strftime("%H:%M:%S"),
        "error": error
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        response.raise_for_status()
        print(f"   ✓ Webhook enviado com sucesso (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"   ⚠️ Erro ao enviar webhook: {e}")
        return False


def setup_driver():
    """Configura o driver do Chrome."""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--start-maximized')
    
    download_path = DOWNLOADS_DIR.absolute()
    prefs = {
        'download.default_directory': str(download_path),
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'plugins.always_open_pdf_externally': True
    }
    chrome_options.add_experimental_option('prefs', prefs)
    
    print("📦 Instalando/atualizando ChromeDriver...")
    driver_path = ChromeDriverManager().install()
    
    if not driver_path.endswith('.exe'):
        driver_dir = os.path.dirname(driver_path)
        possible_paths = [
            os.path.join(driver_dir, 'chromedriver.exe'),
            os.path.join(driver_dir, 'chromedriver-win32', 'chromedriver.exe'),
            os.path.join(os.path.dirname(driver_dir), 'chromedriver.exe'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                driver_path = path
                break
    
    print(f"   ✓ Driver instalado em: {driver_path}")
    
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver


def fazer_login(driver, wait, username, password):
    """Realiza login no sistema."""
    print("\n🔐 Fazendo login...")
    
    username_field = wait.until(
        EC.presence_of_element_located((By.ID, 'Username'))
    )
    username_field.clear()
    username_field.send_keys(username)
    time.sleep(0.5)
    
    password_field = driver.find_element(By.ID, 'Password')
    password_field.clear()
    password_field.send_keys(password)
    time.sleep(0.5)
    
    submit_button = driver.find_element(By.CSS_SELECTOR, 'button.btn-login[type="submit"]')
    submit_button.click()
    time.sleep(5)
    
    print("   ✓ Login realizado!")


def navegar_tela_pesquisa(driver, wait):
    """Navega até a tela de Pesquisa de Contratos."""
    print("\n📋 Navegando para tela de Pesquisa...")
    
    try:
        # Clicar no dropdown Propostas
        dropdown_propostas = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Propostas")]/parent::a'))
        )
        dropdown_propostas.click()
        time.sleep(2)
        
        # Clicar em Pesquisa
        pesquisa_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//a[@href="/FinanceiraVeiculos/Seguranca/Proposta/Pesquisa"]'))
        )
        pesquisa_link.click()
        time.sleep(3)
        
        print("   ✓ Tela de Pesquisa aberta!")
    except Exception as e:
        print(f"   ⚠️  Erro ao navegar para Pesquisa: {e}")
        print("   ℹ️  Pode já estar na tela de pesquisa")


def navegar_nova_proposta(driver, wait):
    """Navega até a tela de Nova Proposta."""
    print("\n📋 Navegando para Nova Proposta...")
    
    # Clicar no dropdown Propostas
    dropdown_propostas = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Propostas")]/parent::a'))
    )
    dropdown_propostas.click()
    time.sleep(2)
    
    # Clicar em Nova Proposta
    nova_proposta = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//a[@href="/FinanceiraVeiculos/Seguranca/Proposta/Manutencao"]'))
    )
    nova_proposta.click()
    time.sleep(3)
    
    print("   ✓ Tela de Nova Proposta aberta!")


def parse_tabela_resultados_selenium(driver, wait, cpf):
    """
    DESABILITADO - Parse via Ctrl+A será usado no fluxo principal
    """
    return {"return_direct": False}


def parse_tabela_ctrl_a(conteudo_raw, cpf):
    """
    Parse do conteúdo capturado via Ctrl+A + Ctrl+C.
    
    Formato esperado (separado por TABs):
    Contrato \t Nome \t Data do Acordo \t Escritório \t CPF/CNPJ \t Valor do Acordo \t 
    Atraso (Dias) \t Saldo Contábil \t Alçada Saída \t Data Agendamento \t Status
    
    Retorna:
    - dict com return_direct=True se for ACORDO FORMALIZADO (múltiplas linhas)
    - dict com return_direct=False para continuar fluxo normal
    """
    from datetime import datetime
    
    print("\n   🔍 Analisando conteúdo capturado via Ctrl+A...")
    
    linhas = conteudo_raw.split('\n')
    linhas_dados = []
    
    # Procurar linhas que contenham dados da tabela (após "Resultado da Pesquisa")
    encontrou_header = False
    for linha in linhas:
        linha_limpa = linha.strip()
        
        # Detectar início da tabela
        if "Resultado da Pesquisa" in linha_limpa:
            encontrou_header = True
            continue
        
        # Pular linha de cabeçalho (contém "Contrato \t Nome \t Data...")
        if encontrou_header and "Contrato" in linha_limpa and "Nome" in linha_limpa:
            print("   ✓ Cabeçalho da tabela encontrado")
            continue
        
        # Procurar linhas de dados (começam com número de contrato)
        if encontrou_header and linha_limpa:
            # Split por TAB
            colunas = linha_limpa.split('\t')
            
            # Verificar se é linha de dados (tem número de contrato + pelo menos 8 colunas)
            if len(colunas) >= 10 and re.match(r'\d{5}', colunas[0]):
                linhas_dados.append(colunas)
                print(f"   📌 Linha encontrada: Contrato={colunas[0]}, Data={colunas[2] if len(colunas) > 2 else 'N/A'}")
    
    qtd_linhas = len(linhas_dados)
    print(f"\n   📋 Total de linhas de dados encontradas: {qtd_linhas}")
    
    # Se não encontrou linhas, retorna para continuar fluxo normal
    if qtd_linhas == 0:
        print("   ⚠️  Nenhuma linha detectada, continuando fluxo normal...")
        return {"return_direct": False, "atraso_dias": "", "saldo_contabil": ""}
    
    # Se tem apenas 1 linha, extrai dados e continua fluxo normal
    if qtd_linhas == 1:
        print("   ℹ️  Apenas 1 linha encontrada, extraindo dados...")
        colunas = linhas_dados[0]
        atraso_dias = colunas[6].strip() if len(colunas) > 6 else ""
        saldo_contabil = colunas[7].strip() if len(colunas) > 7 else ""
        print(f"   📊 Atraso (Dias): {atraso_dias}")
        print(f"   💰 Saldo Contábil: {saldo_contabil}")
        return {"return_direct": False, "atraso_dias": atraso_dias, "saldo_contabil": saldo_contabil}
    
    # ============================================================
    # MÚLTIPLAS LINHAS: Encontrar linha com data mais recente
    # ============================================================
    print(f"\n   ⚠️  MÚLTIPLAS LINHAS detectadas ({qtd_linhas} linhas)!")
    print("   📅 Procurando linha com data mais recente...")
    
    linha_mais_recente = None
    data_mais_recente = None
    dados_linha_recente = {}
    
    for idx, colunas in enumerate(linhas_dados):
        try:
            # Extrair dados (índices conforme formato da tabela)
            contrato = colunas[0].strip() if len(colunas) > 0 else ""
            nome = colunas[1].strip() if len(colunas) > 1 else ""
            data_acordo = colunas[2].strip() if len(colunas) > 2 else ""
            escritorio = colunas[3].strip() if len(colunas) > 3 else ""
            cpf_cnpj = colunas[4].strip() if len(colunas) > 4 else cpf
            valor_acordo = colunas[5].strip() if len(colunas) > 5 else ""
            atraso_dias = colunas[6].strip() if len(colunas) > 6 else ""
            saldo_contabil = colunas[7].strip() if len(colunas) > 7 else ""
            alcada_saida = colunas[8].strip() if len(colunas) > 8 else ""
            data_agendamento = colunas[9].strip() if len(colunas) > 9 else ""
            status = colunas[10].strip() if len(colunas) > 10 else ""
            
            # Parse da data (formato dd/mm/yyyy)
            if re.match(r'\d{2}/\d{2}/\d{4}', data_acordo):
                data_obj = datetime.strptime(data_acordo, "%d/%m/%Y")
                
                if data_mais_recente is None or data_obj > data_mais_recente:
                    data_mais_recente = data_obj
                    linha_mais_recente = colunas
                    dados_linha_recente = {
                        "contrato": contrato,
                        "nome": nome,
                        "data_acordo": data_acordo,
                        "escritorio": escritorio,
                        "cpf_cnpj": cpf_cnpj,
                        "valor_acordo": valor_acordo,
                        "atraso_dias": atraso_dias,
                        "saldo_contabil": saldo_contabil,
                        "alcada_saida": alcada_saida,
                        "data_agendamento": data_agendamento,
                        "status": status
                    }
                
                print(f"      Linha {idx+1}: Data {data_acordo} | Status: {status}")
        except Exception as e:
            print(f"      ⚠️  Erro ao processar linha {idx+1}: {e}")
            continue
    
    if linha_mais_recente is None:
        print("   ⚠️  Não foi possível identificar data mais recente, continuando fluxo normal...")
        return {"return_direct": False, "atraso_dias": "", "saldo_contabil": ""}
    
    print(f"\n   ✓ Linha mais recente identificada:")
    print(f"      Data: {dados_linha_recente['data_acordo']}")
    print(f"      Status: {dados_linha_recente['status']}")
    print(f"      Contrato: {dados_linha_recente['contrato']}")
    print(f"\n   ℹ️  Continuando fluxo normal para abrir proposta...")
    
    return {"return_direct": False, "atraso_dias": dados_linha_recente['atraso_dias'], "saldo_contabil": dados_linha_recente['saldo_contabil']}
    """
    Extrai dados da tabela de resultados usando Selenium.
    
    Colunas esperadas:
    [0] Contrato | [1] Nome | [2] Data do Acordo | [3] Escritório | [4] CPF/CNPJ | 
    [5] Valor do Acordo | [6] Atraso (Dias) | [7] Saldo Contábil | [8] Alçada Saída | 
    [9] Data Agendamento | [10] Status
    
    Retorna:
    - dict com return_direct=True se for ACORDO FORMALIZADO (múltiplas linhas)
    - dict com return_direct=False para continuar fluxo normal
    """
    from datetime import datetime
    
    print("\n   🔍 Analisando tabela de resultados via Selenium...")
    
    try:
        # Aguardar tabela aparecer
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(1)
        
        # Pegar elemento table
        tabela = driver.find_element(By.TAG_NAME, "table")
        
        # Pegar todas as linhas <tr>
        todas_linhas = tabela.find_elements(By.TAG_NAME, "tr")
        
        # Filtrar linhas de dados (ignora header)
        linhas_dados = []
        for idx, linha in enumerate(todas_linhas):
            # Verificar se é linha de dados (tem <td>, não <th>)
            colunas_td = linha.find_elements(By.TAG_NAME, "td")
            if len(colunas_td) >= 10:  # Deve ter pelo menos 10 colunas
                linhas_dados.append(linha)
        
        qtd_linhas = len(linhas_dados)
        print(f"   📋 Linhas de dados encontradas: {qtd_linhas}")
        
        # Se não encontrou linhas, retorna para continuar fluxo normal
        if qtd_linhas == 0:
            print("   ⚠️  Nenhuma linha detectada, continuando fluxo normal...")
            return {"return_direct": False}
        
        # Se tem apenas 1 linha, continua fluxo normal
        if qtd_linhas == 1:
            print("   ℹ️  Apenas 1 linha encontrada, continuando fluxo normal...")
            return {"return_direct": False}
        
        # ============================================================
        # MÚLTIPLAS LINHAS: Encontrar linha com data mais recente
        # ============================================================
        print(f"   ⚠️  MÚLTIPLAS LINHAS detectadas ({qtd_linhas} linhas)!")
        print("   📅 Procurando linha com data mais recente...")
        
        linha_mais_recente = None
        data_mais_recente = None
        dados_linha_recente = {}
        
        for idx, linha in enumerate(linhas_dados):
            try:
                colunas = linha.find_elements(By.TAG_NAME, "td")
                
                # Extrair dados
                contrato = colunas[0].text.strip() if len(colunas) > 0 else ""
                nome = colunas[1].text.strip() if len(colunas) > 1 else ""
                data_acordo = colunas[2].text.strip() if len(colunas) > 2 else ""
                cpf_cnpj = colunas[4].text.strip() if len(colunas) > 4 else cpf
                valor_acordo = colunas[5].text.strip() if len(colunas) > 5 else ""
                atraso_dias = colunas[6].text.strip() if len(colunas) > 6 else ""
                saldo_contabil = colunas[7].text.strip() if len(colunas) > 7 else ""
                status = colunas[10].text.strip() if len(colunas) > 10 else ""
                
                # Parse da data (formato dd/mm/yyyy)
                if re.match(r'\d{2}/\d{2}/\d{4}', data_acordo):
                    data_obj = datetime.strptime(data_acordo, "%d/%m/%Y")
                    
                    if data_mais_recente is None or data_obj > data_mais_recente:
                        data_mais_recente = data_obj
                        linha_mais_recente = linha
                        dados_linha_recente = {
                            "contrato": contrato,
                            "nome": nome,
                            "data_acordo": data_acordo,
                            "cpf_cnpj": cpf_cnpj,
                            "valor_acordo": valor_acordo,
                            "atraso_dias": atraso_dias,
                            "saldo_contabil": saldo_contabil,
                            "status": status
                        }
                    
                    print(f"      Linha {idx+1}: Data {data_acordo} | Status: {status}")
            except Exception as e:
                print(f"      ⚠️  Erro ao processar linha {idx+1}: {e}")
                continue
        
        if linha_mais_recente is None:
            print("   ⚠️  Não foi possível identificar data mais recente, continuando fluxo normal...")
            return {"return_direct": False}
        
        print(f"\n   ✓ Linha mais recente identificada:")
        print(f"      Data: {dados_linha_recente['data_acordo']}")
        print(f"      Status: {dados_linha_recente['status']}")
        print(f"      Contrato: {dados_linha_recente['contrato']}")
        
        # ============================================================
        # Verificar STATUS
        # ============================================================
        status_upper = dados_linha_recente['status'].upper()
        
        if "ACORDO FORMALIZADO" in status_upper and "CUMPRIMENTO" in status_upper:
            print(f"\n   🎯 STATUS = ACORDO FORMALIZADO (EM CUMPRIMENTO)")
            print(f"   ℹ️  Retornando dados direto SEM abrir Nova Proposta")
            
            return {
                "return_direct": True,
                "success": True,
                "error": None,
                "data": {
                    "cliente": {
                        "nome": dados_linha_recente['nome'],
                        "tipo_proposta": "",
                        "correntista_safra": "",
                        "cpf": dados_linha_recente['cpf_cnpj'],
                        "produto": "",
                        "endereco": "",
                        "cep": "",
                        "cidade": "",
                        "uf": "",
                        "resultado": dados_linha_recente['status']
                    },
                    "veiculo": {},
                    "operacao": {
                        "contrato": dados_linha_recente['contrato'],
                        "data_contrato": dados_linha_recente['data_acordo'],
                        "valor_compra": dados_linha_recente['valor_acordo'],
                        "plano": "",
                        "valor_parcelas_pagas": "",
                        "quantidade_parcelas_pagas": "",
                        "dias_atraso": dados_linha_recente['atraso_dias'],
                        "data_parcela_vencida": "",
                        "saldo_contabil": dados_linha_recente['saldo_contabil'],
                        "saldo_gerencial": "",
                        "saldo_principal": "",
                        "saldo_contabil_cdi": "",
                        "plano_balao": ""
                    },
                    "resumo_proposta": {},
                    "estimativa_venda": {}
                }
            }
        
        # Outros status: continua fluxo normal (mas clica na linha mais recente)
        print(f"\n   ℹ️  Status '{dados_linha_recente['status']}' - continuando fluxo normal")
        print(f"   🖱️  Clicando na linha mais recente...")
        
        # Clicar na linha mais recente
        try:
            linha_mais_recente.click()
            time.sleep(1)
            print(f"   ✓ Linha clicada com sucesso!")
        except Exception as e:
            print(f"   ⚠️  Erro ao clicar na linha: {e}")
        
        return {"return_direct": False}
        
    except Exception as e:
        print(f"   ⚠️  Erro ao analisar tabela via Selenium: {e}")
        print(f"   ℹ️  Continuando fluxo normal...")
        return {"return_direct": False}


def processar_cpf(driver, wait, pyautogui, coordenadas, cpf):
    """Processa um CPF específico e retorna os dados extraídos."""
    print(f"\n{'='*60}")
    print(f"PROCESSANDO CPF: {cpf}")
    print(f"{'='*60}")
    
    try:
        # 🔄 Trazer Chrome para frente antes de qualquer interação
        print("   🔄 Trazendo Chrome para frente...")
        try:
            driver.switch_to.window(driver.current_window_handle)
            time.sleep(0.5)
        except Exception:
            pass
        
        # 🔄 FIX: Recarregar página para começar limpo (F5)
        print("   🔄 Recarregando página (F5) para começar limpo...")
        pyautogui.press('f5')
        time.sleep(3)
        print("   ✓ Página recarregada")
        
        # Verificar se o campo de CPF existe
        if 'campo_cpf' not in coordenadas:
            raise Exception("Coordenada 'campo_cpf' não encontrada! Execute captura de coordenadas primeiro.")
        
        # Preencher CPF com digitação humana
        print(f"   📝 Preenchendo CPF no campo...")
        cpf_x, cpf_y = coordenadas['campo_cpf']['x'], coordenadas['campo_cpf']['y']
        
        # Clicar no campo CPF/CNPJ
        pyautogui.click(cpf_x, cpf_y)
        time.sleep(0.5)
        
        # Limpar campo
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.press('delete')
        time.sleep(0.3)
        
        # Digitar CPF como humano (delay aleatório entre teclas)
        import random
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        for digit in cpf_limpo:
            pyautogui.write(digit, interval=0)
            time.sleep(random.uniform(0.05, 0.18))
        time.sleep(0.5)
        print(f"   ✓ CPF '{cpf_limpo}' digitado (humano)")
        
        # Verificar se o botão Pesquisar existe
        if 'botao_pesquisar' not in coordenadas:
            raise Exception("Coordenada 'botao_pesquisar' não encontrada! Execute captura de coordenadas primeiro.")
        
        # Clicar em Pesquisar
        print(f"   🔍 Clicando em Pesquisar...")
        pesquisar_x, pesquisar_y = coordenadas['botao_pesquisar']['x'], coordenadas['botao_pesquisar']['y']
        pyautogui.click(pesquisar_x, pesquisar_y)
        time.sleep(3)
        print(f"   ✓ Pesquisa executada")
        
        # ============================================================
        # NOVA LÓGICA: Capturar e imprimir conteúdo RAW da tabela
        # ============================================================
        print("   📊 Capturando conteúdo da tabela...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        import pyperclip
        conteudo_raw = pyperclip.paste()
        
        # IMPRIMIR CONTEÚDO RAW COMPLETO NO LOG
        print("\n" + "="*80)
        print("📋 CONTEÚDO RAW CAPTURADO (Ctrl+A + Ctrl+C):")
        print("="*80)
        print(conteudo_raw)
        print("="*80)
        print(f"Total de caracteres: {len(conteudo_raw)}")
        print(f"Total de linhas: {len(conteudo_raw.split(chr(10)))}")
        print("="*80 + "\n")
        
        # Parse da tabela para detectar múltiplas linhas
        resultado_parse = parse_tabela_ctrl_a(conteudo_raw, cpf)
        
        # Extrair dias de atraso e saldo contábil da tabela
        dias_atraso_tabela = resultado_parse.get('atraso_dias', '')
        saldo_contabil_tabela = resultado_parse.get('saldo_contabil', '')
        
        # Se retornou dados direto (ex: ACORDO FORMALIZADO com múltiplas linhas)
        if resultado_parse.get("return_direct"):
            print(f"   ✓ Status identificado: {resultado_parse['data']['cliente']['resultado']}")
            print(f"   ℹ️  Retornando dados da tabela sem abrir Nova Proposta")
            return resultado_parse
        
        # Verificar se CPF foi encontrado
        print("   Verificando resultado da pesquisa...")
        conteudo_pesquisa = conteudo_raw
        
        # Verificar se apareceu mensagem de "Nenhum contrato localizado"
        if "nenhum contrato localizado" in conteudo_pesquisa.lower():
            print("   ✗ CPF não encontrado no sistema - Nenhum contrato localizado")
            
            # Fechar modal de erro clicando no botão Fechar
            try:
                if 'fechar_modal_erro' not in coordenadas:
                    print("\n   📍 Capturando coordenada do botão FECHAR...")
                    fechar_erro_x, fechar_erro_y = capturar_posicao("botão FECHAR do modal 'Nenhum contrato localizado'", pyautogui, coordenadas, "fechar_modal_erro")
                    coordenadas['fechar_modal_erro'] = {'x': fechar_erro_x, 'y': fechar_erro_y}
                    salvar_coordenadas(coordenadas)
                else:
                    fechar_erro_x = coordenadas['fechar_modal_erro']['x']
                    fechar_erro_y = coordenadas['fechar_modal_erro']['y']
                
                print(f"   🖱️  Clicando em FECHAR modal ({fechar_erro_x}, {fechar_erro_y})...")
                pyautogui.click(fechar_erro_x, fechar_erro_y)
                time.sleep(1)
                print("   ✓ Modal fechado")
            except Exception as e:
                print(f"   ⚠️  Erro ao fechar modal: {e}")
            
            # Retornar estrutura padrão com resultado específico
            print("   📤 Retornando resultado para callback...")
            return {
                "success": True,
                "error": None,
                "data": {
                    "cliente": {
                        "nome": "",
                        "tipo_proposta": "",
                        "correntista_safra": "",
                        "cpf": cpf,
                        "produto": "",
                        "endereco": "",
                        "cep": "",
                        "cidade": "",
                        "uf": "",
                        "resultado": "Nenhum contrato localizado"
                    },
                    "veiculo": {},
                    "operacao": {},
                    "resumo_proposta": {},
                    "estimativa_venda": {}
                }
            }
        
        # Verificar se o contrato está CANCELADO
        if "cancelad" in conteudo_pesquisa.lower():
            print("   ⚠️ CPF encontrado mas contrato está CANCELADO")
            print("   📍 Iniciando processo para capturar dados...")
            
            # 1. Clicar na engrenagem (ícone de ações)
            if 'cancelado_engrenagem' not in coordenadas:
                engrenagem_x, engrenagem_y = capturar_posicao("ENGRENAGEM (ícone de ações) para CANCELADO", pyautogui, coordenadas, "cancelado_engrenagem")
                coordenadas['cancelado_engrenagem'] = {'x': engrenagem_x, 'y': engrenagem_y}
                salvar_coordenadas(coordenadas)
            else:
                engrenagem_x = coordenadas['cancelado_engrenagem']['x']
                engrenagem_y = coordenadas['cancelado_engrenagem']['y']
            
            print("   🔧 Clicando na engrenagem...")
            pyautogui.click(engrenagem_x, engrenagem_y)
            time.sleep(2)
            
            # Capturar tela para verificar se menu "Nova Proposta" existe
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            import pyperclip
            conteudo_menu = pyperclip.paste()
            
            # Verificar se "Nova Proposta" existe no menu
            if "nova proposta" not in conteudo_menu.lower():
                print("   ⚠️ Menu 'Nova Proposta' não encontrado!")
                print("   🔒 Clicando em Fechar para fechar o menu suspenso...")
                
                # Capturar coordenadas do botão "Fechar" se ainda não existir
                if 'cancelado_fechar_menu' not in coordenadas:
                    fechar_x, fechar_y = capturar_posicao("Botão FECHAR no menu suspenso (cancelado sem Nova Proposta)", pyautogui, coordenadas, "cancelado_fechar_menu")
                    coordenadas['cancelado_fechar_menu'] = {'x': fechar_x, 'y': fechar_y}
                    salvar_coordenadas(coordenadas)
                else:
                    fechar_x = coordenadas['cancelado_fechar_menu']['x']
                    fechar_y = coordenadas['cancelado_fechar_menu']['y']
                
                # Clicar em Fechar
                pyautogui.click(fechar_x, fechar_y)
                time.sleep(2)
                print("   ✓ Menu fechado!")
                
                # Retornar resultado
                return {
                    "cliente": {
                        "nome": "",
                        "tipo_proposta": "",
                        "correntista_safra": "",
                        "cpf": cpf,
                        "produto": "",
                        "endereco": "",
                        "cep": "",
                        "cidade": "",
                        "uf": "",
                        "resultado": "MENU NOVA PROPOSTA NAO EXISTE"
                    },
                    "veiculo": {},
                    "operacao": {},
                    "resumo_proposta": {},
                    "estimativa_venda": {}
                }
            
            # 2. Clicar em "Nova Proposta" no menu
            if 'cancelado_nova_proposta' not in coordenadas:
                nova_prop_x, nova_prop_y = capturar_posicao("NOVA PROPOSTA no menu para CANCELADO", pyautogui, coordenadas, "cancelado_nova_proposta")
                coordenadas['cancelado_nova_proposta'] = {'x': nova_prop_x, 'y': nova_prop_y}
                salvar_coordenadas(coordenadas)
            else:
                nova_prop_x = coordenadas['cancelado_nova_proposta']['x']
                nova_prop_y = coordenadas['cancelado_nova_proposta']['y']
            
            print("   📋 Clicando em Nova Proposta...")
            pyautogui.click(nova_prop_x, nova_prop_y)
            time.sleep(3)
            
            # 3. Clicar no campo "Tipo de Proposta" (select/dropdown)
            if 'cancelado_tipo_proposta' not in coordenadas:
                tipo_prop_x, tipo_prop_y = capturar_posicao("Campo TIPO DE PROPOSTA (select) para CANCELADO", pyautogui, coordenadas, "cancelado_tipo_proposta")
                coordenadas['cancelado_tipo_proposta'] = {'x': tipo_prop_x, 'y': tipo_prop_y}
                salvar_coordenadas(coordenadas)
            else:
                tipo_prop_x = coordenadas['cancelado_tipo_proposta']['x']
                tipo_prop_y = coordenadas['cancelado_tipo_proposta']['y']
            
            print("   📝 Clicando no campo Tipo de Proposta...")
            pyautogui.click(tipo_prop_x, tipo_prop_y)
            time.sleep(1)
            
            # 4. Clicar na opção do dropdown
            if 'cancelado_opcao_dropdown' not in coordenadas:
                opcao_x, opcao_y = capturar_posicao("OPÇÃO do dropdown Tipo de Proposta para CANCELADO", pyautogui, coordenadas, "cancelado_opcao_dropdown")
                coordenadas['cancelado_opcao_dropdown'] = {'x': opcao_x, 'y': opcao_y}
                salvar_coordenadas(coordenadas)
            else:
                opcao_x = coordenadas['cancelado_opcao_dropdown']['x']
                opcao_y = coordenadas['cancelado_opcao_dropdown']['y']
            
            print("   ✓ Selecionando opção do dropdown...")
            pyautogui.click(opcao_x, opcao_y)
            time.sleep(3)
            
            # Capturar conteúdo completo da tela
            print("   📋 Capturando dados da proposta cancelada...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(1)
            
            import pyperclip
            conteudo_cancelado = pyperclip.paste()
            
            if not conteudo_cancelado or len(conteudo_cancelado) < 50:
                print("   ⚠️ Conteúdo capturado vazio, usando dados mínimos")
                dados_cancelado = {
                    "cliente": {
                        "nome": "",
                        "tipo_proposta": "",
                        "correntista_safra": "",
                        "cpf": cpf,
                        "produto": "",
                        "endereco": "",
                        "cep": "",
                        "cidade": "",
                        "uf": "",
                        "resultado": "CANCELADO"
                    },
                    "veiculo": {},
                    "operacao": {},
                    "resumo_proposta": {},
                    "estimativa_venda": {}
                }
            else:
                # ============================================================
                # VERIFICAR DIAS DE ATRASO E PREENCHER REPASSE/BANCO SE > 180
                # ============================================================
                print(f"\n   ==========================================")
                print(f"   📊 Atraso (Dias) extraído da tabela: '{dias_atraso_tabela}'")
                print(f"   💰 Saldo Contábil extraído da tabela: '{saldo_contabil_tabela}'")
                print(f"   ==========================================\n")
                
                dias_atraso_str = dias_atraso_tabela
                saldo_contabil_str = saldo_contabil_tabela
                
                # Converter dias em atraso para número
                import re
                try:
                    dias_atraso = int(re.sub(r'\D', '', dias_atraso_str)) if dias_atraso_str else 0
                    print(f"   🔢 Dias em atraso convertido para número: {dias_atraso}")
                except Exception as e:
                    dias_atraso = 0
                    print(f"   ⚠️  ERRO ao converter dias em atraso: {e}")
                    print(f"   ⚠️  Usando dias_atraso = 0")
                
                print(f"\n   ==========================================")
                print(f"   🔍 VERIFICANDO CONDIÇÃO:")
                print(f"   dias_atraso ({dias_atraso}) > 180?")
                print(f"   Resultado: {dias_atraso > 180}")
                print(f"   ==========================================\n")
                
                # === REGRA: Se dias > 180, preencher Repasse/Banco ===
                if dias_atraso > 180:
                    print(f"\n   ==========================================")
                    print(f"   ⚠️  CONDIÇÃO ATENDIDA!")
                    print(f"   Dias em atraso = {dias_atraso} (> 180)")
                    print(f"   🔄 Iniciando preenchimento do campo 'Repasse / Banco'")
                    print(f"   Valor a preencher: {saldo_contabil_str}")
                    print(f"   ==========================================\n")
                    
                    # Verificar se já tem a coordenada salva
                    if 'input_repasse_banco' not in coordenadas:
                        print("\n" + "="*80)
                        print("📍 CAPTURA DE COORDENADA - Input 'Repasse / Banco'")
                        print("="*80)
                        print("⚠️  Coordenada 'input_repasse_banco' não encontrada!")
                        print("📋 Posicione o mouse sobre o INPUT 'Repasse / Banco'")
                        print("⏱️  Captura em 5 segundos...")
                        print("="*80 + "\n")
                        
                        for i in range(5, 0, -1):
                            print(f"   {i}...")
                            time.sleep(1)
                        
                        pos = pyautogui.position()
                        print(f"\n✅ Coordenada capturada: X={pos[0]}, Y={pos[1]}")
                        
                        coordenadas['input_repasse_banco'] = {
                            'x': pos[0],
                            'y': pos[1]
                        }
                        
                        with open('coordenadas.json', 'w', encoding='utf-8') as f:
                            json.dump(coordenadas, f, indent=4, ensure_ascii=False)
                        
                        print(f"💾 Coordenada salva em coordenadas.json como 'input_repasse_banco'\n")
                    else:
                        print(f"   ✓ Coordenada 'input_repasse_banco' já existe no arquivo")
                    
                    # Clicar no input usando coordenada
                    input_repasse_x = coordenadas['input_repasse_banco']['x']
                    input_repasse_y = coordenadas['input_repasse_banco']['y']
                    
                    print(f"\n   🖱️  Clicando no campo 'Repasse / Banco' em ({input_repasse_x}, {input_repasse_y})...")
                    pyautogui.click(input_repasse_x, input_repasse_y)
                    time.sleep(0.5)
                    print(f"   ✓ Click executado")
                    
                    # Limpar placeholder/conteúdo do campo com DEL
                    print(f"\n   🧹 Pressionando tecla DEL para limpar campo...")
                    pyautogui.press('delete')
                    time.sleep(0.3)
                    print(f"   ✓ DEL pressionado")
                    
                    # Digitar o valor do Saldo Contábil
                    print(f"\n   ✍️  Digitando valor: '{saldo_contabil_str}'")
                    pyautogui.typewrite(saldo_contabil_str, interval=0.05)
                    time.sleep(1)
                    print(f"   ✓ Valor digitado")
                    
                    print(f"\n   ✅ Campo 'Repasse / Banco' preenchido com sucesso!")
                    
                    # Capturar coordenada para clicar fora do input
                    if 'click_apos_repasse' not in coordenadas:
                        print("\n" + "="*80)
                        print("📍 CAPTURA DE COORDENADA - Click após preencher Repasse/Banco")
                        print("="*80)
                        print("⚠️  Coordenada 'click_apos_repasse' não encontrada!")
                        print("📋 Posicione o mouse em uma área FORA do input (área neutra)")
                        print("⏱️  Captura em 5 segundos...")
                        print("="*80 + "\n")
                        
                        for i in range(5, 0, -1):
                            print(f"   {i}...")
                            time.sleep(1)
                        
                        pos = pyautogui.position()
                        print(f"\n✅ Coordenada capturada: X={pos[0]}, Y={pos[1]}")
                        
                        coordenadas['click_apos_repasse'] = {
                            'x': pos[0],
                            'y': pos[1]
                        }
                        
                        with open('coordenadas.json', 'w', encoding='utf-8') as f:
                            json.dump(coordenadas, f, indent=4, ensure_ascii=False)
                        
                        print(f"💾 Coordenada salva em coordenadas.json como 'click_apos_repasse'\n")
                    else:
                        print(f"   ✓ Coordenada 'click_apos_repasse' já existe no arquivo")
                    
                    # Clicar fora do input
                    click_x = coordenadas['click_apos_repasse']['x']
                    click_y = coordenadas['click_apos_repasse']['y']
                    
                    print(f"\n   🖱️  Clicando fora do input em ({click_x}, {click_y})...")
                    pyautogui.click(click_x, click_y)
                    time.sleep(0.5)
                    print(f"   ✓ Click executado")
                    
                    # Recapturar após preencher
                    print("\n   📋 Recapturando dados após preencher campo...")
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.5)
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(1)
                    conteudo_cancelado = pyperclip.paste()
                    print("   ✓ Dados recapturados!")
                else:
                    print(f"\n   ==========================================")
                    print(f"   ℹ️  CONDIÇÃO NÃO ATENDIDA")
                    print(f"   Dias em atraso = {dias_atraso} (não é maior que 180)")
                    print(f"   ℹ️  Campo 'Repasse / Banco' NÃO será preenchido")
                    print(f"   ==========================================\n")
                
                # Extrair dados completos da proposta cancelada
                print("   🔍 Extraindo dados da proposta cancelada...")
                dados_cancelado = extrair_dados(conteudo_cancelado)
                # Marcar como CANCELADO no resultado
                dados_cancelado["cliente"]["resultado"] = "CANCELADO"
            
            print(f"   ✓ Dados de contrato cancelado preparados!")
            return dados_cancelado
        
        # Verificar se o contrato está NEGADO
        if "negad" in conteudo_pesquisa.lower():
            print("   ⚠️ CPF encontrado mas contrato está NEGADO")
            print("   📍 Iniciando captura de dados adicionais...")
            
            # Capturar coordenadas dos 4 cliques necessários para dados NEGADO
            click1_x, click1_y = capturar_posicao("PRIMEIRO CLIQUE para dados NEGADO", pyautogui, coordenadas, "negado_click1")
            coordenadas['negado_click1'] = {'x': click1_x, 'y': click1_y}
            salvar_coordenadas(coordenadas)
            
            # Primeiro clique
            pyautogui.click(click1_x, click1_y)
            time.sleep(2)
            
            # Capturar coordenadas do segundo clique
            click2_x, click2_y = capturar_posicao("SEGUNDO CLIQUE para dados NEGADO", pyautogui, coordenadas, "negado_click2")
            coordenadas['negado_click2'] = {'x': click2_x, 'y': click2_y}
            salvar_coordenadas(coordenadas)
            
            # Segundo clique
            pyautogui.click(click2_x, click2_y)
            time.sleep(2)
            
            # Capturar coordenadas do terceiro clique
            click3_x, click3_y = capturar_posicao("TERCEIRO CLIQUE para dados NEGADO", pyautogui, coordenadas, "negado_click3")
            coordenadas['negado_click3'] = {'x': click3_x, 'y': click3_y}
            salvar_coordenadas(coordenadas)
            
            # Terceiro clique
            pyautogui.click(click3_x, click3_y)
            time.sleep(2)
            
            # Capturar coordenadas do quarto clique
            click4_x, click4_y = capturar_posicao("QUARTO CLIQUE para dados NEGADO", pyautogui, coordenadas, "negado_click4")
            coordenadas['negado_click4'] = {'x': click4_x, 'y': click4_y}
            salvar_coordenadas(coordenadas)
            
            # Quarto clique
            pyautogui.click(click4_x, click4_y)
            time.sleep(2)
            
            # Capturar conteúdo completo
            print("   📋 Capturando dados da proposta negada...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(1)
            
            import pyperclip
            conteudo_negado = pyperclip.paste()
            
            if not conteudo_negado or len(conteudo_negado) < 50:
                print("   ⚠️ Conteúdo capturado vazio, usando dados mínimos")
                dados_negado = {
                    "cliente": {
                        "nome": "",
                        "tipo_proposta": "",
                        "correntista_safra": "",
                        "cpf": cpf,
                        "produto": "",
                        "endereco": "",
                        "cep": "",
                        "cidade": "",
                        "uf": "",
                        "resultado": "NEGADA"
                    },
                    "veiculo": {},
                    "operacao": {},
                    "resumo_proposta": {},
                    "estimativa_venda": {}
                }
            else:
                # ============================================================
                # VERIFICAR DIAS DE ATRASO E PREENCHER REPASSE/BANCO SE > 180
                # ============================================================
                print(f"\n   ==========================================")
                print(f"   📊 Atraso (Dias) extraído da tabela: '{dias_atraso_tabela}'")
                print(f"   💰 Saldo Contábil extraído da tabela: '{saldo_contabil_tabela}'")
                print(f"   ==========================================\n")
                
                dias_atraso_str = dias_atraso_tabela
                saldo_contabil_str = saldo_contabil_tabela
                
                # Converter dias em atraso para número
                import re
                try:
                    dias_atraso = int(re.sub(r'\D', '', dias_atraso_str)) if dias_atraso_str else 0
                    print(f"   🔢 Dias em atraso convertido para número: {dias_atraso}")
                except Exception as e:
                    dias_atraso = 0
                    print(f"   ⚠️  ERRO ao converter dias em atraso: {e}")
                    print(f"   ⚠️  Usando dias_atraso = 0")
                
                print(f"\n   ==========================================")
                print(f"   🔍 VERIFICANDO CONDIÇÃO:")
                print(f"   dias_atraso ({dias_atraso}) > 180?")
                print(f"   Resultado: {dias_atraso > 180}")
                print(f"   ==========================================\n")
                
                # === REGRA: Se dias > 180, preencher Repasse/Banco ===
                if dias_atraso > 180:
                    print(f"\n   ==========================================")
                    print(f"   ⚠️  CONDIÇÃO ATENDIDA!")
                    print(f"   Dias em atraso = {dias_atraso} (> 180)")
                    print(f"   🔄 Iniciando preenchimento do campo 'Repasse / Banco'")
                    print(f"   Valor a preencher: {saldo_contabil_str}")
                    print(f"   ==========================================\n")
                    
                    # Verificar se já tem a coordenada salva
                    if 'input_repasse_banco' not in coordenadas:
                        print("\n" + "="*80)
                        print("📍 CAPTURA DE COORDENADA - Input 'Repasse / Banco'")
                        print("="*80)
                        print("⚠️  Coordenada 'input_repasse_banco' não encontrada!")
                        print("📋 Posicione o mouse sobre o INPUT 'Repasse / Banco'")
                        print("⏱️  Captura em 5 segundos...")
                        print("="*80 + "\n")
                        
                        for i in range(5, 0, -1):
                            print(f"   {i}...")
                            time.sleep(1)
                        
                        pos = pyautogui.position()
                        print(f"\n✅ Coordenada capturada: X={pos[0]}, Y={pos[1]}")
                        
                        coordenadas['input_repasse_banco'] = {
                            'x': pos[0],
                            'y': pos[1]
                        }
                        
                        with open('coordenadas.json', 'w', encoding='utf-8') as f:
                            json.dump(coordenadas, f, indent=4, ensure_ascii=False)
                        
                        print(f"💾 Coordenada salva em coordenadas.json como 'input_repasse_banco'\n")
                    else:
                        print(f"   ✓ Coordenada 'input_repasse_banco' já existe no arquivo")
                    
                    # Clicar no input usando coordenada
                    input_repasse_x = coordenadas['input_repasse_banco']['x']
                    input_repasse_y = coordenadas['input_repasse_banco']['y']
                    
                    print(f"\n   🖱️  Clicando no campo 'Repasse / Banco' em ({input_repasse_x}, {input_repasse_y})...")
                    pyautogui.click(input_repasse_x, input_repasse_y)
                    time.sleep(0.5)
                    print(f"   ✓ Click executado")
                    
                    # Limpar placeholder/conteúdo do campo com DEL
                    print(f"\n   🧹 Pressionando tecla DEL para limpar campo...")
                    pyautogui.press('delete')
                    time.sleep(0.3)
                    print(f"   ✓ DEL pressionado")
                    
                    # Digitar o valor do Saldo Contábil
                    print(f"\n   ✍️  Digitando valor: '{saldo_contabil_str}'")
                    pyautogui.typewrite(saldo_contabil_str, interval=0.05)
                    time.sleep(1)
                    print(f"   ✓ Valor digitado")
                    
                    print(f"\n   ✅ Campo 'Repasse / Banco' preenchido com sucesso!")
                    
                    # Capturar coordenada para clicar fora do input
                    if 'click_apos_repasse' not in coordenadas:
                        print("\n" + "="*80)
                        print("📍 CAPTURA DE COORDENADA - Click após preencher Repasse/Banco")
                        print("="*80)
                        print("⚠️  Coordenada 'click_apos_repasse' não encontrada!")
                        print("📋 Posicione o mouse em uma área FORA do input (área neutra)")
                        print("⏱️  Captura em 5 segundos...")
                        print("="*80 + "\n")
                        
                        for i in range(5, 0, -1):
                            print(f"   {i}...")
                            time.sleep(1)
                        
                        pos = pyautogui.position()
                        print(f"\n✅ Coordenada capturada: X={pos[0]}, Y={pos[1]}")
                        
                        coordenadas['click_apos_repasse'] = {
                            'x': pos[0],
                            'y': pos[1]
                        }
                        
                        with open('coordenadas.json', 'w', encoding='utf-8') as f:
                            json.dump(coordenadas, f, indent=4, ensure_ascii=False)
                        
                        print(f"💾 Coordenada salva em coordenadas.json como 'click_apos_repasse'\n")
                    else:
                        print(f"   ✓ Coordenada 'click_apos_repasse' já existe no arquivo")
                    
                    # Clicar fora do input
                    click_x = coordenadas['click_apos_repasse']['x']
                    click_y = coordenadas['click_apos_repasse']['y']
                    
                    print(f"\n   🖱️  Clicando fora do input em ({click_x}, {click_y})...")
                    pyautogui.click(click_x, click_y)
                    time.sleep(0.5)
                    print(f"   ✓ Click executado")
                    
                    # Recapturar após preencher
                    print("\n   📋 Recapturando dados após preencher campo...")
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.5)
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(1)
                    conteudo_negado = pyperclip.paste()
                    print("   ✓ Dados recapturados!")
                else:
                    print(f"\n   ==========================================")
                    print(f"   ℹ️  CONDIÇÃO NÃO ATENDIDA")
                    print(f"   Dias em atraso = {dias_atraso} (não é maior que 180)")
                    print(f"   ℹ️  Campo 'Repasse / Banco' NÃO será preenchido")
                    print(f"   ==========================================\n")
                
                # Extrair dados completos da proposta negada
                print("   🔍 Extraindo dados da proposta negada...")
                dados_negado = extrair_dados(conteudo_negado)
                # Marcar como NEGADA no resultado
                dados_negado["cliente"]["resultado"] = "NEGADA"
            
            print(f"   ✓ Dados de contrato negado preparados!")
            return dados_negado
        
        # Verificar se o contrato está com ACORDO FORMALIZADO
        if "acordo formalizado" in conteudo_pesquisa.lower() or "em cumprimento" in conteudo_pesquisa.lower():
            print("   ⚠️ CPF encontrado mas ACORDO FORMALIZADO (EM CUMPRIMENTO)")
            
            # Extrair dados básicos da tela de pesquisa
            dados_acordo = {
                "cliente": {
                    "nome": "",
                    "tipo_proposta": "",
                    "correntista_safra": "",
                    "cpf": cpf,
                    "produto": "",
                    "endereco": "",
                    "cep": "",
                    "cidade": "",
                    "uf": "",
                    "resultado": "ACORDO FORMALIZADO (EM CUMPRIMENTO)"
                },
                "veiculo": {},
                "operacao": {},
                "resumo_proposta": {},
                "estimativa_venda": {}
            }
            
            print(f"   ✓ Dados de acordo formalizado preparados!")
            return dados_acordo
        
        print("   ✓ CPF encontrado! Prosseguindo...")
        
        # Verificar se encontrou resultado (botão Nova Proposta aparece)
        try:
            # Tentar clicar em Nova Proposta após pesquisa
            nova_proposta_x = coordenadas['botao_nova_proposta_pesquisa']['x']
            nova_proposta_y = coordenadas['botao_nova_proposta_pesquisa']['y']
            pyautogui.click(nova_proposta_x, nova_proposta_y)
            time.sleep(5)
            
            # 🔧 FIX: Nova Proposta abre em nova aba - trocar para ela
            print("   🔄 Verificando se abriu nova aba...")
            if len(driver.window_handles) > 1:
                print(f"   ℹ️  Detectadas {len(driver.window_handles)} abas, trocando para a mais recente...")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(2)
                print("   ✓ Trocado para nova aba com sucesso!")
            else:
                print("   ✓ Continua na mesma aba")
        except:
            raise Exception("CPF não encontrado - botão Nova Proposta não disponível")
        
        # Fechar primeiro modal
        fechar_modal1_x = coordenadas['fechar_modal1']['x']
        fechar_modal1_y = coordenadas['fechar_modal1']['y']
        pyautogui.click(fechar_modal1_x, fechar_modal1_y)
        time.sleep(2)
        
        # Clicar no dropdown do segundo modal
        dropdown_modal2_x = coordenadas['dropdown_modal2']['x']
        dropdown_modal2_y = coordenadas['dropdown_modal2']['y']
        pyautogui.click(dropdown_modal2_x, dropdown_modal2_y)
        time.sleep(1)
        
        # Selecionar opção
        opcao_dropdown_x = coordenadas['opcao_dropdown']['x']
        opcao_dropdown_y = coordenadas['opcao_dropdown']['y']
        pyautogui.click(opcao_dropdown_x, opcao_dropdown_y)
        time.sleep(2)
        
        # Clicar em Incluir
        incluir_x = coordenadas['botao_incluir']['x']
        incluir_y = coordenadas['botao_incluir']['y']
        pyautogui.click(incluir_x, incluir_y)
        time.sleep(3)
        
        # === PRIMEIRA CAPTURA: Para extrair Dias em Atraso e Saldo Contábil ===
        print("   📋 Capturando dados iniciais (Ctrl+A)...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(1)
        
        import pyperclip
        conteudo_inicial = pyperclip.paste()
        
        if not conteudo_inicial or len(conteudo_inicial) < 50:
            raise Exception("Conteúdo capturado vazio ou muito pequeno")
        
        # ============================================================
        # USAR VALORES JÁ EXTRAÍDOS DA TABELA (captura inicial)
        # ============================================================
        print(f"\n   ==========================================")
        print(f"   📊 Atraso (Dias) extraído da tabela: '{dias_atraso_tabela}'")
        print(f"   💰 Saldo Contábil extraído da tabela: '{saldo_contabil_tabela}'")
        print(f"   ==========================================\n")
        
        dias_atraso_str = dias_atraso_tabela
        saldo_contabil_str = saldo_contabil_tabela
        
        # Converter dias em atraso para número
        import re
        try:
            dias_atraso = int(re.sub(r'\D', '', dias_atraso_str)) if dias_atraso_str else 0
            print(f"   🔢 Dias em atraso convertido para número: {dias_atraso}")
        except Exception as e:
            dias_atraso = 0
            print(f"   ⚠️  ERRO ao converter dias em atraso: {e}")
            print(f"   ⚠️  Usando dias_atraso = 0")
        
        print(f"\n   ==========================================")
        print(f"   🔍 VERIFICANDO CONDIÇÃO:")
        print(f"   dias_atraso ({dias_atraso}) > 180?")
        print(f"   Resultado: {dias_atraso > 180}")
        print(f"   ==========================================\n")
        
        # === REGRA: Se dias > 180, preencher Repasse/Banco ===
        if dias_atraso > 180:
            print(f"\n   ==========================================")
            print(f"   ⚠️  CONDIÇÃO ATENDIDA!")
            print(f"   Dias em atraso = {dias_atraso} (> 180)")
            print(f"   🔄 Iniciando preenchimento do campo 'Repasse / Banco'")
            print(f"   Valor a preencher: {saldo_contabil_str}")
            print(f"   ==========================================\n")
            
            # Verificar se já tem a coordenada salva
            if 'input_repasse_banco' not in coordenadas:
                print("\n" + "="*80)
                print("📍 CAPTURA DE COORDENADA - Input 'Repasse / Banco'")
                print("="*80)
                print("⚠️  Coordenada 'input_repasse_banco' não encontrada!")
                print("📋 Posicione o mouse sobre o INPUT 'Repasse / Banco'")
                print("⏱️  Captura em 5 segundos...")
                print("="*80 + "\n")
                
                for i in range(5, 0, -1):
                    print(f"   {i}...")
                    time.sleep(1)
                
                # Capturar posição do mouse
                pos = pyautogui.position()
                print(f"\n✅ Coordenada capturada: X={pos[0]}, Y={pos[1]}")
                
                # Salvar no arquivo coordenadas.json
                coordenadas['input_repasse_banco'] = {
                    'x': pos[0],
                    'y': pos[1]
                }
                
                with open('coordenadas.json', 'w', encoding='utf-8') as f:
                    json.dump(coordenadas, f, indent=4, ensure_ascii=False)
                
                print(f"💾 Coordenada salva em coordenadas.json como 'input_repasse_banco'\n")
            else:
                print(f"   ✓ Coordenada 'input_repasse_banco' já existe no arquivo")
            
            # Clicar no input usando coordenada
            input_repasse_x = coordenadas['input_repasse_banco']['x']
            input_repasse_y = coordenadas['input_repasse_banco']['y']
            
            print(f"\n   🖱️  Clicando no campo 'Repasse / Banco' em ({input_repasse_x}, {input_repasse_y})...")
            pyautogui.click(input_repasse_x, input_repasse_y)
            time.sleep(0.5)
            print(f"   ✓ Click executado")
            
            # Limpar placeholder/conteúdo do campo com DEL
            print(f"\n   🧹 Pressionando tecla DEL para limpar campo...")
            pyautogui.press('delete')
            time.sleep(0.3)
            print(f"   ✓ DEL pressionado")
            
            # Digitar o valor do Saldo Contábil
            print(f"\n   ✍️  Digitando valor: '{saldo_contabil_str}'")
            pyautogui.typewrite(saldo_contabil_str, interval=0.05)
            time.sleep(1)
            print(f"   ✓ Valor digitado")
            
            print(f"\n   ✅ Campo 'Repasse / Banco' preenchido com sucesso!")
            
            # Capturar coordenada para clicar fora do input
            if 'click_apos_repasse' not in coordenadas:
                print("\n" + "="*80)
                print("📍 CAPTURA DE COORDENADA - Click após preencher Repasse/Banco")
                print("="*80)
                print("⚠️  Coordenada 'click_apos_repasse' não encontrada!")
                print("📋 Posicione o mouse em uma área FORA do input (área neutra)")
                print("⏱️  Captura em 5 segundos...")
                print("="*80 + "\n")
                
                for i in range(5, 0, -1):
                    print(f"   {i}...")
                    time.sleep(1)
                
                pos = pyautogui.position()
                print(f"\n✅ Coordenada capturada: X={pos[0]}, Y={pos[1]}")
                
                coordenadas['click_apos_repasse'] = {
                    'x': pos[0],
                    'y': pos[1]
                }
                
                with open('coordenadas.json', 'w', encoding='utf-8') as f:
                    json.dump(coordenadas, f, indent=4, ensure_ascii=False)
                
                print(f"💾 Coordenada salva em coordenadas.json como 'click_apos_repasse'\n")
            else:
                print(f"   ✓ Coordenada 'click_apos_repasse' já existe no arquivo")
            
            # Clicar fora do input
            click_x = coordenadas['click_apos_repasse']['x']
            click_y = coordenadas['click_apos_repasse']['y']
            
            print(f"\n   🖱️  Clicando fora do input em ({click_x}, {click_y})...")
            pyautogui.click(click_x, click_y)
            time.sleep(0.5)
            print(f"   ✓ Click executado")
            
            # === SEGUNDA CAPTURA: Com campo preenchido ===
            print("\n   📋 Capturando dados finais (Ctrl+A após preencher campo)...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(1)
            
            conteudo_texto = pyperclip.paste()
            print("   ✓ Dados finais capturados com campo Repasse/Banco preenchido!")
        else:
            print(f"\n   ==========================================")
            print(f"   ℹ️  CONDIÇÃO NÃO ATENDIDA")
            print(f"   Dias em atraso = {dias_atraso} (não é maior que 180)")
            print(f"   ℹ️  Campo 'Repasse / Banco' NÃO será preenchido")
            print(f"   ℹ️  Usando captura inicial")
            print(f"   ==========================================\n")
            conteudo_texto = conteudo_inicial
        
        if not conteudo_texto or len(conteudo_texto) < 50:
            raise Exception("Conteúdo final capturado vazio ou muito pequeno")
        
        # Extrair dados
        dados_extraidos = extrair_dados(conteudo_texto)
        
        print(f"   ✓ Dados extraídos com sucesso!")
        return dados_extraidos
        
    except Exception as e:
        print(f"   ✗ Erro ao processar CPF: {e}")
        raise


def extrair_dados(conteudo_texto):
    """Extrai campos específicos do texto capturado."""
    import re
    
    def extrair_campo(texto, campo_nome, proxima_linha=True):
        if proxima_linha:
            padrao = rf'{re.escape(campo_nome)}[:\s]*\n+([^\n]+)'
        else:
            padrao = rf'{re.escape(campo_nome)}[:\s]*([^\n]+)'
        
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    dados_extraidos = {
        "cliente": {
            "nome": extrair_campo(conteudo_texto, "Nome:"),
            "tipo_proposta": extrair_campo(conteudo_texto, "Tipo de Proposta:"),
            "correntista_safra": extrair_campo(conteudo_texto, "Correntista Safra:"),
            "cpf": extrair_campo(conteudo_texto, "CPF:"),
            "produto": extrair_campo(conteudo_texto, "Produto:"),
            "endereco": extrair_campo(conteudo_texto, "Endereço:"),
            "cep": extrair_campo(conteudo_texto, "CEP:"),
            "cidade": extrair_campo(conteudo_texto, "Cidade:"),
            "uf": extrair_campo(conteudo_texto, "UF:"),
            "resultado": "SUCESSO"
        },
        "veiculo": {
            "marca": extrair_campo(conteudo_texto, "Marca:"),
            "modelo": extrair_campo(conteudo_texto, "Modelo:"),
            "modalidade": extrair_campo(conteudo_texto, "Modalidade:"),
            "tipo": extrair_campo(conteudo_texto, "Tipo:"),
            "combustivel": extrair_campo(conteudo_texto, "Combustível:"),
            "placa": extrair_campo(conteudo_texto, "Placa:"),
            "chassi": extrair_campo(conteudo_texto, "Chassi:"),
            "ano_fabricacao_modelo": extrair_campo(conteudo_texto, "Ano Fabricação/Modelo:"),
            "renavam": extrair_campo(conteudo_texto, "Renavam:")
        },
        "operacao": {
            "contrato": extrair_campo(conteudo_texto, "Contrato:"),
            "data_contrato": extrair_campo(conteudo_texto, "Data contrato:"),
            "valor_compra": extrair_campo(conteudo_texto, "Valor da Compra:"),
            "plano": extrair_campo(conteudo_texto, "Plano:"),
            "valor_parcelas_pagas": extrair_campo(conteudo_texto, "Valor Parcelas Pagas:"),
            "quantidade_parcelas_pagas": extrair_campo(conteudo_texto, "Quantidade Parcelas Pagas:"),
            "dias_atraso": extrair_campo(conteudo_texto, "Dias em Atraso:"),
            "data_parcela_vencida": extrair_campo(conteudo_texto, "Data da Parcela + Vencida:"),
            "saldo_contabil": extrair_campo(conteudo_texto, "Saldo Contábil:"),
            "saldo_gerencial": extrair_campo(conteudo_texto, "Saldo Gerencial:"),
            "saldo_principal": extrair_campo(conteudo_texto, "Saldo Principal:"),
            "saldo_contabil_cdi": extrair_campo(conteudo_texto, "Saldo Contábil + CDI:"),
            "plano_balao": extrair_campo(conteudo_texto, "Plano Balão:")
        },
        "resumo_proposta": {
            "data_entrada": extrair_campo(conteudo_texto, "Data da entrada:"),
            "validade": extrair_campo(conteudo_texto, "Validade:"),
            "primeiro_pagamento": extrair_campo(conteudo_texto, "Primeiro pagamento:"),
            "qtd_parcelas_acordo": extrair_campo(conteudo_texto, "Qtd. Parcelas Acordo:"),
            "repasse_banco": extrair_campo(conteudo_texto, "Repasse / Banco:"),
            "alvara": extrair_campo(conteudo_texto, "Alvará:"),
            "total_repasse_alvara": extrair_campo(conteudo_texto, "Total Repasse + Alvará:"),
            "custas_banco": extrair_campo(conteudo_texto, "Custas / Banco:"),
            "ho_escritorio": extrair_campo(conteudo_texto, "HO Escritório:"),
            "ho_politica": extrair_campo(conteudo_texto, "HO Política:"),
            "total_acordo": extrair_campo(conteudo_texto, "Total Acordo:")
        },
        "estimativa_venda": {
            "cadin": extrair_campo(conteudo_texto, "CADIN:"),
            "valor_molicar": extrair_campo(conteudo_texto, "VALOR MOLICAR:"),
            "honorarios": extrair_campo(conteudo_texto, "HONORÁRIOS:")
        }
    }
    
    return dados_extraidos


def extrair_dados_cancelado(conteudo_texto, cpf):
    """Extrai dados específicos da tabela de contratos cancelados."""
    import re
    
    # Padrões para extrair dados da tabela
    # Exemplo: 16200 3535 	LINCOLN CARNEIRO DOS SANTOS FILHO 	26/11/2025 	DUNICE E MARCON ADVOGADOS ASSOCIADOS 	056.812.906-70 	R$ 72.985,58 	488 	R$ 51.190,82 	N1 		CANCELADA
    
    dados = {
        "cliente": {
            "nome": "",
            "tipo_proposta": "",
            "correntista_safra": "",
            "cpf": cpf,
            "produto": "",
            "endereco": "",
            "cep": "",
            "cidade": "",
            "uf": "",
            "resultado": "CANCELADO"
        },
        "veiculo": {},
        "operacao": {
            "contrato": "",
            "data_contrato": "",
            "valor_acordo": "",
            "dias_atraso": "",
            "saldo_contabil": "",
            "alcada_saida": "",
            "data_agendamento": "",
            "escritorio": ""
        },
        "resumo_proposta": {},
        "estimativa_venda": {}
    }
    
    # Tentar extrair o nome (geralmente em MAIÚSCULAS após o número do contrato)
    match_nome = re.search(r'\d+\s+\d+\s+([A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ\s]+)\s+\d{2}/\d{2}/\d{4}', conteudo_texto)
    if match_nome:
        dados["cliente"]["nome"] = match_nome.group(1).strip()
    
    # Extrair contrato (padrão: número espaço número, ex: 16200 3535)
    match_contrato = re.search(r'(\d+\s+\d+)\s+[A-Z]', conteudo_texto)
    if match_contrato:
        dados["operacao"]["contrato"] = match_contrato.group(1).strip()
    
    # Extrair data do acordo (formato: DD/MM/YYYY)
    match_data = re.search(r'(\d{2}/\d{2}/\d{4})', conteudo_texto)
    if match_data:
        dados["operacao"]["data_contrato"] = match_data.group(1).strip()
    
    # Extrair escritório (texto após a data e antes do CPF)
    match_escritorio = re.search(r'\d{2}/\d{2}/\d{4}\s+([A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ\s]+?)\s+\d{3}\.\d{3}\.\d{3}-\d{2}', conteudo_texto)
    if match_escritorio:
        dados["operacao"]["escritorio"] = match_escritorio.group(1).strip()
    
    # Extrair valor do acordo (formato: R$ XX.XXX,XX)
    match_valor_acordo = re.search(r'R\$\s*([\d.]+,\d{2})', conteudo_texto)
    if match_valor_acordo:
        dados["operacao"]["valor_acordo"] = match_valor_acordo.group(0).strip()
    
    # Extrair dias de atraso (número após valor do acordo)
    match_dias = re.search(r'R\$\s*[\d.]+,\d{2}\s+(\d+)\s+R\$', conteudo_texto)
    if match_dias:
        dados["operacao"]["dias_atraso"] = match_dias.group(1).strip()
    
    # Extrair saldo contábil (segundo valor R$)
    valores = re.findall(r'R\$\s*([\d.]+,\d{2})', conteudo_texto)
    if len(valores) >= 2:
        dados["operacao"]["saldo_contabil"] = f"R$ {valores[1]}"
    
    # Extrair alçada de saída (N1, N2, etc.)
    match_alcada = re.search(r'\s+(N\d+)\s+', conteudo_texto)
    if match_alcada:
        dados["operacao"]["alcada_saida"] = match_alcada.group(1).strip()
    
    return dados


def voltar_menu_pesquisa(driver, wait, pyautogui, coordenadas):
    """Volta para o menu de pesquisa clicando no menu lateral 'Pesquisa'."""
    print("\n↩️  Voltando ao menu de pesquisa...")
    
    try:
        # Garantir que está na aba certa (última aba - pesquisa)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        
        # Verificar se já tem coordenada do menu Pesquisa
        if 'menu_pesquisa' not in coordenadas:
            print("\n" + "="*80)
            print("📍 CAPTURA DE COORDENADA - Menu 'Pesquisa'")
            print("="*80)
            print("⚠️  Coordenada 'menu_pesquisa' não encontrada!")
            print("📋 Posicione o mouse sobre o menu 'Pesquisa' (lateral esquerdo)")
            print("⏱️  Captura em 5 segundos...")
            print("="*80 + "\n")
            
            for i in range(5, 0, -1):
                print(f"   {i}...")
                time.sleep(1)
            
            # Capturar posição do mouse
            pos = pyautogui.position()
            print(f"\n✅ Coordenada capturada: X={pos[0]}, Y={pos[1]}")
            
            # Salvar no arquivo coordenadas.json
            coordenadas['menu_pesquisa'] = {
                'x': pos[0],
                'y': pos[1]
            }
            
            import json
            with open('coordenadas.json', 'w', encoding='utf-8') as f:
                json.dump(coordenadas, f, indent=4, ensure_ascii=False)
            
            print(f"💾 Coordenada salva em coordenadas.json como 'menu_pesquisa'\n")
        else:
            print(f"   ✓ Coordenada 'menu_pesquisa' já existe no arquivo")
        
        # Clicar no menu Pesquisa
        menu_x = coordenadas['menu_pesquisa']['x']
        menu_y = coordenadas['menu_pesquisa']['y']
        
        print(f"   🖱️  Clicando no menu 'Pesquisa' ({menu_x}, {menu_y})...")
        pyautogui.click(menu_x, menu_y)
        time.sleep(3)
        
        print("   ✓ Menu Pesquisa aberto!")
        
    except Exception as e:
        print(f"   ⚠️  Erro ao clicar no menu: {e}")
        print(f"   🔄 Tentando F5 como alternativa...")
        pyautogui.press('f5')
        time.sleep(3)


def processar_arquivo(arquivo_entrada, driver, wait, pyautogui, coordenadas):
    """Processa um único arquivo CSV."""
    print(f"\n📄 Arquivo encontrado: {arquivo_entrada.name}")
    registrar_log(f"Arquivo encontrado: {arquivo_entrada.name}")
    
    # Ler CPFs do arquivo
    print("\n📖 Lendo CPFs do arquivo...")
    linhas = ler_cpfs_csv(arquivo_entrada)
    print(f"   ✓ {len(linhas)} CPFs encontrados")
    registrar_log(f"CPFs carregados: {len(linhas)}")
    
    # Processar cada CPF
    for idx, linha in enumerate(linhas, 1):
        cpf = linha['cpf']
        print(f"\n{'='*60}")
        print(f"PROCESSANDO {idx}/{len(linhas)}: {cpf}")
        print(f"{'='*60}")
        
        tentativas = 0
        sucesso = False
        
        while tentativas < MAX_TENTATIVAS and not sucesso:
            try:
                # Processar CPF
                dados = processar_cpf(driver, wait, pyautogui, coordenadas, cpf)
                
                # Enviar para webhook
                webhook_ok = enviar_webhook(success=True, cpf=cpf, data=dados)
                
                # Marcar sucesso
                linha['status'] = 'SUCCESS'
                linha['mensagem'] = 'Dados enviados ao webhook' if webhook_ok else 'Processado mas webhook falhou'
                sucesso = True
                
                # Voltar ao menu de pesquisa
                voltar_menu_pesquisa(driver, wait, pyautogui, coordenadas)
                
            except Exception as e:
                tentativas += 1
                erro_msg = str(e)
                print(f"   ⚠️ Tentativa {tentativas}/{MAX_TENTATIVAS} falhou: {erro_msg}")
                
                if tentativas >= MAX_TENTATIVAS:
                    # Criar estrutura de dados com resultado "CPF/CNPJ Não encontrado"
                    dados_erro = {
                        "cliente": {
                            "nome": "",
                            "tipo_proposta": "",
                            "correntista_safra": "",
                            "cpf": cpf,
                            "produto": "",
                            "endereco": "",
                            "cep": "",
                            "cidade": "",
                            "uf": "",
                            "resultado": "CPF/CNPJ Não encontrado"
                        },
                        "veiculo": {},
                        "operacao": {},
                        "resumo_proposta": {},
                        "estimativa_venda": {}
                    }
                    
                    # Enviar erro para webhook com estrutura de dados
                    enviar_webhook(success=False, cpf=cpf, data=dados_erro, error=erro_msg)
                    
                    linha['status'] = 'ERROR'
                    linha['mensagem'] = erro_msg
                else:
                    time.sleep(2)
    
    # Salvar resultado
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_saida = OUTPUT_DIR / f"{arquivo_entrada.stem}_processado_{timestamp}.csv"
    salvar_csv_resultado(arquivo_saida, linhas)
    
    print(f"\n{'='*60}")
    print(f"✅ PROCESSAMENTO CONCLUÍDO!")
    print(f"{'='*60}")
    print(f"\n📊 Resumo:")
    sucessos = sum(1 for l in linhas if l['status'] == 'SUCCESS')
    erros = sum(1 for l in linhas if l['status'] == 'ERROR')
    print(f"   ✓ Sucessos: {sucessos}")
    print(f"   ✗ Erros: {erros}")
    print(f"\n📁 Resultado salvo em: {arquivo_saida}")
    
    # Registrar resumo no log
    registrar_log(f"PROCESSAMENTO CONCLUÍDO - Sucessos: {sucessos}, Erros: {erros}")
    registrar_log(f"Arquivo de saída: {arquivo_saida}")
    
    # Deletar arquivo de entrada após processar
    try:
        arquivo_entrada.unlink()
        print(f"\n🗑️  Arquivo de entrada deletado: {arquivo_entrada.name}")
        registrar_log(f"Arquivo de entrada deletado: {arquivo_entrada.name}")
    except Exception as e:
        print(f"\n⚠️  Erro ao deletar arquivo: {e}")
        registrar_log(f"ERRO ao deletar arquivo: {e}")


def main():
    """Função principal - Modo contínuo."""
    load_dotenv()
    
    print("="*60)
    print("🤖 RPA SAFRA - MODO CONTÍNUO")
    print("="*60)
    print("\n⏱️  Monitorando pasta input/ a cada 2 minutos...")
    print("💡 Pressione Ctrl+C para parar\n")
    
    # Registrar início da execução
    registrar_log("="*60)
    registrar_log("MODO CONTÍNUO INICIADO")
    
    # Configurações
    website_url = os.getenv('WEBSITE_URL')
    username = os.getenv('SITE_USERNAME')
    password = os.getenv('SITE_PASSWORD')
    timeout = int(os.getenv('BROWSER_TIMEOUT', '30'))
    
    try:
        import pyautogui
    except ImportError:
        print("   Instalando pyautogui...")
        import subprocess
        subprocess.run([os.path.join('venv', 'Scripts', 'pip.exe'), 'install', 'pyautogui', 'pyperclip'], check=True)
        import pyautogui
    
    coordenadas = carregar_coordenadas()
    
    try:
        # Loop contínuo
        while True:
            try:
                # Buscar arquivos CSV/TXT na pasta input
                arquivos_csv = list(INPUT_DIR.glob('*.csv')) + list(INPUT_DIR.glob('*.txt'))
                
                if arquivos_csv:
                    # Ordenar por data de criação (mais antigos primeiro)
                    arquivos_csv.sort(key=lambda f: f.stat().st_ctime)
                    
                    # Processar apenas o primeiro arquivo (mais antigo)
                    arquivo_entrada = arquivos_csv[0]
                    
                    print(f"\n{'='*60}")
                    print(f"🔄 NOVO ARQUIVO DETECTADO")
                    print(f"{'='*60}")
                    registrar_log(f"Novo arquivo detectado: {arquivo_entrada.name}")
                    
                    # Abrir navegador apenas quando há arquivo para processar
                    print("\n🌐 Abrindo navegador...")
                    driver = setup_driver()
                    wait = WebDriverWait(driver, timeout)
                    
                    try:
                        # Fazer login
                        driver.get(website_url)
                        time.sleep(3)
                        fazer_login(driver, wait, username, password)
                        
                        # Navegar para tela de pesquisa
                        navegar_nova_proposta(driver, wait)
                        
                        # Processar o arquivo
                        processar_arquivo(arquivo_entrada, driver, wait, pyautogui, coordenadas)
                        
                        registrar_log("="*60)
                        
                    finally:
                        # Fechar navegador após processar
                        print("\n⚠️  Fechando navegador...")
                        driver.quit()
                        print("✓ Navegador fechado\n")
                    
                else:
                    # Sem arquivos, aguardar 2 minutos
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 👀 Sem arquivos para processar. Aguardando 2 minutos...")
                    time.sleep(120)  # 2 minutos
                    
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"\n❌ Erro no loop principal: {e}")
                registrar_log(f"ERRO no loop: {e}")
                print("   Aguardando 2 minutos antes de tentar novamente...")
                time.sleep(120)
        
    except KeyboardInterrupt:
        print(f"\n\n{'='*60}")
        print(f"⚠️  Sistema interrompido pelo usuário")
        print(f"{'='*60}")
        registrar_log("Sistema interrompido pelo usuário")
        registrar_log("="*60)
    except Exception as e:
        print(f"\n✗ Erro fatal: {str(e)}")
        registrar_log(f"ERRO FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        registrar_log("="*60)


if __name__ == '__main__':
    main()
