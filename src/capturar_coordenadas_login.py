#!/usr/bin/env python3
"""
Capturador de coordenadas para a tela de LOGIN do Safra.
Abre o Chrome na página de login e captura 3 pontos:
  1. Campo Username
  2. Campo Password
  3. Botão Login

Salva em coordenadas.json junto com as coordenadas já existentes.
"""

import json
import time
import os
import sys
from pathlib import Path

try:
    import pyautogui
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyautogui'], check=True)
    import pyautogui

# Desabilitar failsafe
pyautogui.FAILSAFE = False

COORDENADAS_FILE = Path(__file__).parent.parent / "coordenadas.json"

CAMPOS_LOGIN = [
    ("login_campo_username", "Posicione o mouse sobre o CAMPO USERNAME (email/usuário)"),
    ("login_campo_password", "Posicione o mouse sobre o CAMPO PASSWORD (senha)"),
    ("login_botao_entrar", "Posicione o mouse sobre o BOTÃO LOGIN/ENTRAR"),
]


def carregar_coordenadas():
    if COORDENADAS_FILE.exists():
        with open(COORDENADAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_coordenadas(coords):
    with open(COORDENADAS_FILE, "w", encoding="utf-8") as f:
        json.dump(coords, f, indent=2, ensure_ascii=False)


def capturar_ponto(nome, instrucao):
    print(f"\n{'='*60}")
    print(f"📍 {instrucao}")
    print(f"{'='*60}")
    print("Posicione o mouse e aguarde 5 segundos...")
    
    for i in range(5, 0, -1):
        pos = pyautogui.position()
        print(f"  {i}... (posição atual: {pos.x}, {pos.y})")
        time.sleep(1)
    
    x, y = pyautogui.position()
    print(f"\n✅ Capturado '{nome}': x={x}, y={y}")
    return {"x": x, "y": y}


def main():
    print("="*60)
    print("🔐 CAPTURADOR DE COORDENADAS - TELA DE LOGIN SAFRA")
    print("="*60)
    print()
    print("INSTRUÇÕES:")
    print("1. Abra o Chrome MANUALMENTE na página de login:")
    print("   https://wwws.jsafra.com.br/FinanceiraVeiculos/LoginForm")
    print("2. Deixe a página carregada com os campos visíveis")
    print("3. Para cada campo, posicione o mouse e espere 5s")
    print()
    input("Pressione ENTER quando a página de login estiver aberta...")
    
    coords = carregar_coordenadas()
    
    for nome, instrucao in CAMPOS_LOGIN:
        coords[nome] = capturar_ponto(nome, instrucao)
    
    salvar_coordenadas(coords)
    
    print(f"\n{'='*60}")
    print("✅ COORDENADAS DE LOGIN SALVAS!")
    print(f"{'='*60}")
    print(f"Arquivo: {COORDENADAS_FILE}")
    print(f"\nCoordenadas capturadas:")
    for nome, _ in CAMPOS_LOGIN:
        c = coords[nome]
        print(f"  {nome}: ({c['x']}, {c['y']})")
    print(f"\n💡 Agora reinicie a API para testar o login com coordenadas.")


if __name__ == "__main__":
    main()
