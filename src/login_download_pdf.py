#!/usr/bin/env python3
"""
Web Automation Script - Login and Download PDF
Este script automatiza o login em um site e o download de documentos PDF.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests


class WebAutomation:
    """Classe para automação de login e download de PDFs."""
    
    def __init__(self):
        """Inicializa o automation com as configurações do .env"""
        load_dotenv()
        
        self.website_url = os.getenv('WEBSITE_URL')
        self.username = os.getenv('USERNAME')
        self.password = os.getenv('PASSWORD')
        self.pdf_url = os.getenv('PDF_URL')
        self.download_path = Path(os.getenv('DOWNLOAD_PATH', './downloads'))
        self.headless = os.getenv('HEADLESS', 'False').lower() == 'true'
        self.timeout = int(os.getenv('BROWSER_TIMEOUT', '30'))
        
        self.driver = None
        
        # Criar diretório de downloads se não existir
        self.download_path.mkdir(parents=True, exist_ok=True)
    
    def setup_driver(self):
        """Configura o driver do Chrome com as opções necessárias."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Configurar download automático
        prefs = {
            'download.default_directory': str(self.download_path.absolute()),
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'plugins.always_open_pdf_externally': True
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        
        print("✓ Driver do Chrome configurado com sucesso")
    
    def login(self, username_field='username', password_field='password', submit_button='//button[@type="submit"]'):
        """
        Realiza login no site.
        
        Args:
            username_field: Nome ou ID do campo de usuário
            password_field: Nome ou ID do campo de senha
            submit_button: XPath do botão de submit
        """
        try:
            print(f"Acessando {self.website_url}...")
            self.driver.get(self.website_url)
            
            # Aguardar página carregar
            wait = WebDriverWait(self.driver, self.timeout)
            
            # Localizar e preencher campo de usuário
            print("Preenchendo credenciais...")
            username_input = wait.until(
                EC.presence_of_element_located((By.NAME, username_field))
            )
            username_input.clear()
            username_input.send_keys(self.username)
            
            # Localizar e preencher campo de senha
            password_input = self.driver.find_element(By.NAME, password_field)
            password_input.clear()
            password_input.send_keys(self.password)
            
            # Clicar no botão de login
            print("Realizando login...")
            submit = self.driver.find_element(By.XPATH, submit_button)
            submit.click()
            
            # Aguardar login ser processado
            time.sleep(3)
            
            print("✓ Login realizado com sucesso")
            return True
            
        except Exception as e:
            print(f"✗ Erro ao realizar login: {str(e)}")
            return False
    
    def download_pdf_with_selenium(self, pdf_link_xpath):
        """
        Baixa PDF clicando em um link usando Selenium.
        
        Args:
            pdf_link_xpath: XPath do link do PDF
        """
        try:
            wait = WebDriverWait(self.driver, self.timeout)
            pdf_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, pdf_link_xpath))
            )
            
            print("Iniciando download do PDF...")
            pdf_link.click()
            
            # Aguardar download iniciar
            time.sleep(5)
            
            print("✓ Download iniciado com sucesso")
            return True
            
        except Exception as e:
            print(f"✗ Erro ao baixar PDF: {str(e)}")
            return False
    
    def download_pdf_with_requests(self, pdf_url=None, filename='documento.pdf'):
        """
        Baixa PDF usando requests (útil quando você tem a URL direta).
        
        Args:
            pdf_url: URL do PDF (usa self.pdf_url se não fornecida)
            filename: Nome do arquivo a ser salvo
        """
        try:
            url = pdf_url or self.pdf_url
            
            print(f"Baixando PDF de {url}...")
            
            # Obter cookies da sessão do Selenium (se disponível)
            cookies = {}
            if self.driver:
                selenium_cookies = self.driver.get_cookies()
                cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
            
            # Fazer request com os cookies da sessão
            response = requests.get(url, cookies=cookies, stream=True)
            response.raise_for_status()
            
            # Salvar PDF
            file_path = self.download_path / filename
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✓ PDF salvo em: {file_path}")
            return True
            
        except Exception as e:
            print(f"✗ Erro ao baixar PDF: {str(e)}")
            return False
    
    def close(self):
        """Fecha o navegador."""
        if self.driver:
            self.driver.quit()
            print("✓ Navegador fechado")


def main():
    """Função principal do script."""
    automation = WebAutomation()
    
    try:
        # 1. Configurar driver
        automation.setup_driver()
        
        # 2. Fazer login
        # NOTA: Ajuste os parâmetros conforme os campos do seu site
        success = automation.login(
            username_field='username',  # ou 'email', 'user', etc.
            password_field='password',  # ou 'senha', 'pass', etc.
            submit_button='//button[@type="submit"]'  # XPath do botão
        )
        
        if not success:
            print("Falha no login. Encerrando...")
            return
        
        # 3. Baixar PDF
        # Opção A: Clicar em um link na página
        # automation.download_pdf_with_selenium('//a[contains(@href, ".pdf")]')
        
        # Opção B: Download direto via URL (recomendado se você tem a URL)
        automation.download_pdf_with_requests(filename='meu_documento.pdf')
        
        # Aguardar para verificar resultado
        time.sleep(5)
        
    except Exception as e:
        print(f"✗ Erro durante execução: {str(e)}")
    
    finally:
        # Sempre fechar o navegador
        automation.close()


if __name__ == '__main__':
    main()
