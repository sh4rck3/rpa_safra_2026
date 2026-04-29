#!/usr/bin/env python3
"""
Capturador de coordenada do botão Nova Proposta na tela de resultados.
Salva em coordenadas.json atualizando a chave 'botao_nova_proposta'.
"""

import json
import time
import sys
from pathlib import Path

try:
    import pyautogui
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyautogui'], check=True)
    import pyautogui

pyautogui.FAILSAFE = False

COORDENADAS_FILE = Path(__file__).parent.parent / "coordenadas.json"


def carregar_coordenadas():
    if COORDENADAS_FILE.exists():
        with open(COORDENADAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_coordenadas(coords):
    with open(COORDENADAS_FILE, "w", encoding="utf-8") as f:
        json.dump(coords, f, indent=2, ensure_ascii=False)


def main():
    print("=" * 60)
    print("📋 CAPTURAR COORDENADA DO BOTÃO NOVA PROPOSTA")
    print("=" * 60)
    print()
    print("1. Abra o Chrome na tela de resultados (após pesquisar)")
    print("2. Posicione o mouse sobre o botão NOVA PROPOSTA")
    print("3. Aguarde a contagem regressiva")
    print()
    input("Pressione ENTER quando estiver pronto...")

    print("\nPositione o mouse sobre o botão NOVA PROPOSTA...")
    for i in range(5, 0, -1):
        pos = pyautogui.position()
        print(f"  {i}... (posição atual: {pos.x}, {pos.y})")
        time.sleep(1)

    x, y = pyautogui.position()
    print(f"\n✅ Capturado 'botao_nova_proposta': x={x}, y={y}")

    coords = carregar_coordenadas()
    coords["botao_nova_proposta"] = {"x": x, "y": y}
    salvar_coordenadas(coords)

    print(f"\n💾 Salvo em {COORDENADAS_FILE}")
    print(f"   botao_nova_proposta: ({x}, {y})")


if __name__ == "__main__":
    main()
