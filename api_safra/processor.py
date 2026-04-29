#!/usr/bin/env python3
"""
Processor - Lógica de processamento de CPF (extração de dados da página)
Reutiliza funções do processar_lote.py
"""

import os
import sys
import time
from pathlib import Path

# Adicionar diretório src ao path para importar funções
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Importar funções necessárias do processar_lote
from processar_lote import (
    carregar_coordenadas,
    salvar_coordenadas,
    navegar_nova_proposta,
    processar_cpf as processar_cpf_original,
    extrair_dados,
    extrair_dados_cancelado,
    voltar_menu_pesquisa
)


def processar_cpf_completo(session_manager, cpf: str) -> dict:
    """
    Processa um CPF completo: abre Chrome se necessário, navega, extrai dados
    
    Args:
        session_manager: Instância do SessionManager
        cpf: CPF a processar
    
    Returns:
        dict: Resultado do processamento com estrutura padrão
              SEMPRE inclui array 'resultados_etapas' com APENAS a última etapa
    """
    
    # Variável para rastrear a ÚLTIMA etapa executada
    etapa_final = {
        "etapa": "Inicialização",
        "status": "em_andamento",
        "mensagem": "Processamento iniciado"
    }
    
    try:
        # Garantir que pyautogui está disponível
        try:
            import pyautogui
            import pyperclip
        except ImportError:
            print("   Instalando pyautogui e pyperclip...")
            import subprocess
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyautogui', 'pyperclip'], check=True)
            import pyautogui
            import pyperclip
        
        etapa_final = {
            "etapa": "Bibliotecas carregadas",
            "status": "sucesso",
            "mensagem": "pyautogui e pyperclip disponíveis"
        }
        
        # Verificar se Chrome está aberto
        chrome_estava_aberto = session_manager.is_chrome_open()
        
        if not chrome_estava_aberto:
            # Chrome FECHADO → Abrir, logar e navegar
            print("\n🌐 Chrome fechado - Abrindo e navegando...")
            etapa_final = {
                "etapa": "Abrindo Chrome",
                "status": "em_andamento",
                "mensagem": "Iniciando navegador e fazendo login"
            }
            
            # Obter driver e wait (abre Chrome e faz login)
            driver, wait = session_manager.get_driver_and_wait()
            
            etapa_final = {
                "etapa": "Chrome aberto e login efetuado",
                "status": "sucesso",
                "mensagem": "Navegador iniciado com sucesso"
            }
            
            # Navegar para Nova Proposta (abre aba de pesquisa)
            print("\n📋 Navegando para Nova Proposta...")
            from processar_lote import navegar_nova_proposta
            navegar_nova_proposta(driver, wait)
            
            etapa_final = {
                "etapa": "Navegação para tela de pesquisa",
                "status": "sucesso",
                "mensagem": "Tela de pesquisa aberta"
            }
            
            session_manager.set_estado(session_manager.OCIOSO_LOGADO)
        else:
            # Chrome ABERTO → Só pegar driver (input já está selecionado)
            print("\n✓ Chrome já aberto - Input CPF já selecionado")
            driver, wait = session_manager.get_driver_and_wait()
            
            etapa_final = {
                "etapa": "Chrome já estava aberto",
                "status": "sucesso",
                "mensagem": "Reutilizando sessão existente"
            }
        
        # Marcar como processando
        session_manager.set_estado(session_manager.PROCESSANDO)
        
        # Carregar coordenadas
        coordenadas = carregar_coordenadas()
        etapa_final = {
            "etapa": "Coordenadas carregadas",
            "status": "sucesso",
            "mensagem": f"Arquivo coordenadas.json lido com {len(coordenadas)} coordenadas"
        }
        
        # Processar CPF (F5 será feito automaticamente no início)
        print(f"\n🔍 Processando CPF: {cpf}")
        etapa_final = {
            "etapa": "Iniciando processamento do CPF",
            "status": "em_andamento",
            "mensagem": f"Processando CPF {cpf}"
        }
        
        dados = processar_cpf_original(driver, wait, pyautogui, coordenadas, cpf)
        
        # Verificar o tipo de resultado retornado
        resultado = dados.get("cliente", {}).get("resultado", "").upper() if isinstance(dados, dict) and "cliente" in dados else ""
        
        # Definir etapa final baseada no resultado
        if "CANCELADO" in resultado:
            etapa_final = {
                "etapa": "Contrato CANCELADO - Dados extraídos",
                "status": "sucesso",
                "mensagem": "Contrato cancelado processado, dados coletados e voltou para pesquisa"
            }
        elif "NEGAD" in resultado:
            etapa_final = {
                "etapa": "Contrato NEGADO - Dados extraídos",
                "status": "sucesso",
                "mensagem": "Contrato negado processado, dados coletados e voltou para pesquisa"
            }
        elif "ACORDO FORMALIZADO" in resultado or "CUMPRIMENTO" in resultado:
            etapa_final = {
                "etapa": "Acordo formalizado - Dados básicos extraídos",
                "status": "sucesso",
                "mensagem": "Acordo em cumprimento identificado, dados da tabela coletados"
            }
        elif "NENHUM CONTRATO LOCALIZADO" in resultado.upper() or "NÃO ENCONTRADO" in resultado.upper():
            etapa_final = {
                "etapa": "CPF não encontrado",
                "status": "alerta",
                "mensagem": "Nenhum contrato localizado para este CPF, modal fechado e voltou para pesquisa"
            }
        elif "MENU NOVA PROPOSTA NAO EXISTE" in resultado.upper():
            etapa_final = {
                "etapa": "Contrato CANCELADO - Menu Nova Proposta não existe",
                "status": "alerta",
                "mensagem": "Contrato cancelado sem acesso ao menu Nova Proposta, fechou menu e voltou para pesquisa"
            }
        else:
            etapa_final = {
                "etapa": "Dados extraídos - Voltou para pesquisa",
                "status": "sucesso",
                "mensagem": "Contrato processado com sucesso, dados completos extraídos"
            }
        
        # Marcar atividade
        session_manager.marcar_atividade()
        
        # Voltar para consulta SEM mudar estado (ainda PROCESSANDO - aguarda callback)
        session_manager.voltar_para_consulta_sem_mudar_estado()
        
        # Retornar sucesso com dados E etapa_final na raiz
        return {
            "success": True,
            "error": None,
            "data": dados,
            "resultados_etapas": [etapa_final]  # Array com 1 elemento - a última etapa
        }
        
    except Exception as e:
        erro_msg = str(e)
        print(f"\n❌ Erro ao processar CPF: {erro_msg}")
        
        # 🔴 ACCESS DENIED: Fechar tudo e parar imediatamente
        if "Access Denied" in erro_msg:
            print("\n🔴 ACCESS DENIED DETECTADO - FECHANDO SISTEMA!")
            print("="*60)
            print("❌ Site bloqueou o acesso (proteção anti-bot)")
            print("🔒 Chrome será fechado. Sistema voltará para AGUARDANDO.")
            print("💡 Tente novamente em alguns minutos.")
            print("="*60)
            
            try:
                session_manager.fechar_chrome()
            except Exception:
                pass
            
            etapa_final = {
                "etapa": "Access Denied - Sistema parado",
                "status": "erro",
                "mensagem": "Site bloqueou o acesso. Chrome fechado. Tente novamente."
            }
            
            return {
                "success": False,
                "error": "Access Denied - site bloqueou o acesso",
                "data": {
                    "cliente": {
                        "nome": "",
                        "cpf": cpf,
                        "resultado": "ACCESS DENIED"
                    }
                },
                "resultados_etapas": [etapa_final]
            }
        
        # ⚠️ IMPORTANTE: Voltar para menu Pesquisa MESMO com erro!
        try:
            print("\n🔙 Tentando voltar para menu Pesquisa após erro...")
            session_manager.voltar_para_consulta_sem_mudar_estado()
            etapa_final = {
                "etapa": "Erro no processamento - Voltou para pesquisa",
                "status": "erro",
                "mensagem": f"Erro: {erro_msg}. Sistema voltou para tela de pesquisa."
            }
        except Exception as voltar_erro:
            print(f"   ⚠️ Erro ao voltar para pesquisa: {voltar_erro}")
            etapa_final = {
                "etapa": "Erro crítico - Não conseguiu voltar para pesquisa",
                "status": "erro",
                "mensagem": f"Erro processamento: {erro_msg}. Erro ao voltar: {voltar_erro}"
            }
        
        # Identificar tipo de erro mais específico
        if "coordenada" in erro_msg.lower():
            etapa_final = {
                "etapa": "Erro - Coordenada não encontrada",
                "status": "erro",
                "mensagem": f"Falta configurar coordenada: {erro_msg}"
            }
        elif "campo_cpf" in erro_msg.lower():
            etapa_final = {
                "etapa": "Erro - Campo CPF não localizado",
                "status": "erro",
                "mensagem": "Coordenada do campo CPF não encontrada. Configure com capturar_coordenadas.py"
            }
        elif "botao_pesquisar" in erro_msg.lower():
            etapa_final = {
                "etapa": "Erro - Botão Pesquisar não localizado",
                "status": "erro",
                "mensagem": "Coordenada do botão Pesquisar não encontrada. Configure com capturar_coordenadas.py"
            }
        elif "nova proposta" in erro_msg.lower():
            etapa_final = {
                "etapa": "Erro - CPF não encontrado ou sem acesso",
                "status": "erro",
                "mensagem": "CPF não retornou resultados ou botão Nova Proposta indisponível"
            }
        elif "conteúdo capturado vazio" in erro_msg.lower():
            etapa_final = {
                "etapa": "Erro - Captura de tela falhou",
                "status": "erro",
                "mensagem": "Ctrl+A / Ctrl+C não capturou conteúdo. Verifique foco na janela."
            }
        elif "timeout" in erro_msg.lower():
            etapa_final = {
                "etapa": "Erro - Timeout ao aguardar elemento",
                "status": "erro",
                "mensagem": "Elemento não apareceu na tela no tempo esperado"
            }
        
        # Retornar erro com estrutura padrão + etapa_final NA RAIZ
        return {
            "success": False,
            "error": erro_msg,
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
                    "resultado": "ERRO NO PROCESSAMENTO"
                },
                "veiculo": {},
                "operacao": {},
                "resumo_proposta": {},
                "estimativa_venda": {}
            },
            "resultados_etapas": [etapa_final]  # Array com 1 elemento - a última etapa
        }
