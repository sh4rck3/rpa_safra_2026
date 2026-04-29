"""
Script para Capturar Coordenadas do Sistema GCPJ
================================================

Este script ajuda a capturar as coordenadas dos elementos na tela
para automatizar o acesso ao sistema GCPJ via extensão do Chrome.

IMPORTANTE: Execute este script ANTES de usar o processamento em lote!

Passos:
1. Abre o Chrome com perfil persistente
2. Aguarda você posicionar o mouse em cada elemento
3. Captura as coordenadas ao pressionar ENTER
4. Salva tudo em coordenadas_gcpj.json

Coordenadas são salvas incrementalmente - só pede as que faltam!
"""

import json
import pyautogui
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Desabilitar failsafe do pyautogui
pyautogui.FAILSAFE = False

# Arquivo para salvar coordenadas
ARQUIVO_COORDENADAS = Path(__file__).parent.parent / "coordenadas_gcpj.json"

# Variável global para o driver
driver = None

def capturar_coordenada(nome_elemento: str, descricao: str) -> dict:
    """
    Captura a coordenada de um elemento específico.
    
    Args:
        nome_elemento: Nome identificador do elemento
        descricao: Descrição do que o usuário deve fazer
    
    Returns:
        dict com x, y da coordenada capturada
    """
    print(f"\n{'='*70}")
    print(f"📍 ELEMENTO: {nome_elemento.upper()}")
    print(f"{'='*70}")
    print(f"📋 {descricao}")
    print(f"\n⚠️  INSTRUÇÕES:")
    print(f"   1. Posicione o mouse EXATAMENTE sobre o elemento")
    print(f"   2. Pressione ENTER para capturar a coordenada")
    print(f"   3. NÃO mova o mouse após pressionar ENTER!")
    
    input("\n⏸️  Pressione ENTER quando o mouse estiver posicionado...")
    
    # Captura posição do mouse
    x, y = pyautogui.position()
    
    print(f"✅ Coordenada capturada: X={x}, Y={y}")
    
    return {"x": x, "y": y, "descricao": descricao}

def carregar_coordenadas_existentes():
    """Carrega coordenadas já salvas anteriormente."""
    if ARQUIVO_COORDENADAS.exists():
        with open(ARQUIVO_COORDENADAS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_coordenadas(coordenadas: dict):
    """Salva coordenadas no arquivo JSON."""
    with open(ARQUIVO_COORDENADAS, "w", encoding="utf-8") as f:
        json.dump(coordenadas, f, indent=4, ensure_ascii=False)
    print(f"💾 Coordenadas salvas!")

def abrir_chrome():
    """Abre o Chrome automaticamente com perfil persistente."""
    global driver
    
    print("\n🌐 Abrindo Chrome com perfil dedicado...")
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Perfil dedicado para o Selenium (na pasta do projeto)
    profile_dir = Path(__file__).parent.parent / "chrome_profile"
    profile_dir.mkdir(exist_ok=True)
    chrome_options.add_argument(f"--user-data-dir={profile_dir.absolute()}")
    
    print(f"📁 Perfil persistente: {profile_dir}")
    print("💡 Extensões instaladas neste perfil ficarão salvas!")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"⚠️  Erro: {e}")
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e2:
            print(f"❌ Erro ao abrir Chrome: {e2}")
            raise
    
    driver.get("about:blank")
    print("✅ Chrome aberto!")
    time.sleep(2)

def main():
    """Função principal para capturar todas as coordenadas do GCPJ."""
    global driver
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║        🤖 CAPTURA DE COORDENADAS - SISTEMA GCPJ                     ║
║                                                                      ║
║  Este script irá capturar as coordenadas dos elementos necessários  ║
║  para automatizar o acesso ao sistema GCPJ via extensão do Chrome.  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n📝 PASSOS QUE SERÃO CAPTURADOS:")
    print("   1. Ícone da extensão GCPJ no Chrome")
    print("   2. Campo de input/busca da extensão")
    print("   3. Item 'GCPJ' no menu suspenso")
    print("   4. Botão 'ACESSAR'")
    print("   5. Link 'Consulta de Processos'")
    print("   6. Campo 'Nº do Processo Bradesco'")
    print("   7. Botão 'BUSCAR'")
    print("\n🚀 Abrindo Chrome automaticamente...")
    
    # Abre o Chrome
    abrir_chrome()
    
    # Carregar coordenadas existentes
    coordenadas = carregar_coordenadas_existentes()
    
    if coordenadas:
        print("\n" + "="*70)
        print(f"📂 COORDENADAS EXISTENTES: {len(coordenadas)}")
        for nome in coordenadas.keys():
            print(f"   ✓ {nome}")
        print("="*70)
        print("💡 Executando coordenadas existentes automaticamente...")
        print("💡 Apenas as coordenadas faltantes serão capturadas!")
    
    # Verificar se a extensão já foi configurada (pergunta apenas uma vez)
    if not coordenadas.get("_extensao_configurada"):
        print("\n" + "="*70)
        print("🔍 VERIFICANDO EXTENSÃO GCPJ NO CHROME")
        print("="*70)
        
        if not coordenadas:
            print("📌 PRIMEIRA EXECUÇÃO NESTE COMPUTADOR:")
        else:
            print("📌 VERIFICANDO EXTENSÃO:")
        
        print("   1. Instale a extensão GCPJ no Chrome (se ainda não tiver)")
        print("   2. Faça LOGIN na extensão")
        print("   3. IMPORTANTE: O usuário do login NÃO pode estar em uso")
        print("   4. Verifique se a extensão está VISÍVEL e ACESSÍVEL")
        print("   5. Clique na extensão para garantir que abre o popup")
        print("="*70)
        print("\n💡 DICA: A extensão fica no canto superior direito do Chrome")
        print("💡 O Chrome foi aberto em modo MAXIMIZADO para facilitar")
        print("\n⚠️  A extensão ficará instalada neste perfil para as próximas execuções!")
        
        resposta = input("\n✅ A extensão está instalada, LOGADA e o usuário NÃO está em uso? (s/n): ").strip().lower()
        
        if resposta != 's':
            print("\n" + "="*70)
            print("⏸️  AGUARDANDO INSTALAÇÃO DA EXTENSÃO")
            print("="*70)
            print("\n📝 PASSOS PARA INSTALAR:")
            print("   1. Vá para a Chrome Web Store ou local da extensão")
            print("   2. Instale a extensão GCPJ")
            print("   3. Faça login se necessário")
            print("   4. Clique no ícone da extensão para testar")
            print("   5. Volte aqui e pressione ENTER")
            print("\n💡 O Chrome continuará aberto esperando você!")
            input("\n⏸️  Pressione ENTER quando a extensão estiver instalada e funcionando...")
        
        # Salvar flag indicando que a extensão foi configurada
        coordenadas["_extensao_configurada"] = True
        salvar_coordenadas(coordenadas)
        
        print("\n✅ Ótimo! Configuração salva, não vou perguntar novamente!")
        time.sleep(2)
    else:
        print("\n✅ Extensão já configurada anteriormente, continuando...")
        time.sleep(1)
    
    # =================================================================
    # PASSO 1: Capturar ícone da extensão
    # =================================================================
    if "extensao_chrome" not in coordenadas:
        coordenadas["extensao_chrome"] = capturar_coordenada(
            "extensao_chrome",
            "Posicione o mouse sobre o ÍCONE DA EXTENSÃO GCPJ no Chrome\n"
            "   (geralmente fica no canto superior direito)"
        )
        salvar_coordenadas(coordenadas)
    else:
        print(f"\n✓ extensao_chrome já existe, pulando...")
    
    time.sleep(2)
    
    # Clicar na extensão
    print(f"\n🖱️  Clicando na extensão...")
    pyautogui.click(coordenadas["extensao_chrome"]["x"], 
                    coordenadas["extensao_chrome"]["y"])
    time.sleep(1.5)
    
    # =================================================================
    # PASSO 2: Capturar campo de input
    # =================================================================
    if "input_busca" not in coordenadas:
        coordenadas["input_busca"] = capturar_coordenada(
            "input_busca",
            "Posicione o mouse sobre o CAMPO DE BUSCA/INPUT da extensão\n"
            "   (onde você digita 'GCPJ')"
        )
        salvar_coordenadas(coordenadas)
    else:
        print(f"\n✓ input_busca já existe, pulando...")
    
    time.sleep(1)
    
    # Clicar no input e digitar
    print(f"\n🖱️  Clicando no campo de busca...")
    pyautogui.click(coordenadas["input_busca"]["x"], 
                    coordenadas["input_busca"]["y"])
    time.sleep(0.3)
    
    print(f"⌨️  Digitando 'GCPJ'...")
    pyautogui.typewrite('GCPJ', interval=0.1)
    time.sleep(1)
    
    # =================================================================
    # PASSO 3: Capturar item GCPJ no menu
    # =================================================================
    if "item_gcpj_menu" not in coordenadas:
        coordenadas["item_gcpj_menu"] = capturar_coordenada(
            "item_gcpj_menu",
            "Posicione o mouse sobre o ITEM 'GCPJ' no menu suspenso\n"
            "   (que apareceu após digitar 'GCPJ')"
        )
        salvar_coordenadas(coordenadas)
    else:
        print(f"\n✓ item_gcpj_menu já existe, pulando...")
    
    time.sleep(1)
    
    # Clicar no item
    print(f"\n🖱️  Clicando no item GCPJ...")
    pyautogui.click(coordenadas["item_gcpj_menu"]["x"], 
                    coordenadas["item_gcpj_menu"]["y"])
    time.sleep(1)
    
    # =================================================================
    # PASSO 4: Capturar botão ACESSAR
    # =================================================================
    if "botao_acessar" not in coordenadas:
        coordenadas["botao_acessar"] = capturar_coordenada(
            "botao_acessar",
            "Posicione o mouse sobre o BOTÃO 'ACESSAR'\n"
            "   (que apareceu após selecionar GCPJ)"
        )
        salvar_coordenadas(coordenadas)
    else:
        print(f"\n✓ botao_acessar já existe, pulando...")
    
    time.sleep(1)
    
    # Clicar em Acessar
    print(f"\n🖱️  Clicando no botão Acessar...")
    pyautogui.click(coordenadas["botao_acessar"]["x"], 
                    coordenadas["botao_acessar"]["y"])
    
    print("⏳ Aguardando sistema GCPJ carregar (10 segundos)...")
    time.sleep(10)
    
    # Trocar para a nova aba/janela que foi aberta
    print("\n🔄 Verificando abas abertas...")
    if len(driver.window_handles) > 1:
        print(f"   Encontradas {len(driver.window_handles)} abas, trocando para a última...")
        driver.switch_to.window(driver.window_handles[-1])
    
    # Verificar se a URL está correta antes de continuar
    print("\n🔍 Verificando se o sistema carregou corretamente...")
    url_esperada = "https://juridico8.bradesco.com.br/gcpj/#redirect-completed"
    max_tentativas = 15  # 15 tentativas = até 30 segundos extras
    tentativa = 0
    url_correta = False
    
    while tentativa < max_tentativas:
        url_atual = driver.current_url
        if url_atual == url_esperada:
            print(f"✅ URL correta detectada: {url_atual}")
            url_correta = True
            break
        else:
            tentativa += 1
            print(f"⏳ Aguardando URL correta... (tentativa {tentativa}/{max_tentativas})")
            print(f"   URL atual: {url_atual}")
            time.sleep(2)
    
    if not url_correta:
        print(f"\n⚠️  URL esperada não foi detectada após {max_tentativas} tentativas")
        print(f"   Esperado: {url_esperada}")
        
        try:
            print(f"   Atual: {driver.current_url}")
        except:
            print(f"   Atual: (driver inválido)")
        
        print("\n🔄 Fechando aba problemática e tentando novamente...")
        
        try:
            # Verificar quantas abas existem
            num_abas = len(driver.window_handles)
            print(f"   Abas abertas: {num_abas}")
            
            if num_abas > 1:
                # Fechar a aba atual (última)
                driver.close()
                print("   ✓ Aba fechada")
                
                # Voltar para a primeira aba
                driver.switch_to.window(driver.window_handles[0])
                print("   ✓ Voltou para primeira aba")
            else:
                print("   ⚠️  Apenas 1 aba aberta, mantendo...")
        except Exception as e:
            print(f"   ⚠️  Erro ao gerenciar abas: {e}")
        
        time.sleep(2)
        
        # Tentar novamente: clicar na extensão até acessar
        print("\n🔄 Reiniciando processo de acesso ao GCPJ...\n")
        
        try:
            # Clicar na extensão
            print(f"\n🖱️  Clicando na extensão Chrome...")
            pyautogui.click(coordenadas["extensao_chrome"]["x"], 
                            coordenadas["extensao_chrome"]["y"])
            time.sleep(1)
            
            # Clicar no input e digitar
            print(f"\n🖱️  Clicando no campo de busca...")
            pyautogui.click(coordenadas["input_busca"]["x"], 
                            coordenadas["input_busca"]["y"])
            time.sleep(0.3)
            
            print(f"⌨️  Digitando 'GCPJ'...")
            pyautogui.typewrite('GCPJ', interval=0.1)
            time.sleep(1)
            
            # Clicar no item GCPJ
            print(f"\n🖱️  Clicando no item GCPJ...")
            pyautogui.click(coordenadas["item_gcpj_menu"]["x"], 
                            coordenadas["item_gcpj_menu"]["y"])
            time.sleep(1)
            
            # Clicar em Acessar
            print(f"\n🖱️  Clicando no botão Acessar...")
            pyautogui.click(coordenadas["botao_acessar"]["x"], 
                            coordenadas["botao_acessar"]["y"])
            
            print("⏳ Aguardando sistema GCPJ carregar (10 segundos)...")
            time.sleep(10)
        
            # Trocar para a nova aba novamente
            print("\n🔄 Verificando abas abertas...")
            if len(driver.window_handles) > 1:
                print(f"   Encontradas {len(driver.window_handles)} abas, trocando para a última...")
                driver.switch_to.window(driver.window_handles[-1])
            
            # Verificar URL novamente com loop
            print("\n🔍 Verificando URL novamente...")
            max_tentativas_retry = 15
            tentativa_retry = 0
            url_correta_retry = False
            
            while tentativa_retry < max_tentativas_retry:
                try:
                    url_atual = driver.current_url
                    if url_atual == url_esperada:
                        print(f"✅ URL correta detectada após retry: {url_atual}")
                        url_correta_retry = True
                        break
                    else:
                        tentativa_retry += 1
                        print(f"⏳ Retry: aguardando URL... ({tentativa_retry}/{max_tentativas_retry})")
                        print(f"   URL: {url_atual}")
                        time.sleep(2)
                except Exception as e:
                    print(f"   ⚠️  Erro ao verificar URL: {e}")
                    break
            
            if not url_correta_retry:
                print(f"\n❌ ERRO: Ainda não conseguiu carregar após retry")
                print("\n⚠️  Encerrando script.")
                try:
                    driver.quit()
                except:
                    pass
                return
                
        except Exception as e:
            print(f"\n❌ ERRO durante retry: {e}")
            print("⚠️  Encerrando script.")
            try:
                driver.quit()
            except:
                pass
            return
    
    time.sleep(1)
    
    print("\n✅ Sistema GCPJ carregado!")
    
    # =================================================================
    # PASSO 5: Capturar link "Consulta de Processos"
    # =================================================================
    if "link_consulta_processos" not in coordenadas:
        coordenadas["link_consulta_processos"] = capturar_coordenada(
            "link_consulta_processos",
            "Posicione o mouse sobre o link/botão 'CONSULTA DE PROCESSOS'\n"
            "   (no menu ou página inicial do GCPJ)"
        )
        salvar_coordenadas(coordenadas)
    else:
        print(f"\n✓ link_consulta_processos já existe, pulando...")
    
    time.sleep(1)
    
    # Clicar em Consulta de Processos
    print(f"\n🖱️  Clicando em Consulta de Processos...")
    pyautogui.click(coordenadas["link_consulta_processos"]["x"], 
                    coordenadas["link_consulta_processos"]["y"])
    
    print("⏳ Aguardando página carregar e campo ficar selecionado (5 segundos)...")
    time.sleep(5)
    
    # =================================================================
    # PASSO 6: Capturar campo Nº do Processo Bradesco (GCPJ)
    # =================================================================
    if "campo_numero_processo" not in coordenadas:
        print("\n⚠️  ATENÇÃO: Capture apenas o campo 'Nº do Processo Bradesco'")
        print("   NÃO capture 'Nome do Envolvido' ou outros campos!")
        coordenadas["campo_numero_processo"] = capturar_coordenada(
            "campo_numero_processo",
            "Posicione o mouse sobre o campo 'Nº DO PROCESSO BRADESCO' (GCPJ)\n"
            "   ⚠️  APENAS este campo! Não o 'Nome do Envolvido'!"
        )
        salvar_coordenadas(coordenadas)
    else:
        print(f"\n✓ campo_numero_processo já existe, usando coordenada salva...")
    
    # Ler número do processo do arquivo
    arquivo_lote = Path(__file__).parent.parent / "input" / "lote_gcpj.txt"
    
    print(f"\n🔍 Verificando arquivo: {arquivo_lote}")
    print(f"   Arquivo existe? {arquivo_lote.exists()}")
    
    if arquivo_lote.exists():
        with open(arquivo_lote, "r", encoding="utf-8") as f:
            linhas = f.readlines()
        
        print(f"\n📄 Total de linhas no arquivo: {len(linhas)}")
        
        # Pular cabeçalho (primeira linha) e pegar a segunda linha com dados
        numero_processo = ""
        if len(linhas) > 1:
            # Segunda linha contém os dados
            linha_dados = linhas[1].strip()
            print(f"   Linha de dados: '{linha_dados}'")
            
            # Extrair primeiro valor (separar por ponto-e-vírgula)
            if ';' in linha_dados:
                valores = linha_dados.split(';')
                numero_processo = valores[0].strip()
            else:
                # Se não tiver ponto-e-vírgula, pega o primeiro valor por espaço
                valores = linha_dados.split()
                numero_processo = valores[0] if valores else ""
        
        print(f"\n📄 GCPJ extraído: '{numero_processo}'")
        print(f"   Tipo: {type(numero_processo)}")
        print(f"   Tamanho: {len(numero_processo)} caracteres")
        print(f"   É numérico? {numero_processo.isdigit()}")
        
        if numero_processo and numero_processo.isdigit():
            print("\n✅ Número processo OK (é numérico), prosseguindo com digitação...")
            time.sleep(1)
            
            # Clicar no campo para garantir que está focado
            print(f"\n🖱️  Clicando no campo GCPJ nas coordenadas ({coordenadas['campo_numero_processo']['x']}, {coordenadas['campo_numero_processo']['y']})...")
            pyautogui.click(coordenadas["campo_numero_processo"]["x"], 
                            coordenadas["campo_numero_processo"]["y"])
            time.sleep(0.5)
            
            # Limpar campo antes de digitar
            print(f"🧹 Limpando campo...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.3)
            
            print(f"⌨️  INICIANDO digitação de: '{numero_processo}'")
            # Tentar com typewrite primeiro
            try:
                pyautogui.typewrite(numero_processo, interval=0.15)
                print("✅ Digitação com typewrite concluída")
            except Exception as e:
                print(f"⚠️  typewrite falhou com erro: {e}")
                print("   Tentando write...")
                pyautogui.write(numero_processo, interval=0.15)
                print("✅ Digitação com write concluída")
            
            time.sleep(1)
        else:
            print("\n❌ ERRO: numero_processo está vazio ou não é numérico!")
    else:
        print(f"\n⚠️  Arquivo {arquivo_lote} não encontrado!")
        print("💡 Crie o arquivo com um número de processo para testar")
    
    # =================================================================
    # PASSO 7: Capturar botão Buscar
    # =================================================================
    if "botao_buscar" not in coordenadas:
        coordenadas["botao_buscar"] = capturar_coordenada(
            "botao_buscar",
            "Posicione o mouse sobre o BOTÃO 'BUSCAR' ou 'PESQUISAR'\n"
            "   (para buscar o número do processo digitado)"
        )
        salvar_coordenadas(coordenadas)
    else:
        print(f"\n✓ botao_buscar já existe, usando coordenada salva...")
    
    time.sleep(1)
    
    # Clicar no botão Buscar
    print(f"\n🖱️  Clicando no botão Buscar/Pesquisar...")
    pyautogui.click(coordenadas["botao_buscar"]["x"], 
                    coordenadas["botao_buscar"]["y"])
    
    print("\n⏳ Aguardando resultado da pesquisa (5 segundos)...")
    time.sleep(5)
    
    # =================================================================
    # PASSO 8: Coletar dados da página
    # =================================================================
    print(f"\n{'='*70}")
    print("📋 COLETANDO DADOS DA PÁGINA")
    print(f"{'='*70}")
    
    try:
        # Usar Ctrl+A + Ctrl+C para copiar todo conteúdo visível
        print("\n📄 Selecionando todo conteúdo (Ctrl+A)...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        
        print("📋 Copiando para clipboard (Ctrl+C)...")
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(1)
        
        # Pegar conteúdo do clipboard
        import pyperclip
        import re
        
        conteudo_texto = pyperclip.paste()
        print(f"✅ Conteúdo copiado: {len(conteudo_texto)} caracteres")
        
        # Função para extrair valor após label
        def extrair_campo(texto, label):
            # Procurar padrão: "Label:\t\tValor" ou "Label:\tValor"
            pattern = rf"{re.escape(label)}\s*:?\s*\t+([^\t\n]+)"
            match = re.search(pattern, texto)
            if match:
                return match.group(1).strip()
            return ""
        
        # Função para extrair linha completa após label (pega tudo até quebra de linha)
        def extrair_linha_completa(texto, label):
            # Procurar padrão: "Label:\t...resto da linha..."
            pattern = rf"{re.escape(label)}\s*:\s*\t+(.*?)(?=\n|$)"
            match = re.search(pattern, texto)
            if match:
                # Pegar tudo e juntar com tab para manter formato
                linha = match.group(1).strip()
                # Substituir múltiplos tabs/espaços por um único espaço
                linha = re.sub(r'\s+', ' ', linha)
                return linha
            return ""
        
        # Ler o número GCPJ do arquivo
        arquivo_lote = Path(__file__).parent.parent / "input" / "lote_gcpj.txt"
        with open(arquivo_lote, "r", encoding="utf-8") as f:
            linhas = f.readlines()
        linha_dados = linhas[1].strip() if len(linhas) > 1 else ""
        numero_gcpj = linha_dados.split(';')[0].strip() if ';' in linha_dados else ""
        
        from datetime import datetime
        
        print("\n🔍 Extraindo campos estruturados...")
        
        # Extrair dados do processo
        dados_json = {
            "gcpj": numero_gcpj,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dados_processo": {
                "numero_processo_bradesco": extrair_campo(conteudo_texto, "Nº do Processo Bradesco"),
                "status_processo": "Processo Ativo" if "Processo Ativo" in conteudo_texto else "Processo Inativo",
                "data_cadastro": extrair_campo(conteudo_texto, "Data do Cadastro"),
                "data_movimento": extrair_campo(conteudo_texto, "Data do Movimento"),
                "departamento_juridico": extrair_campo(conteudo_texto, "Departamento Jurídico"),
                "empresa_grupo": extrair_campo(conteudo_texto, "Empresa Grupo"),
                "compartilhado": extrair_campo(conteudo_texto, "Compartilhado"),
                "dep_envolvida": extrair_campo(conteudo_texto, "Dep. Envolvida"),
                "orgao_julgador": extrair_campo(conteudo_texto, "Órgão Julgador"),
                "comarca": extrair_campo(conteudo_texto, "Comarca"),
                "tribunal": extrair_campo(conteudo_texto, "Tribunal"),
                "numero_processo_judicial": extrair_campo(conteudo_texto, "Nº do Processo Judicial"),
                "valor_causa": extrair_campo(conteudo_texto, "Valor da Causa R$"),
                "valor_causa_atualizado": extrair_campo(conteudo_texto, "Valor da Causa Atualiz. R$"),
                "data_fato_gerador": extrair_campo(conteudo_texto, "Data do Fato Gerador"),
                "data_distrib_orgao_julgador": extrair_campo(conteudo_texto, "Data Distrib. O. Julgador"),
                "origem_cnj": extrair_campo(conteudo_texto, "Origem CNJ"),
                "comunicacoes": extrair_campo(conteudo_texto, "Comunicações")
            },
            "classificacao": {
                "tipo_processo": extrair_campo(conteudo_texto, "Tipo de Processo"),
                "risco_acao": extrair_campo(conteudo_texto, "Risco da Ação"),
                "tipo_acao": extrair_campo(conteudo_texto, "Tipo de Ação"),
                "nome_acao": extrair_campo(conteudo_texto, "Nome de Ação"),
                "preocupante": extrair_campo(conteudo_texto, "Preocupante")
            },
            "detalhamento": {
                "pedido": ""
            },
            "envolvidos": [],
            "advogados": [],
            "dados_dependencia": {},
            "contratos": []
        }
        
        # Extrair Detalhamento Classificação (tabela)
        print("🔍 Extraindo Detalhamento Classificação...")
        detalhamento_match = re.search(r'Detalhamento Classificação\s+Pedido\s+(.*?)(?=\n\n|Advogado/Procurador|Envolvidos|$)', conteudo_texto, re.DOTALL)
        if detalhamento_match:
            pedido_completo = detalhamento_match.group(1).strip()
            # Pegar apenas a primeira linha (antes de qualquer quebra ou texto de paginação)
            pedido_valor = pedido_completo.split('\n')[0].split('\r')[0].strip()
            # Remover texto de paginação se houver
            pedido_valor = re.sub(r'(primeira página|página anterior|página posterior|última página|\[\d+\]).*', '', pedido_valor).strip()
            dados_json["detalhamento"]["pedido"] = pedido_valor
            print(f"   ✅ Pedido: {pedido_valor}")
        else:
            print(f"   ⚠️  Não encontrou Detalhamento Classificação")
        
        # Extrair tabela de Envolvidos
        print("🔍 Extraindo tabela de Envolvidos...")
        envolvidos_match = re.search(r'Envolvidos\s+Nome\s+Documento\s+Tipo Envolvido\s+Seq\.\s+(.*?)(?=\n\n|\nClassificação|Advogado)', conteudo_texto, re.DOTALL)
        if envolvidos_match:
            linhas_envolvidos = envolvidos_match.group(1).strip().split('\n')
            for linha in linhas_envolvidos:
                # Padrão: Nome\tDocumento\tTipo\tSeq
                partes = [p.strip() for p in linha.split('\t') if p.strip()]
                if len(partes) >= 4:
                    dados_json["envolvidos"].append({
                        "nome": partes[0],
                        "documento": partes[1],
                        "tipo": partes[2],
                        "sequencia": partes[3]
                    })
        
        print(f"   ✅ {len(dados_json['envolvidos'])} envolvidos extraídos")
        
        # Capturar HTML completo da página para referência
        print("\n📄 Capturando HTML completo da página...")
        page_source = driver.page_source if driver else ""
        print(f"   ✅ HTML capturado: {len(page_source)} caracteres")
        
        # =================================================================
        # PASSO 8.1: Capturar coordenada e clicar no primeiro envolvido
        # =================================================================
        if dados_json['envolvidos']:
            print(f"\n{'='*70}")
            print("📋 COLETANDO DADOS DETALHADOS DO PRIMEIRO ENVOLVIDO")
            print(f"{'='*70}")
            
            # Capturar coordenada do primeiro nome na tabela
            if "primeiro_envolvido_link" not in coordenadas:
                print("\n⚠️  É necessário capturar a coordenada do primeiro nome na tabela Envolvidos")
                coordenadas["primeiro_envolvido_link"] = capturar_coordenada(
                    "primeiro_envolvido_link",
                    "Posicione o mouse sobre o PRIMEIRO NOME na tabela de Envolvidos\n"
                    f"   (Clique em: {dados_json['envolvidos'][0]['nome']})"
                )
                salvar_coordenadas(coordenadas)
            else:
                print(f"\n✓ primeiro_envolvido_link já existe, usando coordenada salva...")
            
            # Clicar no primeiro envolvido
            print(f"\n🖱️  Clicando no primeiro envolvido: {dados_json['envolvidos'][0]['nome']}...")
            pyautogui.click(coordenadas["primeiro_envolvido_link"]["x"], 
                            coordenadas["primeiro_envolvido_link"]["y"])
            
            print("⏳ Aguardando modal abrir (3 segundos)...")
            time.sleep(3)
            
            # Capturar coordenada dentro do modal para dar foco
            if "dentro_modal_envolvido" not in coordenadas:
                print("\n⚠️  É necessário capturar uma coordenada DENTRO do modal")
                coordenadas["dentro_modal_envolvido"] = capturar_coordenada(
                    "dentro_modal_envolvido",
                    "Posicione o mouse em qualquer ÁREA DE TEXTO dentro do modal\n"
                    "   (Pode ser no título 'Dados da Dependência' ou qualquer texto)"
                )
                salvar_coordenadas(coordenadas)
            else:
                print(f"\n✓ dentro_modal_envolvido já existe, usando coordenada salva...")
            
            # Clicar dentro do modal para dar foco
            print(f"\n🖱️  Clicando dentro do modal para dar foco...")
            pyautogui.click(coordenadas["dentro_modal_envolvido"]["x"], 
                            coordenadas["dentro_modal_envolvido"]["y"])
            time.sleep(1)
            
            try:
                # AGORA sim copiar dados do modal (depois de dar foco)
                print("\n📄 Copiando dados do modal (Ctrl+A + Ctrl+C)...")
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(1)
                
                conteudo_modal = pyperclip.paste()
                print(f"✅ Conteúdo do modal copiado: {len(conteudo_modal)} caracteres")
                
                # Extrair dados do modal
                print("🔍 Extraindo dados da dependência...")
                dados_dependencia = {
                    "dependencia": extrair_linha_completa(conteudo_modal, "Dependência"),
                    "dir_regional": extrair_linha_completa(conteudo_modal, "Dir. Regional"),
                    "ger_regional": extrair_linha_completa(conteudo_modal, "Ger. Regional"),
                    "empresa_inc": extrair_linha_completa(conteudo_modal, "Empresa Inc"),
                    "cod_natureza": extrair_campo(conteudo_modal, "Cód. Natureza"),
                    "gerente": extrair_linha_completa(conteudo_modal, "Gerente"),
                    "email": extrair_campo(conteudo_modal, "Email")
                }
                
                # Adicionar dados ao JSON principal (não dentro do envolvido)
                dados_json['dados_dependencia'] = dados_dependencia
                
                print(f"   ✅ Dados da dependência extraídos:")
                print(f"      - Dependência: {dados_dependencia['dependencia']}")
                print(f"      - Gerente: {dados_dependencia['gerente']}")
                print(f"      - Email: {dados_dependencia['email']}")
                
            except Exception as e:
                print(f"\n⚠️  Erro ao processar modal: {e}")
            
            # Capturar coordenada do botão fechar modal
            if "fechar_modal_envolvido" not in coordenadas:
                print("\n⚠️  É necessário capturar a coordenada do botão FECHAR (X)")
                coordenadas["fechar_modal_envolvido"] = capturar_coordenada(
                    "fechar_modal_envolvido",
                    "Posicione o mouse sobre o BOTÃO FECHAR do modal\n"
                    "   (Geralmente um X no canto superior)"
                )
                salvar_coordenadas(coordenadas)
            else:
                print(f"\n✓ fechar_modal_envolvido já existe, usando coordenada salva...")
            
            # Fechar modal clicando no X
            print("\n❌ Fechando modal...")
            pyautogui.click(coordenadas["fechar_modal_envolvido"]["x"], 
                            coordenadas["fechar_modal_envolvido"]["y"])
            time.sleep(2)
        
        # =================================================================
        # PASSO 8.2: Clicar no botão "Contratos" usando reconhecimento de imagem
        # =================================================================
        print(f"\n{'='*70}")
        print("🔍 PROCURANDO BOTÃO 'CONTRATOS' POR RECONHECIMENTO DE IMAGEM")
        print(f"{'='*70}")
        
        # Rolar página para baixo primeiro
        print("\n⬇️  Rolando página para baixo...")
        for i in range(3):
            pyautogui.scroll(-300)  # Rolar para baixo
            time.sleep(0.5)
        
        # Caminho da imagem do botão
        pasta_assets = Path(__file__).parent.parent / "assets"
        pasta_assets.mkdir(exist_ok=True)
        imagem_botao = pasta_assets / "btn_contratos.png"
        
        if not imagem_botao.exists():
            print(f"\n⚠️  IMAGEM NÃO ENCONTRADA!")
            print(f"   Salve um print do botão 'Contratos' em:")
            print(f"   {imagem_botao}")
            print(f"\n   Instruções:")
            print(f"   1. Faça print da tela com o botão 'Contratos' visível")
            print(f"   2. Recorte APENAS o botão (pequeno retângulo)")
            print(f"   3. Salve como: {imagem_botao.name}")
            print(f"   4. Execute o script novamente")
            raise FileNotFoundError(f"Imagem não encontrada: {imagem_botao}")
        
        # Tentar localizar o botão na tela (máximo 5 tentativas)
        print(f"\n🔍 Procurando botão na tela...")
        print(f"   Imagem: {imagem_botao.name}")
        
        botao_encontrado = None
        max_tentativas = 5
        
        for tentativa in range(1, max_tentativas + 1):
            print(f"\n   Tentativa {tentativa}/{max_tentativas}...")
            
            try:
                # Usar Pillow/PyAutoGUI para comparação exata
                localizacao = pyautogui.locateOnScreen(str(imagem_botao), grayscale=True)
                
                if localizacao:
                    botao_encontrado = localizacao
                    print(f"   ✅ Botão encontrado! Posição: {localizacao}")
                    break
                else:
                    print(f"   ⚠️  Botão não encontrado nesta tentativa")
                    
            except Exception as e:
                print(f"   ⚠️  Erro na busca: {e}")
            
            # Se não encontrou, rolar mais e tentar novamente
            if tentativa < max_tentativas:
                print(f"   ⬇️  Rolando mais para baixo...")
                pyautogui.scroll(-200)
                time.sleep(1)
        
        if not botao_encontrado:
            print(f"\n❌ BOTÃO NÃO ENCONTRADO após {max_tentativas} tentativas!")
            print(f"   Verifique se:")
            print(f"   1. A imagem {imagem_botao.name} corresponde exatamente ao botão na tela")
            print(f"   2. O botão está visível (tente rolar manualmente)")
            print(f"   3. A resolução da tela está igual a quando tirou o print")
            raise Exception("Botão Contratos não encontrado")
        
        # Clicar no centro do botão encontrado
        centro_x = botao_encontrado.left + botao_encontrado.width // 2
        centro_y = botao_encontrado.top + botao_encontrado.height // 2
        
        print(f"\n🖱️  Clicando no botão Contratos...")
        print(f"   Posição: ({centro_x}, {centro_y})")
        pyautogui.click(centro_x, centro_y)
        time.sleep(3)
        
        print("✅ Clique realizado com sucesso!")
        print("   ⏳ Aguardando modal abrir...")
        time.sleep(2)
        
        # Rolar página para cima após abrir modal
        print("\n⬆️  Rolando página para cima...")
        for i in range(5):
            pyautogui.scroll(300)  # Rolar para cima
            time.sleep(0.3)
        
        # =================================================================
        # PASSO 8.3: Extrair dados do modal de Contratos
        # =================================================================
        print(f"\n{'='*70}")
        print("📋 EXTRAINDO DADOS DO MODAL DE CONTRATOS")
        print(f"{'='*70}")
        
        # Capturar coordenada dentro do modal Contratos
        if "dentro_modal_contratos" not in coordenadas:
            print("\n⚠️  É necessário capturar a coordenada DENTRO do modal de Contratos")
            coordenadas["dentro_modal_contratos"] = capturar_coordenada(
                "dentro_modal_contratos",
                "Posicione o mouse DENTRO do modal de Contratos\n"
                "   (Em alguma área vazia ou na tabela de contratos)\n"
                "   Isso dará foco ao modal para copiar o conteúdo"
            )
            salvar_coordenadas(coordenadas)
        else:
            print(f"\n✓ dentro_modal_contratos já existe, usando coordenada salva...")
        
        # Clicar dentro do modal para dar foco
        print("\n🖱️  Clicando dentro do modal Contratos para dar foco...")
        pyautogui.click(coordenadas["dentro_modal_contratos"]["x"], 
                        coordenadas["dentro_modal_contratos"]["y"])
        time.sleep(1)
        
        # Copiar conteúdo do modal (Ctrl+A + Ctrl+C)
        print("\n📄 Copiando dados do modal (Ctrl+A + Ctrl+C)...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(1)
        
        conteudo_modal_contratos = pyperclip.paste()
        print(f"✅ Conteúdo do modal copiado: {len(conteudo_modal_contratos)} caracteres")
        
        # Extrair tabela de Contratos
        print("\n🔍 Extraindo tabela de Contratos...")
        contratos_match = re.search(
            r'Contratos\s+Agência\s+Conta\s+Carteira\s+Nº Contrato\s+Sequencia\s+Nome Envolvido\s+Data da Safra\s+(.*?)(?=primeira página|$)', 
            conteudo_modal_contratos, 
            re.DOTALL
        )
        
        if contratos_match:
            linhas_contratos = contratos_match.group(1).strip().split('\n')
            for linha in linhas_contratos:
                # Ignorar linhas vazias ou de paginação
                if not linha.strip() or 'página' in linha.lower():
                    continue
                    
                # Padrão: Agência\tConta\tCarteira\tNº Contrato\tSequencia\tNome Envolvido\tData da Safra
                partes = [p.strip() for p in linha.split('\t') if p.strip()]
                if len(partes) >= 6:
                    dados_json["contratos"].append({
                        "agencia": partes[0],
                        "conta": partes[1],
                        "carteira": partes[2],
                        "numero_contrato": partes[3],
                        "sequencia": partes[4],
                        "nome_envolvido": partes[5],
                        "data_safra": partes[6] if len(partes) >= 7 else ""
                    })
                    print(f"   ✅ Contrato: {partes[3]} - {partes[5]}")
        
        print(f"\n   ✅ {len(dados_json['contratos'])} contrato(s) extraído(s)")
        
        # Fechar modal de Contratos (reutilizar coordenada do X do modal anterior)
        print("\n❌ Fechando modal de Contratos...")
        pyautogui.click(coordenadas["fechar_modal_envolvido"]["x"], 
                        coordenadas["fechar_modal_envolvido"]["y"])
        time.sleep(2)
        
        print("✅ Modal de Contratos processado!")
        
        # =================================================================
        # PASSO 9: Voltar ao menu de Consulta (2 cliques)
        # =================================================================
        print(f"\n{'='*70}")
        print("🔙 VOLTANDO PARA O MENU DE CONSULTA")
        print(f"{'='*70}")
        
        # Primeiro clique para voltar
        if "voltar_clique_1" not in coordenadas:
            print("\n⚠️  É necessário capturar a coordenada do PRIMEIRO clique para voltar")
            coordenadas["voltar_clique_1"] = capturar_coordenada(
                "voltar_clique_1",
                "Posicione o mouse sobre o PRIMEIRO elemento para voltar\n"
                "   (Pode ser um botão Voltar, link, ou ícone de retorno)"
            )
            salvar_coordenadas(coordenadas)
        else:
            print(f"\n✓ voltar_clique_1 já existe, usando coordenada salva...")
        
        print("\n🖱️  Executando primeiro clique para voltar...")
        pyautogui.click(coordenadas["voltar_clique_1"]["x"], 
                        coordenadas["voltar_clique_1"]["y"])
        time.sleep(2)
        
        # Segundo clique para acessar Consulta novamente
        if "voltar_clique_2" not in coordenadas:
            print("\n⚠️  É necessário capturar a coordenada do SEGUNDO clique")
            coordenadas["voltar_clique_2"] = capturar_coordenada(
                "voltar_clique_2",
                "Posicione o mouse sobre o SEGUNDO elemento\n"
                "   (Link 'Consulta' ou menu para retornar à tela de consulta)"
            )
            salvar_coordenadas(coordenadas)
        else:
            print(f"\n✓ voltar_clique_2 já existe, usando coordenada salva...")
        
        print("\n🖱️  Executando segundo clique para acessar Consulta...")
        pyautogui.click(coordenadas["voltar_clique_2"]["x"], 
                        coordenadas["voltar_clique_2"]["y"])
        time.sleep(2)
        
        print("✅ Retornado ao menu de Consulta!")
        
        # Extrair tabela de Advogados/Procuradores
        print("🔍 Extraindo tabela de Advogados...")
        advogados_match = re.search(r'Advogado/Procurador\s+Tipo\s+Nome\s+OAB\s+(.*?)(?=\n\n|$)', conteudo_texto, re.DOTALL)
        if advogados_match:
            linhas_advogados = advogados_match.group(1).strip().split('\n')
            for linha in linhas_advogados:
                # Padrão: Tipo\tNome\tOAB (ou às vezes Nome sem OAB)
                partes = [p.strip() for p in linha.split('\t') if p.strip()]
                if len(partes) >= 2:
                    dados_json["advogados"].append({
                        "tipo": partes[0],
                        "nome": partes[1],
                        "oab": partes[2] if len(partes) >= 3 else ""
                    })
        
        print(f"   ✅ {len(dados_json['advogados'])} advogados extraídos")
        
        # Salvar JSON na pasta output
        pasta_output = Path(__file__).parent.parent / "output"
        pasta_output.mkdir(exist_ok=True)
        
        arquivo_json = pasta_output / f"dados_{numero_gcpj}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(arquivo_json, "w", encoding="utf-8") as f:
            json.dump(dados_json, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Dados estruturados extraídos!")
        print(f"   - Campos do processo: {len([v for v in dados_json['dados_processo'].values() if v])} preenchidos")
        print(f"   - Envolvidos: {len(dados_json['envolvidos'])} registros")
        print(f"   - Advogados: {len(dados_json['advogados'])} registros")
        print(f"\n💾 Dados salvos em: {arquivo_json}")
        print(f"   Arquivo: {arquivo_json.name}")
        
    except Exception as e:
        print(f"\n⚠️  Erro ao coletar dados: {e}")
        import traceback
        traceback.print_exc()
        
        # Função auxiliar para extrair texto
        def extrair_texto(texto_busca):
            try:
                # Procurar pelo label e pegar o próximo elemento ou texto
                elementos = soup.find_all(string=lambda text: texto_busca in text if text else False)
                if elementos:
                    # Pegar o pai e próximo sibling ou conteúdo
                    for elem in elementos:
                        parent = elem.parent
                        if parent:
                            # Tentar pegar próximo td ou próximo texto
                            next_td = parent.find_next('td')
                            if next_td:
                                return next_td.get_text(strip=True)
                return ""
            except:
                return ""
        
        # Ler o número GCPJ do arquivo
        arquivo_lote = Path(__file__).parent.parent / "input" / "lote_gcpj.txt"
        with open(arquivo_lote, "r", encoding="utf-8") as f:
            linhas = f.readlines()
        linha_dados = linhas[1].strip() if len(linhas) > 1 else ""
        numero_gcpj = linha_dados.split(';')[0].strip() if ';' in linha_dados else ""
        
        # Extrair dados estruturados
        from datetime import datetime
        
        dados_json = {
            "gcpj": numero_gcpj,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dados_processo": {
                "numero_processo_bradesco": extrair_texto("Nº do Processo Bradesco:"),
                "status_processo": extrair_texto("Processo Ativo") or extrair_texto("Processo Inativo"),
                "data_cadastro": extrair_texto("Data do Cadastro:"),
                "data_movimento": extrair_texto("Data do Movimento:"),
                "departamento_juridico": extrair_texto("Departamento Jurídico:"),
                "empresa_grupo": extrair_texto("Empresa Grupo:"),
                "compartilhado": extrair_texto("Compartilhado:"),
                "dep_envolvida": extrair_texto("Dep. Envolvida:"),
                "orgao_julgador": extrair_texto("Órgão Julgador:"),
                "comarca": extrair_texto("Comarca:"),
                "tribunal": extrair_texto("Tribunal:"),
                "numero_processo_judicial": extrair_texto("Nº do Processo Judicial:"),
                "valor_causa": extrair_texto("Valor da Causa R$:"),
                "valor_causa_atualizado": extrair_texto("Valor da Causa Atualiz. R$:"),
                "data_fato_gerador": extrair_texto("Data do Fato Gerador:"),
                "data_distrib_orgao_julgador": extrair_texto("Data Distrib. O. Julgador:"),
                "origem_cnj": extrair_texto("Origem CNJ:"),
                "comunicacoes": extrair_texto("Comunicações:")
            },
            "classificacao": {
                "tipo_processo": extrair_texto("Tipo de Processo:"),
                "risco_acao": extrair_texto("Risco da Ação:"),
                "tipo_acao": extrair_texto("Tipo de Ação:"),
                "nome_acao": extrair_texto("Nome de Ação:"),
                "preocupante": extrair_texto("Preocupante:")
            },
            "detalhamento": {
                "pedido": extrair_texto("Pedido")
            },
            "envolvidos": [],
            "advogados": [],
            "html_completo": driver.page_source if driver else ""  # Guardando HTML completo para referência
        }
        
        # Extrair envolvidos (tabela)
        try:
            # Procurar tabela de envolvidos
            envolvidos_section = soup.find(string="Envolvidos")
            if envolvidos_section:
                tabela = envolvidos_section.find_next('table')
                if tabela:
                    linhas_tabela = tabela.find_all('tr')[1:]  # Pular cabeçalho
                    for linha in linhas_tabela:
                        colunas = linha.find_all('td')
                        if len(colunas) >= 4:
                            dados_json["envolvidos"].append({
                                "nome": colunas[0].get_text(strip=True),
                                "documento": colunas[1].get_text(strip=True),
                                "tipo": colunas[2].get_text(strip=True),
                                "sequencia": colunas[3].get_text(strip=True)
                            })
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair envolvidos: {e}")
        
        # Extrair advogados
        try:
            advogado_section = soup.find(string="Advogado/Procurador")
            if advogado_section:
                tabela = advogado_section.find_next('table')
                if tabela:
                    linhas_tabela = tabela.find_all('tr')[1:]  # Pular cabeçalho
                    for linha in linhas_tabela:
                        colunas = linha.find_all('td')
                        if len(colunas) >= 3:
                            dados_json["advogados"].append({
                                "tipo": colunas[0].get_text(strip=True),
                                "nome": colunas[1].get_text(strip=True),
                                "oab": colunas[2].get_text(strip=True)
                            })
        except Exception as e:
            print(f"   ⚠️  Erro ao extrair advogados: {e}")
        
        # Salvar JSON na pasta output
        pasta_output = Path(__file__).parent.parent / "output"
        pasta_output.mkdir(exist_ok=True)
        
        arquivo_json = pasta_output / f"dados_{numero_gcpj}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(arquivo_json, "w", encoding="utf-8") as f:
            json.dump(dados_json, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Dados estruturados extraídos!")
        print(f"   - Dados do processo: {len([k for k,v in dados_json['dados_processo'].items() if v])} campos preenchidos")
        print(f"   - Envolvidos: {len(dados_json['envolvidos'])} registros")
        print(f"   - Advogados: {len(dados_json['advogados'])} registros")
        print(f"\n💾 Dados salvos em: {arquivo_json}")
        print(f"   Arquivo: {arquivo_json.name}")
        
    except Exception as e:
        print(f"\n⚠️  Erro ao coletar dados: {e}")
        import traceback
        traceback.print_exc()
    
    # =================================================================
    # FINALIZAR
    # =================================================================
    print(f"\n{'='*70}")
    print(f"💾 TODAS AS COORDENADAS SALVAS!")
    print(f"{'='*70}")
    
    print(f"\n📄 Arquivo: {ARQUIVO_COORDENADAS}")
    
    print("\n📋 Total de coordenadas:")
    for nome, coord in coordenadas.items():
        # Pular flags booleanas (como _extensao_configurada)
        if isinstance(coord, dict) and 'x' in coord and 'y' in coord:
            print(f"   ✓ {nome}: X={coord['x']}, Y={coord['y']}")
    
    print("\n" + "="*70)
    print("🎉 CAPTURA CONCLUÍDA!")
    print("="*70)
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Verifique se as coordenadas estão corretas")
    print("   2. Execute: python src/gcpj_processar_lote.py")
    print("\n⚠️  Se algo não funcionar, execute este script novamente!\n")
    
    # Perguntar se quer fechar o Chrome
    print("="*70)
    fechar = input("\n❓ Deseja fechar o Chrome agora? (s/n): ").strip().lower()
    
    if fechar == 's':
        print("🔴 Fechando Chrome...")
        if driver:
            driver.quit()
        print("✅ Chrome fechado!")
    else:
        print("💡 Chrome permanecerá aberto.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Captura cancelada pelo usuário!")
        if driver:
            print("🔴 Fechando Chrome...")
            driver.quit()
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        if driver:
            print("🔴 Fechando Chrome...")
            driver.quit()
