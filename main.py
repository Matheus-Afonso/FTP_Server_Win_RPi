"""
Criado 22 de novembro

Main do servidor FTP para Windowns para se conectar ao RPi

Executar no Windows: main.py
Executar no RPi: ftp_listener_nogui.py

"""

from FTP_Client_GUI import FTPGUI
import tkinter as tk
import sys

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s')
    logging.disable(logging.CRITICAL)

    master = tk.Tk()
    app = FTPGUI(master)
    app.start_GUI()

    # Testa para ver se a conexão ainda está aberta após fechar a janela
    try:
        app.conn.getsockname()
        # Conexão ativa. Encerrar o outro lado
        app.enviar_comando('exit')
    except (OSError, AttributeError) as error:
        # Conexão inativa.
        pass
    
    sys.exit()
