#!/usr/bin/env python3
"""
Script auxiliar para capturar coordenadas do campo CPF
Execute este script ENQUANTO o test_login.py está pausado
"""

try:
    import pyautogui
    print("✓ PyAutoGUI instalado")
except ImportError:
    print("✗ PyAutoGUI não instalado. Instalando...")
    import subprocess
    subprocess.run(['venv/Scripts/pip.exe', 'install', 'pyautogui'], check=True)
    import pyautogui

import time

print("=" * 60)
print("CAPTURADOR DE COORDENADAS DO MOUSE")
print("=" * 60)
print("\nInstruções:")
print("1. Certifique-se que o navegador está aberto na página de Pesquisa")
print("2. Posicione o mouse SOBRE o campo CPF")
print("3. Espere 5 segundos SEM MOVER o mouse")
print("\nIniciando em 3 segundos...")
time.sleep(3)

print("\nCapturando posição em 5 segundos...")
print("Posicione o mouse sobre o campo CPF AGORA!")

for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

# Capturar posição
x, y = pyautogui.position()
screen_width, screen_height = pyautogui.size()

print("\n" + "=" * 60)
print("COORDENADAS CAPTURADAS!")
print("=" * 60)
print(f"\nPosição do mouse:")
print(f"  X: {x}")
print(f"  Y: {y}")
print(f"\nResolução da tela:")
print(f"  Largura: {screen_width}")
print(f"  Altura: {screen_height}")
print(f"\nPosição relativa:")
print(f"  Horizontal: {(x/screen_width)*100:.1f}%")
print(f"  Vertical: {(y/screen_height)*100:.1f}%")
print("\n" + "=" * 60)
print("\nCOLE ESSAS INFORMAÇÕES NO CHAT!")
print("=" * 60)
