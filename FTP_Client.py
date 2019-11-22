# coding: UTF-8
#! python3

"""
Criado 15 de novembro

Servidor FTP para Windows para se conectar ao RPi
"""

import socket
import subprocess
import json
import os
import base64
import sys
import shutil

class FTPClient:
    def __init__(self):
        # Variaveis gerais
        self.tamanho_pacote = 8192
        self.total_recebido = 0
    # --- Funções de conexão e envio para o remoto ---
    def init_conn(self, ip, port):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.conn.connect((ip, port))
            return "[+] Conexão estabelecida!"
        except ConnectionRefusedError:
            return "[-] Conexão recusada pela máquina de destino (Refused)"
        except TimeoutError:
            return "[-] Endereço não encontrado (Timeout)"
        except socket.gaierror:
            return "[-] Endereço de IP inválido"

    def enviar_comando(self, comando):
        comando = FTPClient.split_command(comando)
        self.enviar_pacote_json(comando)
        if 'exit' in comando:
            self.conn.close()
            return "[-] Conexão encerrada\n"

        return self.receber_pacote_json()
    
    # --- Funções de tratamento de JSON ---
    def enviar_pacote_json(self, pack):
        pack_json = json.dumps(pack)
        self.conn.send(pack_json.encode()) 

    def receber_pacote_json(self):
        pack_json = b''
        while True:
            try:
                pack_json += self.conn.recv(self.tamanho_pacote)
                return json.loads(pack_json)   # Recebe bytes, retorna str (apenas em 3.6+)
            except ValueError:
                self.total_recebido = len(pack_json)/1000
                # O base64encode adiciona 33% no arquivo. Para normalizar, retirar 25% do tamanho total
                print("\rRecebido: %d Kb" % self.total_recebido, end="")
    
    # --- Funções de arquivos locais ---
    def change_client_directory(self, path):
        if os.path.isdir(path):
            os.chdir(path)
            return "[+] Diretorio mudado para %s" % os.getcwd()
        else:
            return "[-] Diretorio '%s' invalido" % path
    
    def list_client_directory(self, path="."):
        (_, dirs, arqs) = next(os.walk(path))
        return dirs, arqs
            
    # --- Função de tratamento de comando ---
    @staticmethod
    def split_command(comando):
        # Split especial para que 'cd Meus Documentos' funcione
        try:
            comando = comando.split(' ')
            if len(comando) > 2:
                path = ' '.join(comando[1:])
                comando = [comando[0], path]
        except AttributeError:
            # Já é uma lista
            pass
    
        return comando
    
    # --- Funções de escrita e leitura ---
    @staticmethod
    def read_file(path):
        if os.path.isfile(path):
            with open(path, 'rb') as arq:
                data = base64.b64encode(arq.read())
                return data.decode()
        return "[-] Arquivo '%s' nao encontrado" % path

    @staticmethod
    def save_file(data, path):
        with open(path, 'wb') as arq:
            arq.write(base64.b64decode(data))
        return "[+] Download finalizado"

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s')
    logging.disable(logging.CRITICAL)
  
