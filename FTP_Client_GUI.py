# coding: UTF-8
#! python3

"""
Criado 19 de novembro

GUI do servidor FTP para Windows para se conectar ao RPi
"""

from FTP_Client import FTPClient
import tkinter as tk
import sys
import socket
import os
import threading

class FTPGUI(FTPClient):
    def __init__(self, master=None):
        # Inicio da classe FTPClient.
        super().__init__()
        
        #Condições iniciais
        self.master = master
        self.flag_thread = False
        master.title("Servidor FTP - V0.1.2")
        master.resizable(0, 0)

        self.image_down = tk.PhotoImage(file='icons\\download.png')
        self.image_up = tk.PhotoImage(file='icons\\upload.png')
        self.image_conn = tk.PhotoImage(file='icons\\connect.png')
        self.image_abrir = tk.PhotoImage(file='icons\\open.png')
        self.image_disconn = tk.PhotoImage(file='icons\\disconnect.png')

        # Primeira Linha: Label de título
        label_title = tk.Label(master, text="Insira o IP de destino")
        label_title['font'] = ('Arial', 10, 'bold')
        label_title.grid(row=0, column=0, columnspan=5, pady=4)

        # Segunda Linha: Entry do IP e botão de conectar
        self.campo_ip = tk.Entry(master, bd=3, width=150)
        self.campo_ip.bind('<Return>', lambda event: self.criar_thread("conectar"))
        self.campo_ip.grid(row=1, column=0, columnspan=4, padx=3)
        
        self.botao_conn = tk.Button(master, text="Conectar", bd=3, compound='left', image=self.image_conn)
        self.botao_conn['command'] = lambda: self.criar_thread("conectar")
        self.botao_conn.grid(row=1, column=4, padx=4)

        #Terceira Linha: Entry com o caminho atual do RPi e botão de ir
        self.campo_path = tk.Entry(master, bd=3, width=150, state='disabled')
        self.campo_path.bind('<Return>', self.ir_para_path)
        self.campo_path.grid(row=2, column=0, pady=4, columnspan=4)

        self.botao_path = tk.Button(master, text="Abrir", bd=3, compound='left', image=self.image_abrir)
        self.botao_path['command'] = self.ir_para_path
        self.botao_path['state'] = 'disabled'
        self.botao_path.bind('<Return>', self.ir_para_path)
        self.botao_path.grid(row=2, column=4, padx=4, sticky='we')

        #Quarta a Sexta Linha: 2 Listbox + botões entre ele
        self.pastas_local = tk.StringVar(value="Aguardando1...")
        self.pastas_remoto = tk.StringVar(value="Aguardando2...")

        self.list_local = tk.Listbox(master, bd=3, listvariable=self.pastas_local, width=75, height=25)
        self.list_local.bind('<Double-Button-1>', self.click_pasta_local)
        self.list_local.grid(row=3, column=0, pady=4, padx=3, sticky='we', rowspan=3)
        
        self.botao_up = tk.Button(master, bd=3, image=self.image_up, state='disabled')
        self.botao_up['command'] = lambda: self.criar_thread("upload")
        self.botao_up.grid(row=3, column=1, sticky='w', columnspan=2)
        
        self.botao_down = tk.Button(master, bd=3, image=self.image_down, state='disabled')
        self.botao_down['command'] = lambda: self.criar_thread("download")
        self.botao_down.grid(row=5, column=1, sticky='w', columnspan=2)

        self.list_remoto = tk.Listbox(master, bd=3, listvariable=self.pastas_remoto, width=75, height=25)
        self.list_remoto.bind('<Double-Button-1>', self.click_pasta_remote)
        self.list_remoto.grid(row=3, column=3, pady=4, padx=6, sticky = 'e', rowspan=3, columnspan=2)

        # Sétima linha em diante: Terminal
        self.terminal = tk.Text(master, bd=3, height=15, bg='black', fg='white', blockcursor=True, insertbackground='white')
        self.terminal['state'] = 'disabled'
        self.terminal.grid(row=6, column=0, columnspan=5, pady=10, padx=3, sticky='we')
        
        #Extra: Menu Drop-down
        menu_drop = tk.Menu(master)
        master.config(menu = menu_drop)
        
        opt_menu = tk.Menu(master)
        menu_drop.add_cascade(label = "Opções", menu = opt_menu)
        opt_menu.add_command(label = 'Limpar terminal', command = self.clear_terminal)
        
    # ---Funções para habilitar e desabilitar conexão com o remoto ---
    def connect(self):
        ip = self.campo_ip.get()
        if ip != '' and not ip.isspace():
            self.print_terminal("Conectando ao IP %s" % ip)
            self.master['cursor'] = 'wait'
            resposta = self.init_conn(ip, 4444)
            self.print_terminal(resposta)
            self.master['cursor'] = ''

            if '[+]' in resposta:
                self.habilitar_transfer()
                self.update_path()
                self.update_local_archives()
                self.update_remote_arquives()
        else:
            self.print_terminal("[-] IP '%s' inválido" % ip)
        
        self.flag_thread = False
            
    def habilitar_transfer(self):
        self.campo_path['state'] = 'normal'
        self.botao_path['state'] = 'normal'
        self.botao_down['state'] = 'normal'
        self.botao_up['state'] = 'normal'

        # Bloquear o campo de ip e trocar o botão de conectar por um de desconectar
        self.campo_ip['state'] = 'disabled'
        self.botao_conn['text'] = 'Encerrar'
        self.botao_conn['image'] = self.image_disconn
        self.botao_conn['command'] = self.desabilitar_transfer

    def desabilitar_transfer(self):
        resposta = self.enviar_comando("exit")
        self.campo_ip['state'] = 'normal'
        self.botao_conn['text'] = 'Conectar'
        self.botao_conn['image'] = self.image_conn
        self.botao_conn['command'] = self.connect

        # Apagar Listbox
        self.pastas_local.set('Aguardando1...')
        self.pastas_remoto.set('Aguardando2...')
        
        # Desabilitar todos os botões
        self.campo_path['state'] = 'disabled'
        self.botao_path['state'] = 'disabled'
        self.botao_down['state'] = 'disabled'
        self.botao_up['state'] = 'disabled'

        self.print_terminal(resposta)
    
    # ---Funções para o campo_path (local remoto) ---
    def update_path(self):
        #Pegar a pasta atual e jogar no campo_path
        pasta_remote = self.enviar_comando('pwd')
        self.campo_path.delete(0, 'end')
        self.campo_path.insert(0, pasta_remote)

    def ir_para_path(self, event=None):
        path = self.campo_path.get()
        self.mudar_pasta_remote(path)
    
    # ---Funções para arquivos remotos ---
    def update_remote_arquives(self):
        arqs = self.enviar_comando('listar')
        self.pastas_remoto.set(arqs)

    def click_pasta_remote(self, event=None): 
        # Pega o texto da opção selecionada
        select = self.list_remoto.get('active')
        # Checa se é uma pasta
        if select.startswith('--'):
            self.mudar_pasta_remote(select[2:])
            self.update_path()
        elif select == '..':
            self.mudar_pasta_remote('..')
            self.update_path()

    def mudar_pasta_remote(self, path):
        resposta = self.enviar_comando(['cd', path])
        if '[+]' in resposta:
            self.update_remote_arquives()
        else:
            self.print_terminal(resposta)
    
    # ---Funções para arquivos locais ---
    def update_local_archives(self):
        dirs, arqs = self.list_client_directory()
        dirs = ['--' + s for s in dirs]
        #Adiciona o item de voltar
        self.pastas_local.set(['..'] + dirs + arqs)

    def click_pasta_local(self, event=None):
        select = self.list_local.get('active')
        
        if select.startswith('--'):
            self.mudar_pasta_local(select[2:])
        elif select == '..':
            self.mudar_pasta_local(select)
            
    def mudar_pasta_local(self, path):
        resposta = self.change_client_directory(path)
        if '[+]' in resposta:
            self.update_local_archives()
        else:
            self.print_terminal(resposta)

    # ---Funções de transferência de arquivos ---
    def download_arquivo(self):
        arq_remote = self.list_remoto.get('active')
        if not arq_remote.startswith('--') and arq_remote != '..':
            self.print_terminal("[*] Download em progresso...")
            self.estado_carregar(True)

            result = self.enviar_comando(['download', arq_remote])
            result = FTPClient.save_file(result, arq_remote)
            
            self.print_terminal(result)
            self.update_local_archives()
            self.estado_carregar(False)
        
        self.flag_thread = False

    def upload_arquivo(self):
        arq_local = self.list_local.get('active')
        if not arq_local.startswith('--') and arq_local != '..':
            self.print_terminal("[*] Upload em progresso...")
            self.estado_carregar(True)

            data_local = FTPClient.read_file(arq_local)
            result = self.enviar_comando(['upload', arq_local, data_local])
            
            self.print_terminal(result)
            self.update_remote_arquives()
            self.estado_carregar(False)
        
        self.flag_thread = False
    
    # ---Função de threading ---
    def criar_thread(self, modo, event=None):
        if self.flag_thread == False:
            self.flag_thread = True

            if modo == "download":
                proc = threading.Thread(target=self.download_arquivo)
            elif modo == "upload":
                proc = threading.Thread(target=self.upload_arquivo)
            elif modo == "conectar":
                proc = threading.Thread(target=self.connect)
            proc.start()

    # ---Funções de terminal ---
    def print_terminal(self, msg):
        self.terminal['state'] = 'normal'
        self.terminal.insert('end', msg + '\n')
        # Auto scroll
        self.terminal.see('end')
        self.terminal['state'] = 'disabled'
    
    def clear_terminal(self):
        self.terminal['state'] = 'normal'
        self.terminal.delete(1.0, 'end')
        self.terminal['state'] = 'disabled'
    
    # --- Função para desabilitar funções no carregamento ---
    def estado_carregar(self, modo):
        if modo == True:
            self.master['cursor'] = 'wait'
            self.campo_path['state'] = 'disabled'
            self.list_local['state'] = 'disabled'
            self.list_remoto['state'] = 'disabled'
            self.list_local.unbind('<Double-Button-1>')
            self.list_remoto.unbind('<Double-Button-1>')
        else:
            self.master['cursor'] = ''
            self.campo_path['state'] = 'normal'
            self.list_local['state'] = 'normal'
            self.list_remoto['state'] = 'normal'
            self.list_local.bind('<Double-Button-1>', self.click_pasta_local)  
            self.list_remoto.bind('<Double-Button-1>', self.click_pasta_remote)           

    def start_GUI(self):
        self.master.mainloop()


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s')
    #logging.disable(logging.CRITICAL)

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
