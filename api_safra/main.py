#!/usr/bin/env python3
"""
API FastAPI para receber requisições de processamento de CPF
"""

import os
import time
import requests
import threading
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from dotenv import load_dotenv

try:
    from api_safra.session_manager import SessionManager
    from api_safra.processor import processar_cpf_completo
    from api_safra.log_window import init_log_window, close_log_window
except ImportError:
    from session_manager import SessionManager
    from processor import processar_cpf_completo
    from log_window import init_log_window, close_log_window

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar FastAPI
app = FastAPI(
    title="RPA Safra API",
    description="API para processamento de CPF via automação web",
    version="1.0.9"
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

# Lock para processar um CPF por vez
processing_lock = threading.Lock()


# Modelos Pydantic
class ProcessarCPFRequest(BaseModel):
    cpf_id: int
    cpf: str
    nome: str
    contrato: str
    batch_id: Optional[int] = None
    callback_url: Optional[str] = None


class ProcessarCPFResponse(BaseModel):
    status: str
    cpf: str
    message: str


class StatusResponse(BaseModel):
    estado: str
    chrome_aberto: bool
    pronto_para_processar: bool
    ultima_atividade: Optional[str]
    tempo_inativo_segundos: int
    fecha_em_segundos: int
    total_processados: int
    total_erros: int


class HealthResponse(BaseModel):
    status: str
    pronto_para_processar: bool
    estado_sessao: str
    chrome_aberto: bool
    uptime_seconds: int


class FecharSessaoResponse(BaseModel):
    message: str


def processar_job_background(job: dict):
    """
    Processa um CPF em background (thread separada)
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
        print(f"CPF ID: {job['cpf_id']}")
        print(f"CPF: {job['cpf']}")
        print(f"Nome: {job['nome']}")
        print(f"Contrato: {job['contrato']}")
        print(f"{'='*60}\n")
        
        # Processar CPF (já volta para tela de consulta dentro)
        resultado = processar_cpf_completo(session_manager, job['cpf'])
        
        # Atualizar estatísticas
        if resultado.get("success", False):
            stats["total_processados"] += 1
        else:
            stats["total_erros"] += 1
        
        # Preparar payload para callback
        callback_payload = {
            "cpf_id": job['cpf_id'],
            "batch_id": job.get('batch_id'),
            "success": resultado.get("success", False),
            "cpf": job['cpf'],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": resultado.get("error"),
            "data": resultado.get("data", {}),
            "resultados_etapas": resultado.get("resultados_etapas", [])
        }
        
        # Enviar callback se fornecido
        if job.get('callback_url'):
            print(f"\n📤 Enviando resultado para callback...")
            sucesso_callback = enviar_callback(job['callback_url'], callback_payload)
            
            if not sucesso_callback:
                # ❌ CALLBACK FALHOU - NÃO LIBERA LOCK E NÃO MUDA ESTADO
                print(f"\n{'='*60}")
                print(f"🔴 SISTEMA TRAVADO!")
                print(f"{'='*60}")
                print(f"❌ Laravel não respondeu ao callback do CPF {job['cpf']}")
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
        import traceback
        traceback.print_exc()
        stats["total_erros"] += 1
        
        # Preparar payload de erro
        error_payload = {
            "cpf_id": job['cpf_id'],
            "batch_id": job.get('batch_id'),
            "success": False,
            "cpf": job['cpf'],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e),
            "data": {},
            "resultados_etapas": [{
                "etapa": "Erro crítico",
                "status": "erro",
                "mensagem": str(e)
            }]
        }
        
        # Tentar enviar callback de erro
        if job.get('callback_url'):
            sucesso_callback = enviar_callback(job['callback_url'], error_payload)
            
            if not sucesso_callback:
                # ❌ CALLBACK FALHOU - NÃO LIBERA LOCK
                print(f"\n{'='*60}")
                print(f"🔴 SISTEMA TRAVADO!")
                print(f"{'='*60}")
                print(f"❌ Laravel não respondeu ao callback do CPF {job['cpf']}")
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
        "api": "RPA Safra API",
        "version": "1.0.9",
        "status": "online",
        "descricao": "API para processamento de CPF via automação web",
        
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
            "processar": "POST /processar - Processa um CPF",
            "fechar": "POST /fechar-sessao - Fecha o Chrome",
            "docs": "GET /docs - Documentação interativa"
        },
        
        "importante": "Sempre consulte /health antes de enviar um novo CPF!"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """
    Health check - Verifica se API está pronta para processar
    
    IMPORTANTE: Sempre consultar este endpoint antes de enviar novo CPF!
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


@app.post("/processar", response_model=ProcessarCPFResponse, tags=["Processamento"])
async def processar_cpf_endpoint(request: ProcessarCPFRequest, background_tasks: BackgroundTasks):
    """
    Processa um CPF
    
    O processamento é feito em background (assíncrono).
    A resposta é imediata e o callback será enviado quando terminar.
    
    **Fluxo:**
    1. API recebe CPF e retorna resposta imediata
    2. Processamento inicia em background
    3. Quando terminar, envia resultado via callback (se fornecido)
    
    **IMPORTANTE:**
    - Só enviar novo CPF quando /health retornar pronto_para_processar=true
    - Aguardar callback antes de enviar próximo CPF
    """
    
    cpf = request.cpf.strip()
    
    print(f"\n📥 Nova requisição recebida: CPF {cpf}")
    
    # Verificar se já está processando (sem travar o lock)
    if processing_lock.locked():
        raise HTTPException(
            status_code=409,
            detail="Sistema ocupado processando outro CPF. Tente novamente em instantes."
        )
    
    # Preparar job
    job = {
        "cpf_id": request.cpf_id,
        "cpf": cpf,
        "nome": request.nome,
        "contrato": request.contrato,
        "batch_id": request.batch_id,
        "callback_url": request.callback_url
    }
    
    # Adicionar job ao background
    background_tasks.add_task(processar_job_background, job)
    
    return ProcessarCPFResponse(
        status="processando",
        cpf=cpf,
        message="CPF adicionado à fila de processamento"
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
    print("🚀 API SAFRA INICIADA")
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
    print("⚠️  DESLIGANDO API SAFRA")
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


# Handler para erros de validação
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler customizado para erros de validação"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "status": "validation_error",
            "message": "Erro de validação nos dados enviados",
            "errors": errors
        }
    )
