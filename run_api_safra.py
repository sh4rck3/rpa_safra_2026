#!/usr/bin/env python3
"""
Script de inicialização da API
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    # Configurações da API
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    print("="*60)
    print("🚀 INICIANDO RPA SAFRA API")
    print("="*60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print("="*60)
    print("\nPressione Ctrl+C para parar\n")
    
    # Iniciar servidor
    uvicorn.run(
        "api_safra.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
