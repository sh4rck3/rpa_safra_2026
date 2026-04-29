#!/usr/bin/env python3
"""
Session Manager - Gerencia o ciclo de vida do Chrome e sessão
"""

import os
import time
import threading
import uuid
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


class SessionManager:
    """Classe responsável por gerenciar a sessão do Chrome"""
    
    # Estados possíveis
    AGUARDANDO = "AGUARDANDO"
    LOGANDO = "LOGANDO"
    OCIOSO_LOGADO = "OCIOSO_LOGADO"
    PROCESSANDO = "PROCESSANDO"
    
    def __init__(self):
        self.estado = self.AGUARDANDO
        self.driver = None
        self.wait = None
        self.last_activity = None
        self.machine_id = os.getenv('MACHINE_ID', str(uuid.uuid4()))
        self.timeout_inatividade = int(os.getenv('TIMEOUT_INATIVIDADE', 600))  # 10 minutos padrão
        
        # Carregar coordenadas
        self.coordenadas = self._carregar_coordenadas()
        
        # Credenciais
        self.website_url = os.getenv('WEBSITE_URL')
        self.username = os.getenv('SITE_USERNAME')
        self.password = os.getenv('SITE_PASSWORD')
        self.browser_timeout = int(os.getenv('BROWSER_TIMEOUT', 30))
        
        # Lock para thread-safety
        self.lock = threading.Lock()
        
        # Iniciar thread de monitoramento de inatividade
        self.monitor_thread = threading.Thread(target=self._monitor_inatividade, daemon=True)
        self.monitor_thread.start()
        
        print(f"✓ SessionManager inicializado")
        print(f"  Machine ID: {self.machine_id}")
        print(f"  Timeout de inatividade: {self.timeout_inatividade}s ({self.timeout_inatividade // 60} minutos)")
        print(f"  Coordenadas carregadas: {len(self.coordenadas)}")
    
    def _carregar_coordenadas(self) -> dict:
        """Carrega coordenadas do arquivo JSON"""
        try:
            coordenadas_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'coordenadas.json')
            if os.path.exists(coordenadas_path):
                with open(coordenadas_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️  Arquivo coordenadas.json não encontrado em: {coordenadas_path}")
                return {}
        except Exception as e:
            print(f"⚠️  Erro ao carregar coordenadas: {e}")
            return {}
    
    def get_estado(self) -> str:
        """Retorna o estado atual"""
        with self.lock:
            return self.estado
    
    def is_chrome_open(self) -> bool:
        """Verifica se o Chrome está aberto"""
        with self.lock:
            return self.driver is not None
    
    def abrir_chrome(self):
        """Abre o Chrome e faz login"""
        
        with self.lock:
            if self.driver is not None:
                print("   ℹ️  Chrome já está aberto")
                return
            
            self.estado = self.LOGANDO
        
        try:
            print("\n🌐 Abrindo Chrome...")
            
            # Usar undetected-chromedriver para bypass de WAF (Akamai)
            import undetected_chromedriver as uc
            from selenium.webdriver.support.ui import WebDriverWait
            
            # Configurar opções do Chrome
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--lang=pt-BR')
            
            # Guia anônima (configurável via .env)
            if os.getenv('CHROME_INCOGNITO', 'False').lower() in ('true', '1', 'yes'):
                chrome_options.add_argument('--incognito')
                print("   🕶️ Modo anônimo (incógnito) ativado")
            
            # Path de downloads
            from pathlib import Path
            download_path = Path('downloads').absolute()
            download_path.mkdir(exist_ok=True)
            
            prefs = {
                'download.default_directory': str(download_path),
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'plugins.always_open_pdf_externally': True
            }
            chrome_options.add_experimental_option('prefs', prefs)
            
            # Criar driver com undetected-chromedriver (anti-detecção automática)
            # Detecta versão do Chrome automaticamente
            driver = uc.Chrome(options=chrome_options, use_subprocess=True)
            
            wait = WebDriverWait(driver, self.browser_timeout)
            
            print("   ✓ Chrome aberto com sucesso")
            
            # Fazer login
            print("\n🔐 Fazendo login...")
            self._fazer_login(driver, wait)
            
            # Salvar driver e wait
            with self.lock:
                self.driver = driver
                self.wait = wait
                self.estado = self.OCIOSO_LOGADO
                self.last_activity = time.time()
            
            print("   ✓ Login realizado com sucesso!")
            print(f"   Estado: {self.estado}")
            
        except Exception as e:
            print(f"\n❌ Erro ao abrir Chrome: {e}")
            
            with self.lock:
                self.driver = None
                self.wait = None
                self.estado = self.AGUARDANDO
                self.last_activity = None
            
            raise
    
    def _verificar_access_denied(self, driver):
        """Verifica se a página atual é Access Denied por múltiplos métodos"""
        try:
            # Método 1: Verificar título da página
            titulo = driver.title.lower()
            if 'access denied' in titulo or 'denied' in titulo:
                return True
            
            # Método 2: Verificar page_source
            page_text = driver.page_source
            if 'Access Denied' in page_text or "You don't have permission" in page_text:
                return True
            
            # Método 3: Verificar URL (edgesuite = WAF Akamai)
            url_atual = driver.current_url
            if 'edgesuite' in url_atual:
                return True
            
            # Método 4: Verificar se texto visível contém "Access Denied"
            from selenium.webdriver.common.by import By
            body = driver.find_elements(By.TAG_NAME, 'body')
            if body:
                body_text = body[0].text
                if 'Access Denied' in body_text or "don't have permission" in body_text:
                    return True
            
            return False
        except Exception:
            return False
    
    def _digitar_humano(self, texto, intervalo_min=0.05, intervalo_max=0.18):
        """Digita texto caractere por caractere com delay aleatório, simulando humano"""
        import pyautogui
        import random
        
        for char in texto:
            pyautogui.press(char) if len(char) > 1 else pyautogui.write(char, interval=0)
            delay = random.uniform(intervalo_min, intervalo_max)
            time.sleep(delay)
    
    def _fazer_login(self, driver, wait):
        """Realiza login usando pyautogui (coordenadas + digitação humana)"""
        
        import pyautogui
        import random
        
        pyautogui.FAILSAFE = False
        
        # Delay aleatório antes de navegar (parecer humano)
        time.sleep(random.uniform(1.0, 2.5))
        
        driver.get(self.website_url)
        time.sleep(random.uniform(4.0, 6.0))
        
        # Verificar se deu Access Denied (múltiplos métodos)
        if self._verificar_access_denied(driver):
            print("   ❌ ACCESS DENIED DETECTADO!")
            print(f"   URL: {driver.current_url}")
            print(f"   Título: {driver.title}")
            print("   🔄 Fechando Chrome...")
            try:
                driver.quit()
            except Exception:
                pass
            raise Exception("Access Denied - site bloqueou o acesso. Tente novamente.")
        
        # Verificar se as coordenadas de login existem
        coord_username = self.coordenadas.get("login_campo_username")
        coord_password = self.coordenadas.get("login_campo_password")
        coord_botao = self.coordenadas.get("login_botao_entrar")
        
        if not all([coord_username, coord_password, coord_botao]):
            print("   ⚠️ Coordenadas de login não encontradas! Execute:")
            print("      python src/capturar_coordenadas_login.py")
            print("   Tentando login via Selenium (fallback)...")
            self._fazer_login_selenium(driver, wait)
            return
        
        print("   🖱️ Usando coordenadas + digitação humana...")
        
        # 1. Clicar no campo username
        print(f"   1. Clicando no campo username ({coord_username['x']}, {coord_username['y']})...")
        pyautogui.click(coord_username['x'], coord_username['y'])
        time.sleep(random.uniform(0.3, 0.7))
        
        # Limpar campo (Ctrl+A + Delete)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('delete')
        time.sleep(random.uniform(0.2, 0.5))
        
        # Digitar username como humano
        print(f"   2. Digitando username...")
        self._digitar_humano(self.username)
        time.sleep(random.uniform(0.5, 1.0))
        
        # 2. Clicar no campo password
        print(f"   3. Clicando no campo password ({coord_password['x']}, {coord_password['y']})...")
        pyautogui.click(coord_password['x'], coord_password['y'])
        time.sleep(random.uniform(0.3, 0.7))
        
        # Limpar campo
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('delete')
        time.sleep(random.uniform(0.2, 0.5))
        
        # Digitar password como humano
        print(f"   4. Digitando password...")
        self._digitar_humano(self.password)
        time.sleep(random.uniform(0.5, 1.2))
        
        # 3. Clicar no botão login
        print(f"   5. Clicando no botão login ({coord_botao['x']}, {coord_botao['y']})...")
        pyautogui.click(coord_botao['x'], coord_botao['y'])
        time.sleep(6)
        
        # Verificar se deu Access Denied após login
        if self._verificar_access_denied(driver):
            print("   ❌ ACCESS DENIED DETECTADO (após login)!")
            try:
                driver.quit()
            except Exception:
                pass
            raise Exception("Access Denied - site bloqueou o acesso. Tente novamente.")
        
        print("   ✓ Login realizado")
    
    def _fazer_login_selenium(self, driver, wait):
        """Fallback: login via Selenium caso coordenadas não existam"""
        
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            username_field = wait.until(
                EC.presence_of_element_located((By.ID, 'Username'))
            )
        except Exception:
            if self._verificar_access_denied(driver):
                try:
                    driver.quit()
                except Exception:
                    pass
                raise Exception("Access Denied - site bloqueou o acesso. Tente novamente.")
            else:
                raise
        
        username_field.clear()
        username_field.send_keys(self.username)
        time.sleep(0.5)
        
        password_field = driver.find_element(By.ID, 'Password')
        password_field.clear()
        password_field.send_keys(self.password)
        time.sleep(0.5)
        
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button.btn-login[type="submit"]')
        submit_button.click()
        time.sleep(5)
        
        print("   ✓ Login realizado (Selenium fallback)")
    
    def fechar_chrome(self):
        """Fecha o Chrome"""
        
        with self.lock:
            if self.driver is None:
                return
            
            try:
                print("\n⚠️  Fechando Chrome...")
                self.driver.quit()
                print("   ✓ Chrome fechado")
            except Exception as e:
                print(f"   ⚠️  Erro ao fechar Chrome: {e}")
            finally:
                self.driver = None
                self.wait = None
                self.estado = self.AGUARDANDO
                self.last_activity = None
    
    def marcar_atividade(self):
        """Atualiza o timestamp da última atividade"""
        with self.lock:
            self.last_activity = time.time()
    
    def set_estado(self, novo_estado: str):
        """Altera o estado"""
        with self.lock:
            self.estado = novo_estado
            if novo_estado == self.PROCESSANDO:
                self.last_activity = time.time()
    
    def get_driver_and_wait(self):
        """Retorna o driver e wait (abre Chrome se necessário)"""
        
        if not self.is_chrome_open():
            self.abrir_chrome()
        
        with self.lock:
            return self.driver, self.wait
    
    def _monitor_inatividade(self):
        """
        Thread que monitora inatividade e fecha Chrome após 10 minutos
        Simples e direto: fecha Chrome, sem controlar sessão
        """
        
        print("✓ Monitor de inatividade iniciado (fecha Chrome após 10 min de ociosidade)")
        
        while True:
            time.sleep(60)  # Checar a cada 1 minuto
            
            with self.lock:
                # Só verificar se estiver OCIOSO_LOGADO e tiver Chrome aberto
                if self.estado != self.OCIOSO_LOGADO or self.driver is None:
                    continue
                
                if self.last_activity is None:
                    continue
                
                tempo_inativo = time.time() - self.last_activity
                
                # Se passou 10 minutos (600 segundos), fechar Chrome
                if tempo_inativo >= self.timeout_inatividade:
                    minutos_inativo = int(tempo_inativo // 60)
                    print(f"\n⏱️  Chrome ocioso há {minutos_inativo} minutos - fechando navegador...")
                    
                    try:
                        self.driver.quit()
                        print("   ✓ Chrome fechado por inatividade")
                    except Exception as e:
                        print(f"   ⚠️  Erro ao fechar Chrome: {e}")
                    finally:
                        self.driver = None
                        self.wait = None
                        self.estado = self.AGUARDANDO
                        self.last_activity = None
                    
                    print("   ℹ️  Próximo CPF abrirá Chrome novamente e fará login do zero")
    
    def finalizar_processamento(self):
        """Muda estado para OCIOSO_LOGADO após callback bem-sucedido"""
        with self.lock:
            self.estado = self.OCIOSO_LOGADO
            print("\n✅ Estado atualizado: OCIOSO_LOGADO (pronto para próximo CPF)")
    
    def voltar_para_consulta_sem_mudar_estado(self):
        """
        Realiza navegação de volta para tela de consulta
        MAS mantém estado atual (PROCESSANDO)
        
        Usado quando CPF foi processado mas ainda aguarda confirmação do callback
        """
        print("\n🔙 Voltando para tela de consulta (aguardando callback)...")
        
        try:
            import pyautogui
            import time
            
            # 1. Clicar no menu Pesquisa
            if 'menu_pesquisa_pos_callback' in self.coordenadas:
                menu_x = self.coordenadas['menu_pesquisa_pos_callback']['x']
                menu_y = self.coordenadas['menu_pesquisa_pos_callback']['y']
                
                print(f"   🖱️  Clicando no menu Pesquisa ({menu_x}, {menu_y})...")
                pyautogui.click(menu_x, menu_y)
                time.sleep(2)
                print(f"   ✓ Menu Pesquisa clicado!")
            else:
                print(f"   ⚠️  Coordenada 'menu_pesquisa_pos_callback' não encontrada!")
            
            # 2. Clicar no input CPF/CNPJ
            if 'input_cpf_pos_callback' in self.coordenadas:
                input_x = self.coordenadas['input_cpf_pos_callback']['x']
                input_y = self.coordenadas['input_cpf_pos_callback']['y']
                
                print(f"   🖱️  Clicando no input CPF/CNPJ ({input_x}, {input_y})...")
                pyautogui.click(input_x, input_y)
                time.sleep(0.5)
                print(f"   ✓ Input CPF/CNPJ focado")
                
                # Limpar o campo (selecionar tudo e deletar)
                print(f"   🧹 Limpando campo CPF...")
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                pyautogui.press('delete')
                time.sleep(0.3)
                print(f"   ✓ Campo limpo e pronto para próximo CPF!")
            else:
                print(f"   ⚠️  Coordenada 'input_cpf_pos_callback' não encontrada!")
            
            print("   ✅ Voltou para consulta (estado: PROCESSANDO - aguardando callback)")
            
        except Exception as e:
            print(f"   ⚠️  Erro ao voltar para menu Pesquisa: {e}")
    
    def get_status_detalhado(self) -> dict:
        """Retorna status detalhado da sessão"""
        with self.lock:
            status = {
                "estado": self.estado,
                "chrome_aberto": self.driver is not None,
                "pronto_para_processar": self.estado == self.OCIOSO_LOGADO,
                "ultima_atividade": None,
                "tempo_inativo_segundos": 0,
                "fecha_em_segundos": 0
            }
            
            if self.last_activity:
                tempo_inativo = int(time.time() - self.last_activity)
                status["ultima_atividade"] = datetime.fromtimestamp(self.last_activity).strftime("%Y-%m-%d %H:%M:%S")
                status["tempo_inativo_segundos"] = tempo_inativo
                status["fecha_em_segundos"] = max(0, self.timeout_inatividade - tempo_inativo)
            
            return status
