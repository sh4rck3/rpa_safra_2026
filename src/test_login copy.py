#!/usr/bin/env python3
"""
Script de teste interativo - Login passo a passo
"""

import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# Arquivo para salvar coordenadas
COORDENADAS_FILE = Path('coordenadas.json')


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
    print("2. DEIXE o mouse parado lá")
    print("3. Aguarde a contagem regressiva")
    print("\nIniciando captura em 3 segundos...")
    time.sleep(3)
    
    print("\nCapturando posição em 5 segundos...")
    print(f"POSICIONE O MOUSE AGORA!")
    
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    
    # Capturar posição
    x, y = pyautogui.position()
    print(f"\n✓ Posição capturada: X={x}, Y={y}")
    
    return x, y


def setup_driver():
    """Configura o driver do Chrome."""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--start-maximized')
    
    # Download settings
    download_path = Path('./downloads').absolute()
    prefs = {
        'download.default_directory': str(download_path),
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'plugins.always_open_pdf_externally': True
    }
    chrome_options.add_experimental_option('prefs', prefs)
    
    # Instalar e configurar o ChromeDriver
    print("📦 Instalando/atualizando ChromeDriver...")
    driver_path = ChromeDriverManager().install()
    
    # Corrigir caminho se necessário
    if not driver_path.endswith('.exe'):
        # Procurar o chromedriver.exe na pasta
        import os
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
    
    # Criar serviço explicitamente
    service = Service(executable_path=driver_path)
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver


def main():
    """Função principal."""
    load_dotenv()
    
    website_url = os.getenv('WEBSITE_URL')
    username = os.getenv('SITE_USERNAME')
    password = os.getenv('SITE_PASSWORD')
    timeout = int(os.getenv('BROWSER_TIMEOUT', '30'))
    
    print("=" * 60)
    print("SCRIPT DE TESTE - LOGIN INTERATIVO")
    print("=" * 60)
    print(f"\n✓ URL: {website_url}")
    print(f"✓ Usuário: {username}")
    print(f"✓ Timeout: {timeout}s\n")
    
    driver = setup_driver()
    
    try:
        # 1. Acessar o site
        print("1️⃣  Acessando o site...")
        driver.get(website_url)
        time.sleep(3)
        
        # 2. Aguardar página carregar
        wait = WebDriverWait(driver, timeout)
        
        # 3. Tentar encontrar os campos de login
        print("2️⃣  Procurando campos de login...")
        
        # Campo de usuário - usando o ID correto do Safra
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, 'Username'))
        )
        print("   ✓ Campo de usuário encontrado (id='Username')")
        
        # Preencher usuário
        print("3️⃣  Preenchendo usuário...")
        username_field.clear()
        username_field.send_keys(username)
        time.sleep(1)
        
        # Campo de senha - usando o ID correto do Safra
        password_field = driver.find_element(By.ID, 'Password')
        print("   ✓ Campo de senha encontrado (id='Password')")
        
        # Preencher senha
        print("4️⃣  Preenchendo senha...")
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1)
        
        # Botão de login
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button.btn-login[type="submit"]')
        print("   ✓ Botão de login encontrado")
        
        # Fazer login
        print("5️⃣  Clicando no botão de login...")
        submit_button.click()
        time.sleep(5)
        
        print("\n" + "=" * 60)
        print("✅ LOGIN REALIZADO!")
        print("=" * 60)
        
        # PASSO 1: Clicar no dropdown "Propostas"
        print("\n6️⃣  Clicando no menu 'Propostas'...")
        dropdown_propostas = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Propostas")]/parent::a'))
        )
        dropdown_propostas.click()
        time.sleep(2)
        print("   ✓ Dropdown 'Propostas' aberto")
        
        # PASSO 2: Clicar em "Nova Proposta"
        print("7️⃣  Clicando em 'Nova Proposta'...")
        nova_proposta = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//a[@href="/FinanceiraVeiculos/Seguranca/Proposta/Manutencao"]'))
        )
        nova_proposta.click()
        time.sleep(3)
        print("   ✓ 'Nova Proposta' clicado")
        
        # PASSO 3: Preencher CPF com PyAutoGUI
        print("8️⃣  Preparando para preencher CPF...")
        time.sleep(3)
        
        # Importar pyautogui
        try:
            import pyautogui
        except ImportError:
            print("   Instalando pyautogui...")
            import subprocess
            subprocess.run([os.path.join('venv', 'Scripts', 'pip.exe'), 'install', 'pyautogui'], check=True)
            import pyautogui
        
        # Carregar coordenadas salvas
        coordenadas = carregar_coordenadas()
        
        # Capturar ou usar posição salva do campo CPF
        cpf_x, cpf_y = capturar_posicao("campo CPF", pyautogui, coordenadas, "campo_cpf")
        coordenadas['campo_cpf'] = {'x': cpf_x, 'y': cpf_y}
        
        # Clicar no campo
        print("   Clicando no campo CPF...")
        pyautogui.click(cpf_x, cpf_y)
        time.sleep(0.5)
        
        # Limpar campo (Ctrl+A + Delete)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.press('delete')
        time.sleep(0.2)
        
        # Digitar CPF caractere por caractere
        print("   Digitando CPF: 0010305742")
        cpf = "0010305742"
        for digit in cpf:
            pyautogui.typewrite(digit, interval=0.1)
        
        time.sleep(0.5)
        print("   ✓ CPF '0010305742' preenchido com sucesso!")
        time.sleep(1)
        
        # PASSO 4: Clicar em Pesquisar com PyAutoGUI
        print("9️⃣  Preparando para clicar em 'Pesquisar'...")
        
        # Capturar ou usar posição salva do botão Pesquisar
        pesquisar_x, pesquisar_y = capturar_posicao("botão PESQUISAR", pyautogui, coordenadas, "botao_pesquisar")
        coordenadas['botao_pesquisar'] = {'x': pesquisar_x, 'y': pesquisar_y}
        
        # Salvar coordenadas para próximas execuções
        salvar_coordenadas(coordenadas)
        
        # Clicar no botão Pesquisar
        print("   Clicando em 'Pesquisar'...")
        pyautogui.click(pesquisar_x, pesquisar_y)
        time.sleep(5)
        print("   ✓ 'Pesquisar' clicado")
        
        print("\n" + "=" * 60)
        print("✅ PESQUISA REALIZADA!")
        print("=" * 60)
        
        # PASSO 5: Clicar em "Nova Proposta" (após pesquisa)
        print("🔟  Preparando para clicar em 'Nova Proposta'...")
        
        # Capturar ou usar posição salva do botão Nova Proposta
        nova_proposta_x, nova_proposta_y = capturar_posicao("botão NOVA PROPOSTA (após pesquisa)", pyautogui, coordenadas, "botao_nova_proposta_pesquisa")
        coordenadas['botao_nova_proposta_pesquisa'] = {'x': nova_proposta_x, 'y': nova_proposta_y}
        
        # Salvar coordenadas atualizadas
        salvar_coordenadas(coordenadas)
        
        # Clicar no botão Nova Proposta
        print("   Clicando em 'Nova Proposta'...")
        pyautogui.click(nova_proposta_x, nova_proposta_y)
        time.sleep(5)
        print("   ✓ 'Nova Proposta' clicado")
        
        print("\n" + "=" * 60)
        print("✅ FLUXO AVANÇADO!")
        print("=" * 60)
        
        # PASSO 6: Fechar primeiro modal
        print("1️⃣1️⃣  Preparando para fechar PRIMEIRO MODAL...")
        time.sleep(2)
        
        # Capturar ou usar posição salva do botão de fechar modal 1
        fechar_modal1_x, fechar_modal1_y = capturar_posicao("botão FECHAR/X do PRIMEIRO MODAL", pyautogui, coordenadas, "fechar_modal1")
        coordenadas['fechar_modal1'] = {'x': fechar_modal1_x, 'y': fechar_modal1_y}
        
        # Salvar coordenadas
        salvar_coordenadas(coordenadas)
        
        # Clicar para fechar modal 1
        print("   Fechando primeiro modal...")
        pyautogui.click(fechar_modal1_x, fechar_modal1_y)
        time.sleep(2)
        print("   ✓ Primeiro modal fechado")
        
        # PASSO 7: Clicar no dropdown do segundo modal
        print("1️⃣2️⃣  Preparando para clicar no DROPDOWN do SEGUNDO MODAL...")
        time.sleep(2)
        
        # Capturar ou usar posição salva do dropdown
        dropdown_modal2_x, dropdown_modal2_y = capturar_posicao("DROPDOWN do SEGUNDO MODAL (campo select)", pyautogui, coordenadas, "dropdown_modal2")
        coordenadas['dropdown_modal2'] = {'x': dropdown_modal2_x, 'y': dropdown_modal2_y}
        
        # Salvar coordenadas
        salvar_coordenadas(coordenadas)
        
        # Clicar no dropdown
        print("   Clicando no dropdown...")
        pyautogui.click(dropdown_modal2_x, dropdown_modal2_y)
        time.sleep(1)
        print("   ✓ Dropdown aberto")
        
        # PASSO 8: Selecionar opção do dropdown
        print("1️⃣3️⃣  Preparando para selecionar OPÇÃO do dropdown...")
        time.sleep(1)
        
        # Capturar ou usar posição salva da opção
        opcao_dropdown_x, opcao_dropdown_y = capturar_posicao("OPÇÃO a selecionar no dropdown", pyautogui, coordenadas, "opcao_dropdown")
        coordenadas['opcao_dropdown'] = {'x': opcao_dropdown_x, 'y': opcao_dropdown_y}
        
        # Salvar coordenadas
        salvar_coordenadas(coordenadas)
        
        # Clicar na opção
        print("   Selecionando opção...")
        pyautogui.click(opcao_dropdown_x, opcao_dropdown_y)
        time.sleep(2)
        print("   ✓ Opção selecionada")
        
        # PASSO 9: Clicar no botão Incluir
        print("1️⃣4️⃣  Preparando para clicar no botão 'INCLUIR'...")
        time.sleep(1)
        
        # Capturar ou usar posição salva do botão Incluir
        incluir_x, incluir_y = capturar_posicao("botão INCLUIR", pyautogui, coordenadas, "botao_incluir")
        coordenadas['botao_incluir'] = {'x': incluir_x, 'y': incluir_y}
        
        # Salvar coordenadas
        salvar_coordenadas(coordenadas)
        
        # Clicar no botão Incluir
        print("   Clicando em 'Incluir'...")
        pyautogui.click(incluir_x, incluir_y)
        time.sleep(3)
        print("   ✓ 'Incluir' clicado")
        
        print("\n" + "=" * 60)
        print("✅ PÁGINA FINAL ABERTA!")
        print("=" * 60)
        
        # PASSO 10: Copiar conteúdo da página
        print("1️⃣5️⃣  Copiando conteúdo da página...")
        time.sleep(2)
        
        conteudo_texto = None
        dados_extraidos = {}
        
        # Método 1: Tentar via PyAutoGUI (Ctrl+A e Ctrl+C)
        try:
            print("   Método 1: Selecionando todo conteúdo (Ctrl+A)...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            
            print("   Copiando para clipboard (Ctrl+C)...")
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(1)
            
            # Importar pyperclip para ler clipboard
            try:
                import pyperclip
            except ImportError:
                print("   Instalando pyperclip...")
                import subprocess
                subprocess.run([os.path.join('venv', 'Scripts', 'pip.exe'), 'install', 'pyperclip'], check=True)
                import pyperclip
            
            conteudo_texto = pyperclip.paste()
            
            if conteudo_texto and len(conteudo_texto) > 50:
                print(f"   ✓ Conteúdo capturado via Selenium ({len(conteudo_texto)} caracteres)")
                
                # Extrair campos específicos usando regex
                import re
                
                def extrair_campo(texto, campo_nome, proxima_linha=True):
                    """Extrai valor de um campo do texto."""
                    if proxima_linha:
                        # Valor está na próxima linha
                        padrao = rf'{re.escape(campo_nome)}[:\s]*\n+([^\n]+)'
                    else:
                        # Valor está na mesma linha
                        padrao = rf'{re.escape(campo_nome)}[:\s]*([^\n]+)'
                    
                    match = re.search(padrao, texto, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                    return ""
                
                # Extrair todos os campos solicitados
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
                        "uf": extrair_campo(conteudo_texto, "UF:")
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
                
                # Salvar apenas JSON
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                json_file = Path('downloads') / f'proposta_{timestamp}.json'
                
                # Salvar JSON estruturado
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(dados_extraidos, f, ensure_ascii=False, indent=2)
                print(f"   💾 Dados JSON salvos em: {json_file}")
                
                print("\n" + "=" * 60)
                print("DADOS EXTRAÍDOS (JSON):")
                print("=" * 60)
                print(json.dumps(dados_extraidos, ensure_ascii=False, indent=2))
                print("=" * 60)
            else:
                raise Exception("Conteúdo vazio")
                
        except Exception as e:
            print(f"   ⚠️ Erro: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("✅ AUTOMAÇÃO COMPLETA!")
        print("=" * 60)
        print("\n📁 Arquivo salvo na pasta 'downloads/'")
        print("   - proposta_[data].json (dados estruturados)")
        
        input("\n\nPressione ENTER para fechar o navegador...")
        
    except Exception as e:
        print(f"\n✗ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n⚠️  Fechando navegador em 5 segundos...")
        time.sleep(5)
        driver.quit()
        print("✓ Navegador fechado")


if __name__ == '__main__':
    main()
