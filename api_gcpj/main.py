#!/usr/bin/env python3
"""
API FastAPI para receber requisições de processamento de GCPJ
"""

import os
import time
import requests
import threading
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

try:
    from api_gcpj.session_manager import SessionManager
    from api_gcpj.processor import processar_gcpj
    from api_gcpj.log_window import init_log_window, close_log_window
    from api_gcpj.models import (
        ProcessarGCPJRequest,
        ProcessarGCPJResponse,
        StatusResponse,
        HealthResponse,
        FecharSessaoResponse
    )
except ImportError:
    from session_manager import SessionManager
    from processor import processar_gcpj
    from log_window import init_log_window, close_log_window
    from models import (
        ProcessarGCPJRequest,
        ProcessarGCPJResponse,
        StatusResponse,
        HealthResponse,
        FecharSessaoResponse
    )

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar FastAPI
app = FastAPI(
    title="RPA GCPJ API",
    description="API para processamento de processos GCPJ via automação web",
    version="1.0.0"
)

# Tempo de início
START_TIME = time.time()

# Instância global do SessionManager
session_manager = SessionManager()

# Estatísticas
stats = {
    "total_processados": 0,
    "total_erros": 0
}

# Lock para processar um GCPJ por vez
processing_lock = threading.Lock()


def processar_job_background(gcpj: str, callback_url: Optional[str]):
    """
    Processa um GCPJ em background (thread separada)
    Envia callback quando terminar
    
    ⚠️ IMPORTANTE: Lock só é liberado após callback com sucesso!
    Se callback falhar, sistema fica TRAVADO até resolução manual.
    """
    
    # Tentar adquirir lock (não bloqueia se já estiver processando)
    if not processing_lock.acquire(blocking=False):
        print(f"\n⚠️  Já existe um processamento em andamento")
        return
    
    try:
        print(f"\n{'='*60}")
        print(f"🔄 INICIANDO PROCESSAMENTO EM BACKGROUND")
        print(f"{'='*60}")
        print(f"GCPJ: {gcpj}")
        if callback_url:
            print(f"Callback: {callback_url}")
        print(f"{'='*60}\n")
        
        # Processar GCPJ (já volta para tela de consulta dentro)
        resultado = processar_gcpj(session_manager, gcpj)
        
        # Atualizar estatísticas
        if resultado["success"]:
            stats["total_processados"] += 1
        else:
            stats["total_erros"] += 1
        
        # Enviar callback se fornecido
        if callback_url:
            print(f"\n📤 Enviando resultado para callback...")
            sucesso_callback = enviar_callback(callback_url, resultado)
            
            if not sucesso_callback:
                # ❌ CALLBACK FALHOU - NÃO LIBERA LOCK E NÃO MUDA ESTADO
                print(f"\n{'='*60}")
                print(f"🔴 SISTEMA TRAVADO!")
                print(f"{'='*60}")
                print(f"❌ Laravel não respondeu ao callback do GCPJ {gcpj}")
                print(f"⚠️  Sistema permanecerá TRAVADO até resolução manual")
                print(f"💡 Reinicie a API ou corrija o endpoint Laravel")
                print(f"   Estado atual: PROCESSANDO (não mudou para OCIOSO_LOGADO)")
                print(f"{'='*60}\n")
                return  # NÃO libera lock, estado continua PROCESSANDO
        
        # ✅ Callback com sucesso! Mudar estado e liberar lock
        print(f"\n✅ Callback confirmado pelo Laravel!")
        session_manager.finalizar_processamento()  # Muda para OCIOSO_LOGADO
        processing_lock.release()
        
    except Exception as e:
        print(f"\n❌ Erro no processamento em background: {e}")
        stats["total_erros"] += 1
        
        # Tentar enviar callback de erro
        if callback_url:
            resultado_erro = {
                "success": False,
                "gcpj": gcpj,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e),
                "data": {}
            }
            sucesso_callback = enviar_callback(callback_url, resultado_erro)
            
            if not sucesso_callback:
                # ❌ CALLBACK FALHOU - NÃO LIBERA LOCK
                print(f"\n{'='*60}")
                print(f"🔴 SISTEMA TRAVADO!")
                print(f"{'='*60}")
                print(f"❌ Laravel não respondeu ao callback do GCPJ {gcpj}")
                print(f"⚠️  Sistema permanecerá TRAVADO até resolução manual")
                print(f"💡 Reinicie a API ou corrija o endpoint Laravel")
                print(f"   Estado atual: PROCESSANDO (não mudou para OCIOSO_LOGADO)")
                print(f"{'='*60}\n")
                return  # NÃO libera lock, estado continua PROCESSANDO
        
        # Se chegou aqui, callback teve sucesso ou não tinha callback
        print(f"\n✅ Liberando sistema após erro processado...")
        session_manager.finalizar_processamento()  # Muda para OCIOSO_LOGADO
        processing_lock.release()


def enviar_callback(url: str, payload: dict) -> bool:
    """
    Envia callback via POST
    
    Returns:
        bool: True se callback foi enviado com sucesso, False caso contrário
    """
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Callback enviado com sucesso!")
        print(f"   Status: {response.status_code}")
        
        if response.text:
            print(f"   Resposta: {response.text[:200]}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar callback: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Resposta: {e.response.text[:200]}")
        
        return False


@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raiz - Informações da API
    
    Retorna informações sobre a API e status atual
    """
    
    status = session_manager.get_status_detalhado()
    uptime = int(time.time() - START_TIME)
    
    # Calcular uptime formatado
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60
    uptime_formatted = f"{hours}h {minutes}m {seconds}s"
    
    return {
        "api": "RPA GCPJ API",
        "version": "1.0.0",
        "status": "online",
        "descricao": "API para processamento de processos GCPJ via automação web",
        
        "sessao": {
            "estado": status["estado"],
            "chrome_aberto": status["chrome_aberto"],
            "pronto_para_processar": status["pronto_para_processar"],
            "ultima_atividade": status["ultima_atividade"],
            "tempo_inativo_segundos": status["tempo_inativo_segundos"],
            "fecha_em_segundos": status["fecha_em_segundos"]
        },
        
        "estatisticas": {
            "total_processados": stats["total_processados"],
            "total_erros": stats["total_erros"],
            "uptime_segundos": uptime,
            "uptime_formatado": uptime_formatted
        },
        
        "informacoes": {
            "timeout_inatividade_minutos": session_manager.timeout_inatividade // 60,
            "coordenadas_carregadas": len(session_manager.coordenadas)
        },
        
        "endpoints": {
            "health": "GET /health - Verifica se está pronto para processar",
            "status": "GET /status - Status detalhado da sessão",
            "processar": "POST /processar-gcpj - Processa um GCPJ",
            "fechar": "POST /fechar-sessao - Fecha o Chrome",
            "docs": "GET /docs - Documentação interativa"
        },
        
        "importante": "Sempre consulte /health antes de enviar um novo GCPJ!"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """
    Health check - Verifica se API está pronta para processar
    
    IMPORTANTE: Sempre consultar este endpoint antes de enviar novo GCPJ!
    O campo 'pronto_para_processar' indica se pode enviar requisição.
    """
    
    status = session_manager.get_status_detalhado()
    uptime = int(time.time() - START_TIME)
    
    return HealthResponse(
        status="ok",
        pronto_para_processar=status["pronto_para_processar"],
        estado_sessao=status["estado"],
        chrome_aberto=status["chrome_aberto"],
        uptime_seconds=uptime
    )


@app.get("/status", response_model=StatusResponse, tags=["Status"])
async def get_status():
    """
    Retorna status detalhado da sessão
    
    Inclui informações sobre:
    - Estado atual da sessão
    - Se Chrome está aberto
    - Última atividade
    - Tempo de inatividade
    - Estatísticas de processamento
    """
    
    status = session_manager.get_status_detalhado()
    
    return StatusResponse(
        estado=status["estado"],
        chrome_aberto=status["chrome_aberto"],
        pronto_para_processar=status["pronto_para_processar"],
        ultima_atividade=status["ultima_atividade"],
        tempo_inativo_segundos=status["tempo_inativo_segundos"],
        fecha_em_segundos=status["fecha_em_segundos"],
        total_processados=stats["total_processados"],
        total_erros=stats["total_erros"]
    )


@app.post("/processar-gcpj", response_model=ProcessarGCPJResponse, tags=["Processamento"])
async def processar_gcpj_endpoint(request: ProcessarGCPJRequest, background_tasks: BackgroundTasks):
    """
    Processa um número GCPJ
    
    O processamento é feito em background (assíncrono).
    A resposta é imediata e o callback será enviado quando terminar.
    
    **Fluxo:**
    1. API recebe GCPJ e retorna resposta imediata
    2. Processamento inicia em background
    3. Quando terminar, envia resultado via callback (se fornecido)
    
    **IMPORTANTE:**
    - Só enviar novo GCPJ quando /health retornar pronto_para_processar=true
    - Aguardar callback antes de enviar próximo GCPJ
    """
    
    gcpj = request.gcpj.strip()
    
    print(f"\n📥 Nova requisição recebida: GCPJ {gcpj}")
    
    # Validar GCPJ (deve ter 10 dígitos)
    if not gcpj.isdigit() or len(gcpj) != 10:
        raise HTTPException(
            status_code=400,
            detail="GCPJ inválido. Deve conter exatamente 10 dígitos numéricos."
        )
    
    # Verificar se já está processando (sem travar o lock)
    if processing_lock.locked():
        raise HTTPException(
            status_code=409,
            detail="Sistema ocupado processando outro GCPJ. Tente novamente em instantes."
        )
    
    # Adicionar job ao background
    background_tasks.add_task(processar_job_background, gcpj, request.callback_url)
    
    return ProcessarGCPJResponse(
        status="processando",
        gcpj=gcpj,
        message="GCPJ adicionado à fila de processamento"
    )


@app.post("/fechar-sessao", response_model=FecharSessaoResponse, tags=["Sessão"])
async def fechar_sessao():
    """
    Força o fechamento do Chrome
    
    Use este endpoint para fechar o Chrome manualmente,
    sem esperar o timeout de inatividade.
    """
    
    print("\n🔴 Requisição para fechar sessão recebida")
    
    if session_manager.is_chrome_open():
        session_manager.fechar_chrome()
        return FecharSessaoResponse(message="Chrome fechado com sucesso")
    else:
        return FecharSessaoResponse(message="Chrome já estava fechado")


@app.on_event("startup")
async def startup_event():
    """Executado quando a API inicia"""
    
    # Iniciar janela de logs flutuante
    print("🪟 Iniciando janela de logs flutuante...")
    init_log_window()
    
    print("\n" + "="*60)
    print("🚀 API GCPJ INICIADA")
    print("="*60)
    print(f"Estado inicial: {session_manager.estado}")
    print(f"Timeout de inatividade: {session_manager.timeout_inatividade}s")
    print(f"Chrome será fechado após {session_manager.timeout_inatividade // 60} minutos sem atividade")
    print("💡 Chrome abrirá automaticamente ao receber primeira requisição")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Executado quando a API é desligada"""
    print("\n" + "="*60)
    print("⚠️  DESLIGANDO API GCPJ")
    print("="*60)
    
    if session_manager.is_chrome_open():
        print("🔴 Fechando Chrome...")
        session_manager.fechar_chrome()
    
    # Fechar janela de logs
    print("🪟 Fechando janela de logs...")
    close_log_window()
    
    print("✅ API desligada com sucesso")
    print("="*60 + "\n")


# Tratamento de exceções global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global de exceções"""
    print(f"\n❌ Erro não tratado: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor",
            "error": str(exc)
        }
    )
