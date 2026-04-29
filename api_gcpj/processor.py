#!/usr/bin/env python3
"""
Processor - Lógica de processamento de GCPJ
"""

import time
import json
import re
import pyautogui
import pyperclip
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def processar_gcpj(session_manager, gcpj: str) -> Dict[str, Any]:
    """
    Processa um número GCPJ com retry automático
    
    Estratégia de retry (EXATAMENTE igual ao script manual):
    - Máximo 2 tentativas
    - Entre tentativas: fecha ABA (não Chrome)
    - Chrome continua aberto durante todo processo
    - Cada tentativa tem 15 verificações de URL
    
    Args:
        session_manager: Instância do SessionManager
        gcpj: Número do GCPJ (ex: "1300285552")
        
    Returns:
        {
            "success": True/False,
            "gcpj": "1300285552",
            "timestamp": "2026-01-07 14:30:00",
            "error": None ou mensagem de erro,
            "data": {...}
        }
    """
    
    MAX_TENTATIVAS = 2  # Igual ao script manual
    
    print(f"\n{'='*60}")
    print(f"🔄 PROCESSANDO GCPJ: {gcpj}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    try:
        # Verificar se Chrome está aberto e logado
        if not session_manager.is_pronto_para_processar():
            print("⚠️  Chrome não está logado. Fazendo login...")
            session_manager.abrir_chrome_e_logar()
        
        # Mudar estado para PROCESSANDO
        with session_manager.lock:
            session_manager.estado = session_manager.PROCESSANDO
        
        # Atualizar atividade
        session_manager.atualizar_atividade()
        
        # Tentar processar (máximo 2 tentativas)
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            print(f"\n   → Tentativa {tentativa}/{MAX_TENTATIVAS}")
            
            try:
                # Processar GCPJ
                dados = _processar_gcpj_completo(session_manager, gcpj)
                
                # ✅ SUCESSO! Voltar para tela de consulta (mas ainda PROCESSANDO)
                session_manager.voltar_para_consulta_sem_mudar_estado()
                session_manager.atualizar_atividade()
                
                processing_time = int(time.time() - start_time)
                print(f"\n✅ GCPJ processado! Aguardando confirmação do Laravel...")
                
                return {
                    "success": True,
                    "gcpj": gcpj,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "processing_time": processing_time,
                    "error": None,
                    "data": dados
                }
                
            except Exception as e_tentativa:
                print(f"   ❌ Erro na tentativa {tentativa}: {e_tentativa}")
                
                # Se não for a última tentativa, fecha aba e tenta novamente
                if tentativa < MAX_TENTATIVAS:
                    print(f"\n   🔄 Fechando aba problemática e tentando novamente...")
                    try:
                        # Verificar quantas abas existem
                        num_abas = len(session_manager.driver.window_handles)
                        print(f"      Abas abertas: {num_abas}")
                        
                        if num_abas > 1:
                            # Fechar a aba atual
                            session_manager.driver.close()
                            print("      ✓ Aba fechada")
                            
                            # Voltar para a primeira aba
                            session_manager.driver.switch_to.window(session_manager.driver.window_handles[0])
                            print("      ✓ Voltou para primeira aba")
                        else:
                            print("      ⚠️  Apenas 1 aba aberta, mantendo...")
                        
                        time.sleep(2)
                        
                        # Reabrir GCPJ (navegar novamente pela extensão)
                        print("   🔄 Reiniciando processo de acesso ao GCPJ...")
                        session_manager._navegar_para_gcpj()
                        
                    except Exception as e_fechar:
                        print(f"   ⚠️  Erro ao fechar/reabrir aba: {e_fechar}")
                        print(f"   ⏩ Continuando para próxima tentativa mesmo assim...")
                else:
                    print(f"   ⚠️  Todas as {MAX_TENTATIVAS} tentativas falharam")
        
        # Se chegou aqui, todas tentativas falharam
        processing_time = int(time.time() - start_time)
        print(f"\n❌ FALHA: Não foi possível processar GCPJ após {MAX_TENTATIVAS} tentativas")
        
        # Voltar para tela de consulta ou fechar Chrome
        try:
            session_manager.voltar_para_consulta()
        except:
            # Se não conseguir voltar, fecha Chrome
            try:
                session_manager.fechar_chrome()
            except:
                pass
        
        return {
            "success": False,
            "gcpj": gcpj,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "processing_time": processing_time,
            "error": "Sistema GCPJ indisponível após múltiplas tentativas",
            "data": {
                "resultados_etapas": [
                    {
                        "etapa": "Acessar sistema GCPJ",
                        "status": "erro",
                        "mensagem": f"Sistema GCPJ indisponível. Total de tentativas: {MAX_TENTATIVAS}"
                    }
                ]
            }
        }
        
    except Exception as e:
        processing_time = int(time.time() - start_time)
        print(f"\n❌ Erro crítico ao processar GCPJ: {e}")
        
        # Tentar voltar para consulta ou fechar Chrome
        try:
            session_manager.voltar_para_consulta()
        except:
            try:
                session_manager.fechar_chrome()
            except:
                pass
        
        return {
            "success": False,
            "gcpj": gcpj,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "processing_time": processing_time,
            "error": str(e),
            "data": {}
        }


def _processar_gcpj_completo(session_manager, gcpj: str) -> Dict[str, Any]:
    """Processa GCPJ completo e retorna dados estruturados"""
    
    coordenadas = session_manager.coordenadas
    
    # Array para rastrear APENAS problemas (avisos e erros)
    resultados_etapas = []
    
    # ========================================================
    # 1. Preencher campo de busca com número GCPJ
    # ========================================================
    try:
        print("📝 Preenchendo campo de busca...")
        coord = coordenadas.get("campo_numero_processo")
        if not coord:
            raise Exception("Coordenada 'campo_numero_processo' não encontrada")
        
        pyautogui.click(coord["x"], coord["y"])
        time.sleep(1)  # Aguardar foco no campo
        
        # Limpar campo antes
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        
        # Digitar GCPJ
        pyautogui.write(gcpj, interval=0.05)
        time.sleep(0.5)
        print(f"   ✅ GCPJ digitado: {gcpj}")
        # NÃO adiciona ao array - sucesso não precisa reportar
    except Exception as e:
        resultados_etapas.append({
            "etapa": "Preencher campo GCPJ",
            "status": "erro",
            "mensagem": str(e)
        })
        raise
    
    # ========================================================
    # 2. Clicar no botão BUSCAR
    # ========================================================
    try:
        print("\n🔍 Clicando em BUSCAR...")
        coord = coordenadas.get("botao_buscar")
        if not coord:
            raise Exception("Coordenada 'botao_buscar' não encontrada")
        
        pyautogui.click(coord["x"], coord["y"])
        print("\n⏳ Aguardando resultado da pesquisa (5 segundos)...")
        time.sleep(5)  # EXATAMENTE igual ao script original
        print("   ✅ Busca realizada!")
        # NÃO adiciona ao array - sucesso não precisa reportar
    except Exception as e:
        resultados_etapas.append({
            "etapa": "Buscar processo",
            "status": "erro",
            "mensagem": str(e)
        })
        raise
    
    # ========================================================
    # 3. Copiar dados da tela principal (Ctrl+A + Ctrl+C)
    # ========================================================
    try:
        print("\n📄 Copiando dados da tela principal...")
        print("📄 Selecionando todo conteúdo (Ctrl+A)...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)  # EXATAMENTE igual ao script original
        
        print("📋 Copiando para clipboard (Ctrl+C)...")
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(1)  # EXATAMENTE igual ao script original
        
        conteudo_texto = pyperclip.paste()
        print(f"   ✅ Dados copiados: {len(conteudo_texto)} caracteres")
        # NÃO adiciona ao array - sucesso não precisa reportar
    except Exception as e:
        resultados_etapas.append({
            "etapa": "Copiar dados principais",
            "status": "erro",
            "mensagem": str(e)
        })
        conteudo_texto = ""
    
    # ========================================================
    # 4. Extrair dados estruturados
    # ========================================================
    try:
        print("\n🔍 Extraindo dados estruturados...")
        dados_json = _extrair_dados_estruturados(conteudo_texto, gcpj, session_manager.driver)
        # NÃO adiciona ao array - sucesso não precisa reportar
    except Exception as e:
        resultados_etapas.append({
            "etapa": "Extrair dados estruturados",
            "status": "erro",
            "mensagem": str(e)
        })
        dados_json = {
            "gcpj": gcpj,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dados_processo": {},
            "classificacao": {},
            "detalhamento": {},
            "envolvidos": [],
            "advogados": [],
            "dados_dependencia": {},
            "contratos": []
        }
    
    # ========================================================
    # 5. Clicar no primeiro envolvido (se existir)
    # ========================================================
    if dados_json['envolvidos']:
        try:
            print(f"\n📋 Clicando no primeiro envolvido: {dados_json['envolvidos'][0]['nome']}...")
            coord = coordenadas.get("primeiro_envolvido_link")
            if coord:
                pyautogui.click(coord["x"], coord["y"])
                print("⏳ Aguardando modal abrir (3 segundos)...")
                time.sleep(3)  # EXATAMENTE igual ao script original
                
                # Clicar dentro do modal para dar foco
                coord = coordenadas.get("dentro_modal_envolvido")
                if coord:
                    print(f"🖱️  Clicando dentro do modal para dar foco...")
                    pyautogui.click(coord["x"], coord["y"])
                    time.sleep(1)  # EXATAMENTE igual ao script original
                
                # Copiar dados do modal
                print("   📄 Copiando dados do modal (Ctrl+A + Ctrl+C)...")
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)  # EXATAMENTE igual ao script original
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(1)  # EXATAMENTE igual ao script original
                
                conteudo_modal = pyperclip.paste()
                print(f"   ✅ Dados do modal copiados: {len(conteudo_modal)} caracteres")
                
                # Extrair dados da dependência
                dados_json['dados_dependencia'] = _extrair_dados_dependencia(conteudo_modal)
                
                # Fechar modal
                coord = coordenadas.get("fechar_modal_envolvido")
                if coord:
                    print("   ❌ Fechando modal...")
                    pyautogui.click(coord["x"], coord["y"])
                    time.sleep(2)  # EXATAMENTE igual ao script original
                # NÃO adiciona ao array - sucesso não precisa reportar
        except Exception as e:
            print(f"⚠️  Erro ao processar modal de envolvido: {e}")
            resultados_etapas.append({
                "etapa": "Extrair dados da dependência",
                "status": "erro",
                "mensagem": str(e)
            })
    
    # ========================================================
    # 6. Clicar no botão Contratos (reconhecimento de imagem)
    # ========================================================
    print(f"\n🔍 Procurando botão 'Contratos'...")
    
    # Rolar para baixo EXATAMENTE como no script original
    print("⬇️  Rolando página para baixo...")
    for i in range(3):
        pyautogui.scroll(-300)
        time.sleep(0.5)  # EXATAMENTE igual ao script original
    
    # Procurar botão
    pasta_assets = Path(__file__).parent.parent / "assets"
    imagem_botao = pasta_assets / "btn_contratos.png"
    
    print(f"\n📍 DEBUG - Caminho da imagem:")
    print(f"   __file__: {__file__}")
    print(f"   pasta_assets: {pasta_assets}")
    print(f"   imagem_botao: {imagem_botao}")
    print(f"   imagem_botao.exists(): {imagem_botao.exists()}")
    print(f"   imagem_botao.is_absolute(): {imagem_botao.is_absolute()}")
    
    if imagem_botao.exists():
        botao_encontrado = None
        max_tentativas = 5  # EXATAMENTE igual ao script original
        
        for tentativa in range(1, max_tentativas + 1):
            print(f"   Tentativa {tentativa}/{max_tentativas}...")
            try:
                # Tentar com grayscale (mais rápido, match exato)
                localizacao = pyautogui.locateOnScreen(str(imagem_botao), grayscale=True)
                if localizacao:
                    botao_encontrado = localizacao
                    print(f"   ✅ Botão encontrado! Posição: {localizacao}")
                    break
                
                # Tentar sem grayscale (mais preciso com cores)
                localizacao = pyautogui.locateOnScreen(str(imagem_botao))
                if localizacao:
                    botao_encontrado = localizacao
                    print(f"   ✅ Botão encontrado (colorido)! Posição: {localizacao}")
                    break
                
                print(f"   ⚠️  Botão não encontrado nesta tentativa")
            except Exception as e:
                print(f"   ⚠️  Erro na busca: {e}")
            
            if tentativa < max_tentativas:
                print(f"   ⬇️  Rolando mais para baixo...")
                pyautogui.scroll(-200)
                time.sleep(1)  # EXATAMENTE igual ao script original
        
        if botao_encontrado:
            centro_x = botao_encontrado.left + botao_encontrado.width // 2
            centro_y = botao_encontrado.top + botao_encontrado.height // 2
            
            print(f"   ✅ Botão Contratos encontrado!")
            print(f"🖱️  Clicando no botão Contratos...")
            print(f"   Posição: ({centro_x}, {centro_y})")
            pyautogui.click(centro_x, centro_y)
            time.sleep(3)  # EXATAMENTE igual ao script original
            
            print("✅ Clique realizado com sucesso!")
            print("   ⏳ Aguardando modal abrir...")
            time.sleep(2)  # EXATAMENTE igual ao script original
            
            # Rolar para cima EXATAMENTE como no script original
            print("⬆️  Rolando página para cima...")
            for i in range(5):
                pyautogui.scroll(300)
                time.sleep(0.3)  # EXATAMENTE igual ao script original
            
            # Clicar dentro do modal de contratos
            print("🖱️  Clicando dentro do modal Contratos para dar foco...")
            coord = coordenadas.get("dentro_modal_contratos")
            if coord:
                pyautogui.click(coord["x"], coord["y"])
                time.sleep(1)  # EXATAMENTE igual ao script original
            
            # Copiar dados do modal de contratos
            print("   📄 Copiando dados do modal (Ctrl+A + Ctrl+C)...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)  # EXATAMENTE igual ao script original
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(1)  # EXATAMENTE igual ao script original
            
            conteudo_contratos = pyperclip.paste()
            print(f"   ✅ Dados de contratos copiados: {len(conteudo_contratos)} caracteres")
            
            # Extrair contratos
            dados_json['contratos'] = _extrair_contratos(conteudo_contratos)
            
            # Fechar modal
            coord = coordenadas.get("fechar_modal_envolvido")  # Reutilizar coordenada do X
            if coord:
                print("   ❌ Fechando modal de contratos...")
                pyautogui.click(coord["x"], coord["y"])
                time.sleep(2)  # EXATAMENTE igual ao script original
            # NÃO adiciona ao array - sucesso não precisa reportar
        else:
            print("   ⚠️  Botão Contratos não encontrado")
            resultados_etapas.append({
                "etapa": "Extrair contratos",
                "status": "aviso",
                "mensagem": "Botão 'Contratos' não foi encontrado na tela após 5 tentativas. Dados de contratos não foram extraídos."
            })
    else:
        print(f"   ⚠️  Imagem do botão não encontrada: {imagem_botao}")
        resultados_etapas.append({
            "etapa": "Extrair contratos",
            "status": "aviso",
            "mensagem": f"Imagem do botão (btn_contratos.png) não encontrada. Verifique se a imagem existe em: {pasta_assets}"
        })
    
    # Adicionar array de resultados ao JSON final (SEMPRE, mesmo sem problemas)
    if resultados_etapas:
        # Tem problemas - listar eles
        dados_json['resultados_etapas'] = resultados_etapas
        print(f"\n⚠️  Processamento com ressalvas:")
        for resultado in resultados_etapas:
            print(f"   - [{resultado['status'].upper()}] {resultado['etapa']}: {resultado['mensagem']}")
    else:
        # Sem problemas - informar sucesso
        dados_json['resultados_etapas'] = [
            {
                "etapa": "Processamento completo",
                "status": "sucesso",
                "mensagem": "Captura de dados concluída com sucesso"
            }
        ]
        print(f"\n✅ Todos os dados extraídos com sucesso!")
    
    print(f"   - Campos do processo: {len([v for v in dados_json['dados_processo'].values() if v])}")
    print(f"   - Envolvidos: {len(dados_json['envolvidos'])}")
    print(f"   - Contratos: {len(dados_json['contratos'])}")
    print(f"   - Advogados: {len(dados_json['advogados'])}")
    
    return dados_json


def _extrair_dados_estruturados(conteudo: str, gcpj: str, driver) -> Dict[str, Any]:
    """Extrai dados estruturados do conteúdo copiado"""
    
    def extrair_campo(texto, campo):
        """Extrai valor de um campo específico"""
        pattern = rf'{campo}\s*[:\s]+([^\n\r]+)'
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            valor = match.group(1).strip()
            # Remover texto de paginação
            valor = re.sub(r'(primeira página|página anterior|página posterior|última página|\[\d+\]).*', '', valor).strip()
            return valor
        return ""
    
    dados = {
        "gcpj": gcpj,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dados_processo": {
            "numero_processo_bradesco": extrair_campo(conteudo, "Nº do Processo Bradesco"),
            "status_processo": "Processo Ativo" if "Processo Ativo" in conteudo else "Processo Inativo",
            "data_cadastro": extrair_campo(conteudo, "Data do Cadastro"),
            "data_movimento": extrair_campo(conteudo, "Data do Movimento"),
            "departamento_juridico": extrair_campo(conteudo, "Departamento Jurídico"),
            "empresa_grupo": extrair_campo(conteudo, "Empresa Grupo"),
            "compartilhado": extrair_campo(conteudo, "Compartilhado"),
            "dep_envolvida": extrair_campo(conteudo, "Dep. Envolvida"),
            "orgao_julgador": extrair_campo(conteudo, "Órgão Julgador"),
            "comarca": extrair_campo(conteudo, "Comarca"),
            "tribunal": extrair_campo(conteudo, "Tribunal"),
            "numero_processo_judicial": extrair_campo(conteudo, "Nº do Processo Judicial"),
            "valor_causa": extrair_campo(conteudo, "Valor da Causa R\\$"),
            "valor_causa_atualizado": extrair_campo(conteudo, "Valor da Causa Atualiz. R\\$"),
            "data_fato_gerador": extrair_campo(conteudo, "Data do Fato Gerador"),
            "data_distrib_orgao_julgador": extrair_campo(conteudo, "Data Distrib. O. Julgador"),
            "origem_cnj": extrair_campo(conteudo, "Origem CNJ"),
            "comunicacoes": extrair_campo(conteudo, "Comunicações")
        },
        "classificacao": {
            "tipo_processo": extrair_campo(conteudo, "Tipo de Processo"),
            "risco_acao": extrair_campo(conteudo, "Risco da Ação"),
            "tipo_acao": extrair_campo(conteudo, "Tipo de Ação"),
            "nome_acao": extrair_campo(conteudo, "Nome de Ação"),
            "preocupante": extrair_campo(conteudo, "Preocupante")
        },
        "detalhamento": {
            "pedido": extrair_campo(conteudo, "Pedido")
        },
        "envolvidos": [],
        "advogados": [],
        "dados_dependencia": {},
        "contratos": [],
        "html_completo": driver.page_source if driver else ""
    }
    
    # Extrair envolvidos
    envolvidos_match = re.search(
        r'Envolvidos\s+Nome\s+Documento\s+Tipo Envolvido\s+Seq\.\s+(.*?)(?=\n\n|\nClassificação|Advogado)',
        conteudo, re.DOTALL
    )
    if envolvidos_match:
        linhas = envolvidos_match.group(1).strip().split('\n')
        for linha in linhas:
            partes = [p.strip() for p in linha.split('\t') if p.strip()]
            if len(partes) >= 4:
                dados["envolvidos"].append({
                    "nome": partes[0],
                    "documento": partes[1],
                    "tipo": partes[2],
                    "sequencia": partes[3]
                })
    
    # Extrair advogados
    advogados_match = re.search(
        r'Advogado/Procurador\s+Tipo\s+Nome\s+OAB\s+(.*?)(?=\n\n|$)',
        conteudo, re.DOTALL
    )
    if advogados_match:
        linhas = advogados_match.group(1).strip().split('\n')
        for linha in linhas:
            partes = [p.strip() for p in linha.split('\t') if p.strip()]
            if len(partes) >= 2:
                dados["advogados"].append({
                    "tipo": partes[0],
                    "nome": partes[1],
                    "oab": partes[2] if len(partes) >= 3 else ""
                })
    
    return dados


def _extrair_dados_dependencia(conteudo: str) -> Dict[str, str]:
    """Extrai dados da dependência do modal"""
    
    def extrair_linha_completa(texto, label):
        """Extrai linha completa após o label"""
        pattern = rf'{label}\s*[:\s]+([^\n\r]+)'
        match = re.search(pattern, texto, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    def extrair_campo(texto, campo):
        """Extrai campo simples"""
        pattern = rf'{campo}\s*[:\s]+([^\n\r\t]+)'
        match = re.search(pattern, texto, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    return {
        "dependencia": extrair_linha_completa(conteudo, "Dependência"),
        "dir_regional": extrair_linha_completa(conteudo, "Dir. Regional"),
        "ger_regional": extrair_linha_completa(conteudo, "Ger. Regional"),
        "empresa_inc": extrair_linha_completa(conteudo, "Empresa Inc"),
        "cod_natureza": extrair_campo(conteudo, "Cód. Natureza"),
        "gerente": extrair_linha_completa(conteudo, "Gerente"),
        "email": extrair_campo(conteudo, "Email")
    }


def _extrair_contratos(conteudo: str) -> list:
    """Extrai contratos do modal"""
    
    contratos = []
    
    contratos_match = re.search(
        r'Contratos\s+Agência\s+Conta\s+Carteira\s+Nº Contrato\s+Sequencia\s+Nome Envolvido\s+Data da Safra\s+(.*?)(?=primeira página|$)',
        conteudo, re.DOTALL
    )
    
    if contratos_match:
        linhas = contratos_match.group(1).strip().split('\n')
        for linha in linhas:
            if not linha.strip() or 'página' in linha.lower():
                continue
            
            partes = [p.strip() for p in linha.split('\t') if p.strip()]
            if len(partes) >= 6:
                contratos.append({
                    "agencia": partes[0],
                    "conta": partes[1],
                    "carteira": partes[2],
                    "numero_contrato": partes[3],
                    "sequencia": partes[4],
                    "nome_envolvido": partes[5],
                    "data_safra": partes[6] if len(partes) >= 7 else ""
                })
    
    return contratos
