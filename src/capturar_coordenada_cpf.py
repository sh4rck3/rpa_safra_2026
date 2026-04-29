#!/usr/bin/env python3
"""
Capturador de coordenada do campo CPF/CNPJ na tela de Pesquisa de Contratos.
Salva em coordenadas.json atualizando a chave 'campo_cpf'.
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
    print("=" * 60)
    print("📍 CAPTURADOR DE COORDENADA - CAMPO CPF/CNPJ")
    print("=" * 60)
    print()
    print("INSTRUÇÕES:")
    print("1. Abra o Chrome na tela de Pesquisa de Contratos")
    print("   (faça login e navegue até a tela de pesquisa)")
    print("2. Posicione o mouse DENTRO do campo CPF / CNPJ:")
    print("   (o input branco ao lado do label 'CPF / CNPJ:')")
    print("3. Aguarde 5 segundos sem mover o mouse")
    print()
    input("Pressione ENTER quando estiver pronto...")

    coords = carregar_coordenadas()

    coord = capturar_ponto("campo_cpf", "Posicione o mouse DENTRO do input CPF / CNPJ")
    coords["campo_cpf"] = coord

    salvar_coordenadas(coords)

    print(f"\n{'='*60}")
    print(f"✅ Coordenada 'campo_cpf' salva: x={coord['x']}, y={coord['y']}")
    print(f"📁 Arquivo: {COORDENADAS_FILE}")
    print(f"📊 Total de coordenadas: {len(coords)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
