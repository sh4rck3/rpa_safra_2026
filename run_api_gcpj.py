#!/usr/bin/env python3
"""
Script de inicialização da API GCPJ
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    # Configurações da API
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8001))
    
    print("="*60)
    print("🚀 INICIANDO RPA GCPJ API")
    print("="*60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Docs: http://localhost:{port}/docs")
    print("="*60)
    print("\n💡 IMPORTANTE:")
    print("   - Sempre consulte /health antes de enviar GCPJ")
    print("   - Aguarde callback antes de enviar próximo GCPJ")
    print("   - Chrome fecha após 10 min de inatividade")
    print("\nPressione Ctrl+C para parar\n")
    
    # Iniciar servidor
    uvicorn.run(
        "api_gcpj.main:app",
        host=host,
        port=port,
        reload=False,  # Não usar reload em produção
        log_level="info"
    )
