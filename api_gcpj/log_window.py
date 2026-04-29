#!/usr/bin/env python3
"""
Janela flutuante de logs em tempo real
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import sys
from datetime import datetime


class LogWindow:
    """Janela flutuante para exibir logs em tempo real"""
    
    def __init__(self):
        self.window = None
        self.text_widget = None
        self.max_lines = 100  # Máximo de linhas a exibir
        self.is_running = False
        
    def start(self):
        """Inicia a janela em thread separada"""
        if self.is_running:
            return
        
        self.is_running = True
        thread = threading.Thread(target=self._create_window, daemon=True)
        thread.start()
    
    def _create_window(self):
        """Cria a janela Tkinter"""
        self.window = tk.Tk()
        self.window.title("RPA GCPJ - Logs")
        
        # Tamanho e posição (canto inferior direito)
        width = 500
        height = 400
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = screen_width - width - 10
        y = screen_height - height - 70
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Sempre no topo
        self.window.attributes('-topmost', True)
        
        # Estilo
        self.window.configure(bg='#1e1e1e')
        
        # Frame com título
        title_frame = tk.Frame(self.window, bg='#2d2d30', height=30)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        
        title_label = tk.Label(
            title_frame, 
            text="🔄 RPA GCPJ - Logs em Tempo Real",
            bg='#2d2d30',
            fg='#00ff00',
            font=('Consolas', 10, 'bold'),
            pady=5
        )
        title_label.pack()
        
        # Área de texto com scroll
        self.text_widget = scrolledtext.ScrolledText(
            self.window,
            bg='#1e1e1e',
            fg='#d4d4d4',
            font=('Consolas', 9),
            insertbackground='white',
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tags para cores
        self.text_widget.tag_config('timestamp', foreground='#808080')
        self.text_widget.tag_config('success', foreground='#4ec9b0')
        self.text_widget.tag_config('error', foreground='#f48771')
        self.text_widget.tag_config('warning', foreground='#dcdcaa')
        self.text_widget.tag_config('info', foreground='#569cd6')
        
        # Mensagem inicial
        self.add_log("Janela de logs iniciada", 'info')
        
        # Iniciar loop
        self.window.mainloop()
    
    def add_log(self, message, tag='normal'):
        """Adiciona uma linha de log"""
        if not self.text_widget:
            return
        
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            self.text_widget.config(state=tk.NORMAL)
            
            # Adicionar timestamp
            self.text_widget.insert(tk.END, f"[{timestamp}] ", 'timestamp')
            
            # Adicionar mensagem
            self.text_widget.insert(tk.END, f"{message}\n", tag)
            
            # Limitar número de linhas
            lines = int(self.text_widget.index('end-1c').split('.')[0])
            if lines > self.max_lines:
                self.text_widget.delete('1.0', '2.0')
            
            # Auto-scroll para o final
            self.text_widget.see(tk.END)
            
            self.text_widget.config(state=tk.DISABLED)
        except:
            pass  # Ignorar erros se janela foi fechada
    
    def close(self):
        """Fecha a janela"""
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
        self.is_running = False


class LogCapture:
    """Captura prints e redireciona para janela de log"""
    
    def __init__(self, log_window, original_stdout):
        self.log_window = log_window
        self.original_stdout = original_stdout
        self.buffer = ""
    
    def write(self, message):
        # Escrever no stdout original (terminal)
        self.original_stdout.write(message)
        self.original_stdout.flush()
        
        # Adicionar à janela de log
        if message.strip():
            # Determinar tag baseado no conteúdo
            tag = 'normal'
            msg_lower = message.lower()
            
            if '✅' in message or 'sucesso' in msg_lower or 'completo' in msg_lower:
                tag = 'success'
            elif '❌' in message or 'erro' in msg_lower or 'error' in msg_lower:
                tag = 'error'
            elif '⚠️' in message or 'warning' in msg_lower or 'aviso' in msg_lower:
                tag = 'warning'
            elif '🔍' in message or '📋' in message or '🖱️' in message or '📄' in message:
                tag = 'info'
            
            self.log_window.add_log(message.strip(), tag)
    
    def flush(self):
        self.original_stdout.flush()


# Instância global
_log_window = None
_original_stdout = None


def init_log_window():
    """Inicializa a janela de log"""
    global _log_window, _original_stdout
    
    if _log_window is None:
        _log_window = LogWindow()
        _log_window.start()
        
        # Aguardar janela iniciar
        import time
        time.sleep(1)
        
        # Redirecionar stdout
        _original_stdout = sys.stdout
        sys.stdout = LogCapture(_log_window, _original_stdout)
    
    return _log_window


def close_log_window():
    """Fecha a janela de log"""
    global _log_window, _original_stdout
    
    if _log_window:
        _log_window.close()
        _log_window = None
    
    if _original_stdout:
        sys.stdout = _original_stdout
        _original_stdout = None
