# coding: UTF-8
"""
Criado: 15 de novembro

Servidor FTP. Facilita a troca de arquivos e de informações entre o RPi e a máquina cliente.
Feito para rodar no RPi. N
Recebe as informações e arquivos na porta 4444 (ou na porta 21?)

FEITO: Adicionar Persistência. Quando uma conexão for encerrada, já começa o Listen para outra
FEITO: Detectar o IP do RPi e colocar no main
TODO: Ajustar a velocidade de transferência - mudar recv
TODO: Criar interface gráfica. Preferência de com o código em outro arquivo
FEITO: (Difícil) Mostrar o progresso da transferência

NOTAS:
**Quais funções devem estar em ambos:
    - Upload & Download
    - Mudar diretorio
    - Enviar e receber pacotes JSON
**Quais funções devem estar apenas na máquina Windows:
    - Separar comando?
**Quais funções devem estar apenas no RPi:
    - Executar comando (subprocess) 

BUGS:
    Se o arquivo em upload possuir espaço, buga o programa - CORRIGIDO
    Velocidade de transferência de upload menor que de download

"""
#! /usr/bin/python3

import socket
import json
import os
import base64
import subprocess
import sys


class FTPListener:
    def __init__(self, ip, port):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Muda as configurações do socket para habilitar o reuso de endereços
        # (Caso a conexão caia, reconecta no mesmo endereço)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Seta em 1 o reuse q está no level sol_socket
        listener.bind((ip, port))
        # Limite de conexões/tempo. Com 0 = infinito
        listener.listen(0)
        
        print("\n[+] Aguardando uma conexão")
        self.conn, ip_addr = listener.accept()
        print("[+] Conexão feita com", ip_addr)
        
        self.tamanho_pacote = 8192

    def enviar_pacote_json(self, pacote):
        pack_json = json.dumps(pacote)
        self.conn.send(pack_json.encode())
        
    def receber_pacote_json(self):
        pack_json = b''
        while True:
            try:
                pack_json += self.conn.recv(self.tamanho_pacote)
                return json.loads(pack_json)    # Recebe bytes, transforma para string
            except ValueError:
                # Caso não tenha chegado ao fim do JSON, um ValueError é dado na conversão
                print("\rRecebido: %d Kb" % (len(pack_json)/1000), end="")
        

    def change_directory(self, path):
        if os.path.isdir(path):
            os.chdir(path)
            return "[+] Diretorio mudado para %s" % os.getcwd()
        return "[-] Diretorio '%s' invalido" % path

    def start(self):
        while True:
            # Recebe em pacotes de 1MB
            comando = self.receber_pacote_json()
            try:
                if 'exit' in comando:
                    self.conn.close()
                    break
                elif 'cd' in comando[0] and len(comando) > 1:
                    # Comando 'cd DIRECTORY'
                    resposta = self.change_directory(comando[1])
                elif 'download' in comando[0]:
                    # Comando: download ARQ.ext
                    resposta = FTPListener.read_file(comando[1])
                elif 'upload' in comando[0]:
                    # Comando upload ARQ.ext DATA
                    resposta = FTPListener.save_file(comando[2], comando[1])
                    print("\rRecebido: %d Kb" % (len(comando[2])/1000))
                elif 'remove' in comando[0]:
                    # Comando: remove ARQ.ext
                    resposta = FTPListener.remove_file(comando[1])
                elif comando[0] in ['more', 'cat'] and len(comando) == 1:
                    #Evitar bug de travar o programa
                    resposta = "[-] Comando 'more' necessita de mais um argumento"
                else:
                    # Comando simples como dir, ipconfig...
                    resposta = FTPListener.executar_subprocess(comando)
            except TypeError:
                resposta = '[-] Erro na execucao do comando'
            
            self.enviar_pacote_json(resposta)
            

    @staticmethod
    def split_command(comando):
        # Split especial para que 'cd Meus Documentos' funcione
        comando = comando.split(' ')
        if len(comando) > 2:
            path = ' '.join(comando[1:])
            comando = [comando[0], path]
        return comando
    
    @staticmethod
    def executar_subprocess(comando):
        try:
            resposta = subprocess.run(comando, capture_output=True).stdout
            return resposta.decode()   #Codificação descoberta com 'chcp' no CMD
        except subprocess.CalledProcessError:
            return "[-] Comando '%s' invalido (CalledProcessError)" % ' '.join(comando)
        except FileNotFoundError:
            return "[-] Comando '%s' retornou FileNotFound" % ' '.join(comando)

    @staticmethod
    def save_file(data, path):
        nome_arq = os.path.basename(path)
        logging.debug(type(data))
        with open(nome_arq, 'wb') as arq:
            arq.write(base64.b64decode(data))
        return '[+] Upload Finalizado'

    @staticmethod
    def read_file(path):
        with open(path, 'rb') as arq:
            data = base64.b64encode(arq.read())
            return data.decode()
    
    @staticmethod
    def remove_file(path):
        if os.path.isfile(path):
            os.remove(path)
            return "Arquivo %s removido com sucesso" % path
        return 'Arquivo "%s" inválido. Operação cancelada' % path
    

def discover_ip():
    import re
    if sys.platform == "linux":
        ip = subprocess.run('ifconfig', capture_output=True, text=True).stdout
        ip = re.findall('(?:inet\s)(\S+)', ip)
    
    elif sys.platform == "win32":
        ip = subprocess.run('ipconfig', shell=True, capture_output=True, text=True).stdout
        ip = re.findall(r'(?:IPv4.*:\s)(\S+)', ip)
    
    # Remove a interface não usada
    if len(ip) > 1 and '127.0.0.1' in ip:
        ip.remove('127.0.0.1')
    
    return ip[0]


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s')
    logging.disable(logging.CRITICAL)
    
    ip = discover_ip()
    print("[+] IP atual: %s" % ip)
    
    while True:
        try:
            server = FTPListener(ip, 4444)
            server.start()
            print('[-] Conexão encerrada pelo usuário\n')
        except KeyboardInterrupt:
            print("[---] Finalizado!")
            sys.exit()
        except ConnectionResetError:
            print('[-] Conexão com o cliente perdida')
            continue

        
