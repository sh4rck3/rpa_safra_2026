#!/usr/bin/env python3
"""
Session Manager - Gerencia o ciclo de vida do Chrome e sessão do GCPJ
"""

import os
import time
import json
import threading
import pyautogui
import pyperclip
from datetime import datetime
from typing import Optional
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Desabilitar failsafe do pyautogui
pyautogui.FAILSAFE = False


class SessionManager:
    """Classe responsável por gerenciar a sessão do Chrome para GCPJ"""
    
    # Estados possíveis
    AGUARDANDO = "AGUARDANDO"  # API pronta, aguardando requisição (Chrome fechado)
    LOGANDO = "LOGANDO"
    OCIOSO_LOGADO = "OCIOSO_LOGADO"
    PROCESSANDO = "PROCESSANDO"
    
    def __init__(self):
        self.estado = self.AGUARDANDO  # Inicia AGUARDANDO requisição
        self.driver = None
        self.wait = None
        self.last_activity = None
        self.timeout_inatividade = int(os.getenv('TIMEOUT_INATIVIDADE', 600))  # 10 minutos padrão
        
        # Coordenadas (serão carregadas do arquivo)
        self.coordenadas = {}
        self._carregar_coordenadas()
        
        # Lock para thread-safety
        self.lock = threading.Lock()
        
        # Iniciar thread de monitoramento de inatividade
        self.monitor_thread = threading.Thread(target=self._monitor_inatividade, daemon=True)
        self.monitor_thread.start()
        
        print(f"✓ SessionManager GCPJ inicializado")
        print(f"  Timeout de inatividade: {self.timeout_inatividade}s ({self.timeout_inatividade // 60} minutos)")
        print(f"  Coordenadas carregadas: {len(self.coordenadas)}")
    
    def _carregar_coordenadas(self):
        """Carrega coordenadas do arquivo JSON"""
        arquivo_coordenadas = Path(__file__).parent.parent / "coordenadas_gcpj.json"
        
        if not arquivo_coordenadas.exists():
            print(f"⚠️  Arquivo de coordenadas não encontrado: {arquivo_coordenadas}")
            print(f"   Execute: python src/gcpj_capturar_coordenadas.py")
            return
        
        try:
            with open(arquivo_coordenadas, "r", encoding="utf-8") as f:
                self.coordenadas = json.load(f)
            
            # Filtrar apenas coordenadas válidas (ignorar flags como _extensao_configurada)
            self.coordenadas = {
                k: v for k, v in self.coordenadas.items() 
                if isinstance(v, dict) and 'x' in v and 'y' in v
            }
            
            print(f"✓ Coordenadas carregadas: {list(self.coordenadas.keys())}")
        except Exception as e:
            print(f"❌ Erro ao carregar coordenadas: {e}")
    
    def get_estado(self) -> str:
        """Retorna o estado atual"""
        with self.lock:
            return self.estado
    
    def is_chrome_open(self) -> bool:
        """Verifica se o Chrome está aberto"""
        with self.lock:
            return self.driver is not None
    
    def is_pronto_para_processar(self) -> bool:
        """Verifica se está pronto para processar (logado e ocioso)"""
        with self.lock:
            return self.estado == self.OCIOSO_LOGADO
    
    def abrir_chrome_e_logar(self):
        """Abre o Chrome e faz login completo até a tela de consulta"""
        
        with self.lock:
            if self.driver is not None:
                print("   ℹ️  Chrome já está aberto")
                return
            
            self.estado = self.LOGANDO
        
        try:
            print("\n🌐 Abrindo Chrome com perfil persistente...")
            
            # Configurar Chrome
            chrome_options = Options()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Perfil dedicado para o Selenium (na pasta do projeto)
            profile_dir = Path(__file__).parent.parent / "chrome_profile"
            profile_dir.mkdir(exist_ok=True)
            chrome_options.add_argument(f"--user-data-dir={profile_dir.absolute()}")
            
            # Criar driver
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"⚠️  Erro ao instalar ChromeDriver: {e}")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.wait = WebDriverWait(self.driver, 30)
            self.driver.get("about:blank")
            
            print("✅ Chrome aberto!")
            time.sleep(2)
            
            # Fazer login completo
            print("\n🔑 Fazendo login no GCPJ...")
            self._executar_login_completo()
            
            with self.lock:
                self.estado = self.OCIOSO_LOGADO
                self.last_activity = time.time()
            
            print("✅ Login completo! Estado: OCIOSO_LOGADO")
            print("   Pronto para processar GCPJs!\n")
            
        except Exception as e:
            print(f"❌ Erro ao abrir Chrome: {e}")
            with self.lock:
                self.estado = self.FECHADO
                self.driver = None
            raise
    
    def _executar_login_completo(self):
        """Executa o login completo no GCPJ até chegar na tela de consulta"""
        
        print("   1. Clicando na extensão GCPJ...")
        coord = self.coordenadas.get("extensao_chrome")
        if not coord:
            raise Exception("Coordenada 'extensao_chrome' não encontrada")
        pyautogui.click(coord["x"], coord["y"])
        time.sleep(1.5)
        
        print("   2. Clicando no campo de busca...")
        coord = self.coordenadas.get("input_busca")
        if not coord:
            raise Exception("Coordenada 'input_busca' não encontrada")
        pyautogui.click(coord["x"], coord["y"])
        time.sleep(0.5)
        
        print("   3. Digitando 'GCPJ'...")
        pyautogui.write("GCPJ", interval=0.1)
        time.sleep(0.5)
        
        print("   4. Clicando em 'GCPJ' no menu...")
        coord = self.coordenadas.get("item_gcpj_menu")
        if not coord:
            raise Exception("Coordenada 'item_gcpj_menu' não encontrada")
        pyautogui.click(coord["x"], coord["y"])
        time.sleep(1.5)
        
        print("   5. Clicando em 'ACESSAR'...")
        coord = self.coordenadas.get("botao_acessar")
        if not coord:
            raise Exception("Coordenada 'botao_acessar' não encontrada")
        pyautogui.click(coord["x"], coord["y"])
        
        print("   ⏳ Aguardando sistema GCPJ carregar (10 segundos)...")
        time.sleep(10)
        
        # Trocar para a nova aba/janela que foi aberta
        print("\n   🔄 Verificando abas abertas...")
        if len(self.driver.window_handles) > 1:
            print(f"      Encontradas {len(self.driver.window_handles)} abas, trocando para a última...")
            self.driver.switch_to.window(self.driver.window_handles[-1])
        
        # Verificar se a URL está correta antes de continuar
        print("\n   🔍 Verificando se o sistema carregou corretamente...")
        url_esperada = "https://juridico8.bradesco.com.br/gcpj/#redirect-completed"
        max_tentativas = 15
        tentativa = 0
        url_correta = False
        
        while tentativa < max_tentativas:
            url_atual = self.driver.current_url
            if url_atual == url_esperada:
                print(f"      ✅ URL correta detectada: {url_atual}")
                url_correta = True
                break
            else:
                tentativa += 1
                print(f"      ⏳ Aguardando URL correta... (tentativa {tentativa}/{max_tentativas})")
                print(f"         URL atual: {url_atual}")
                time.sleep(2)
        
        if not url_correta:
            raise Exception(f"URL esperada não foi detectada após {max_tentativas} tentativas. Esperado: {url_esperada}, Atual: {self.driver.current_url}")
        
        print("   6. Clicando em 'Consulta de Processos'...")
        coord = self.coordenadas.get("link_consulta_processos")
        if not coord:
            raise Exception("Coordenada 'link_consulta_processos' não encontrada")
        pyautogui.click(coord["x"], coord["y"])
        time.sleep(2)
        
        print("   ✅ Chegou na tela de consulta!")
    
    def _navegar_para_gcpj(self):
        """Navega para GCPJ (usado em retry de aba)
        
        Realiza apenas a parte de navegação (extensão → GCPJ → Acessar → Consulta)
        assumindo que o Chrome já está aberto
        """
        print("\n   🔄 Navegando para GCPJ...")
        
        print("   1. Clicando na extensão GCPJ...")
        coord = self.coordenadas.get("extensao_chrome")
        if not coord:
            raise Exception("Coordenada 'extensao_chrome' não encontrada")
        pyautogui.click(coord["x"], coord["y"])
        time.sleep(1.5)
        
        print("   2. Clicando no campo de busca...")
        coord = self.coordenadas.get("input_busca")
        if not coord:
            raise Exception("Coordenada 'input_busca' não encontrada")
        pyautogui.click(coord["x"], coord["y"])
        time.sleep(0.5)
        
        print("   3. Digitando 'GCPJ'...")
        pyautogui.write("GCPJ", interval=0.1)
        time.sleep(0.5)
        
        print("   4. Clicando em 'GCPJ' no menu...")
        coord = self.coordenadas.get("item_gcpj_menu")
        if not coord:
            raise Exception("Coordenada 'item_gcpj_menu' não encontrada")
        pyautogui.click(coord["x"], coord["y"])
        time.sleep(1.5)
        
        print("   5. Clicando em 'ACESSAR'...")
        coord = self.coordenadas.get("botao_acessar")
        if not coord:
            raise Exception("Coordenada 'botao_acessar' não encontrada")
        pyautogui.click(coord["x"], coord["y"])
        
        print("   ⏳ Aguardando sistema GCPJ carregar (10 segundos)...")
        time.sleep(10)
        
        # Trocar para a nova aba/janela que foi aberta
        print("\n   🔄 Verificando abas abertas...")
        if len(self.driver.window_handles) > 1:
            print(f"      Encontradas {len(self.driver.window_handles)} abas, trocando para a última...")
            self.driver.switch_to.window(self.driver.window_handles[-1])
        
        # Verificar se a URL está correta
        print("\n   🔍 Verificando se o sistema carregou corretamente...")
        url_esperada = "https://juridico8.bradesco.com.br/gcpj/#redirect-completed"
        max_tentativas = 15
        tentativa = 0
        url_correta = False
        
        while tentativa < max_tentativas:
            url_atual = self.driver.current_url
            if url_atual == url_esperada:
                print(f"      ✅ URL correta detectada: {url_atual}")
                url_correta = True
                break
            else:
                tentativa += 1
                print(f"      ⏳ Aguardando URL correta... (tentativa {tentativa}/{max_tentativas})")
                print(f"         URL atual: {url_atual}")
                time.sleep(2)
        
        if not url_correta:
            raise Exception(f"URL esperada não foi detectada após {max_tentativas} tentativas. Esperado: {url_esperada}, Atual: {self.driver.current_url}")
        
        print("   6. Clicando em 'Consulta de Processos'...")
        coord = self.coordenadas.get("link_consulta_processos")
        if not coord:
            raise Exception("Coordenada 'link_consulta_processos' não encontrada")
        pyautogui.click(coord["x"], coord["y"])
        time.sleep(2)
        
        print("   ✅ Navegação completa!")
    
    def atualizar_atividade(self):
        """Atualiza timestamp da última atividade"""
        with self.lock:
            self.last_activity = time.time()
    
    def fechar_chrome(self):
        """Fecha o Chrome gracefully"""
        with self.lock:
            if self.driver:
                try:
                    print("🔴 Fechando Chrome (sessão expirou após inatividade)...")
                    self.driver.quit()
                except:
                    pass
                finally:
                    self.driver = None
                    self.wait = None
                    self.estado = self.AGUARDANDO  # Volta para AGUARDANDO (não FECHADO)
                    self.last_activity = None
                    print("✅ Chrome fechado. Estado: AGUARDANDO (pronto para próxima requisição)")
    
    def voltar_para_consulta(self):
        """Volta para a tela de consulta (2 cliques) e muda estado para OCIOSO_LOGADO"""
        print("\n🔙 Voltando para tela de consulta...")
        
        # Primeiro clique
        coord = self.coordenadas.get("voltar_clique_1")
        if coord:
            print("   1. Primeiro clique...")
            pyautogui.click(coord["x"], coord["y"])
            time.sleep(2)
        
        # Segundo clique
        coord = self.coordenadas.get("voltar_clique_2")
        if coord:
            print("   2. Segundo clique...")
            pyautogui.click(coord["x"], coord["y"])
            time.sleep(2)
        
        print("   ✅ Voltou para consulta!")
        
        with self.lock:
            self.estado = self.OCIOSO_LOGADO
    
    def voltar_para_consulta_sem_mudar_estado(self):
        """Volta para a tela de consulta (2 cliques) mas mantém estado atual"""
        print("\n🔙 Voltando para tela de consulta (mantém estado PROCESSANDO)...")
        
        # Primeiro clique
        coord = self.coordenadas.get("voltar_clique_1")
        if coord:
            print("   1. Primeiro clique...")
            pyautogui.click(coord["x"], coord["y"])
            time.sleep(2)
        
        # Segundo clique
        coord = self.coordenadas.get("voltar_clique_2")
        if coord:
            print("   2. Segundo clique...")
            pyautogui.click(coord["x"], coord["y"])
            time.sleep(2)
        
        print("   ✅ Voltou para consulta (aguardando callback)!")
    
    def finalizar_processamento(self):
        """Muda estado para OCIOSO_LOGADO após callback bem-sucedido"""
        with self.lock:
            self.estado = self.OCIOSO_LOGADO
            print("\n✅ Estado atualizado: OCIOSO_LOGADO (pronto para próximo GCPJ)")
    
    def _monitor_inatividade(self):
        """Thread que monitora inatividade e fecha Chrome após timeout"""
        while True:
            try:
                time.sleep(30)  # Verificar a cada 30 segundos
                
                with self.lock:
                    if self.driver and self.last_activity:
                        tempo_inativo = time.time() - self.last_activity
                        
                        if tempo_inativo >= self.timeout_inatividade:
                            print(f"\n⚠️  {self.timeout_inatividade // 60} minutos de inatividade detectados")
                
                # Fechar fora do lock para evitar deadlock
                if self.driver and self.last_activity:
                    tempo_inativo = time.time() - self.last_activity
                    if tempo_inativo >= self.timeout_inatividade:
                        self.fechar_chrome()
                        
            except Exception as e:
                print(f"⚠️  Erro no monitor de inatividade: {e}")
    
    def get_status_detalhado(self) -> dict:
        """Retorna status detalhado da sessão"""
        with self.lock:
            status = {
                "estado": self.estado,
                "chrome_aberto": self.driver is not None,
                "pronto_para_processar": self.estado == self.OCIOSO_LOGADO,
                "ultima_atividade": None,
                "tempo_inativo_segundos": None,
                "fecha_em_segundos": None
            }
            
            if self.last_activity:
                tempo_inativo = int(time.time() - self.last_activity)
                status["ultima_atividade"] = datetime.fromtimestamp(self.last_activity).strftime("%Y-%m-%d %H:%M:%S")
                status["tempo_inativo_segundos"] = tempo_inativo
                status["fecha_em_segundos"] = max(0, self.timeout_inatividade - tempo_inativo)
            
            return status
