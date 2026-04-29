#!/usr/bin/env python3
"""
Modelos Pydantic para API GCPJ
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class ProcessarGCPJRequest(BaseModel):
    """Request para processar um GCPJ"""
    gcpj: str = Field(..., description="Número do GCPJ (ex: 1300285552)")
    callback_url: Optional[str] = Field(None, description="URL para receber callback quando processar terminar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "gcpj": "1300285552",
                "callback_url": "https://seu-sistema.com/webhook"
            }
        }


class ProcessarGCPJResponse(BaseModel):
    """Response imediata ao receber GCPJ"""
    status: str = Field(..., description="Status do processamento")
    gcpj: str = Field(..., description="Número do GCPJ recebido")
    message: str = Field(..., description="Mensagem informativa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "processando",
                "gcpj": "1300285552",
                "message": "GCPJ adicionado à fila de processamento"
            }
        }


class StatusResponse(BaseModel):
    """Response do endpoint /status"""
    estado: str = Field(..., description="Estado atual da sessão")
    chrome_aberto: bool = Field(..., description="Se o Chrome está aberto")
    pronto_para_processar: bool = Field(..., description="Se está pronto para receber novo GCPJ")
    ultima_atividade: Optional[str] = Field(None, description="Timestamp da última atividade")
    tempo_inativo_segundos: Optional[int] = Field(None, description="Tempo inativo em segundos")
    fecha_em_segundos: Optional[int] = Field(None, description="Tempo restante até fechar Chrome")
    total_processados: int = Field(0, description="Total de GCPJs processados")
    total_erros: int = Field(0, description="Total de erros")
    
    class Config:
        json_schema_extra = {
            "example": {
                "estado": "OCIOSO_LOGADO",
                "chrome_aberto": True,
                "pronto_para_processar": True,
                "ultima_atividade": "2026-01-07 14:28:00",
                "tempo_inativo_segundos": 45,
                "fecha_em_segundos": 555,
                "total_processados": 10,
                "total_erros": 0
            }
        }


class HealthResponse(BaseModel):
    """Response do endpoint /health"""
    status: str = Field(..., description="Status geral da API")
    pronto_para_processar: bool = Field(..., description="Se está pronto para receber novo GCPJ")
    estado_sessao: str = Field(..., description="Estado da sessão")
    chrome_aberto: bool = Field(..., description="Se o Chrome está aberto")
    uptime_seconds: int = Field(..., description="Tempo de execução em segundos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "pronto_para_processar": True,
                "estado_sessao": "OCIOSO_LOGADO",
                "chrome_aberto": True,
                "uptime_seconds": 3600
            }
        }


class FecharSessaoResponse(BaseModel):
    """Response do endpoint /fechar-sessao"""
    message: str = Field(..., description="Mensagem de confirmação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Chrome fechado com sucesso"
            }
        }


class CallbackPayload(BaseModel):
    """Payload enviado para o callback"""
    success: bool = Field(..., description="Se o processamento foi bem-sucedido")
    gcpj: str = Field(..., description="Número do GCPJ processado")
    timestamp: str = Field(..., description="Timestamp do processamento")
    data_processamento: str = Field(..., description="Data do processamento")
    hora_processamento: str = Field(..., description="Hora do processamento")
    processing_time: int = Field(..., description="Tempo de processamento em segundos")
    error: Optional[str] = Field(None, description="Mensagem de erro se houver")
    data: Dict[str, Any] = Field(..., description="Dados extraídos do GCPJ")
