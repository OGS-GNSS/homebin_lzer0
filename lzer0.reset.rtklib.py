#!/usr/bin/env python3
# Creato da Simone Galvi (Maggio 2024)
# programma che va a killare rtkrcv dal momento che lo trova bloccato
import socket
import time
import os
import subprocess
from datetime import datetime

host  = '127.0.0.1' # to be used for local connections
port  = 5754

def check_connection(host, port, timeout=10):
    try:
        # Crea un oggetto socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Imposta il timeout della connessione
        sock.settimeout(timeout)
        
        # Tenta di connettersi al servizio
        sock.connect((host, port))
        
        # Se la connessione ha successo, restituisce True
        return True
    
    except socket.error:
        # Se si verifica un errore, restituisce False
        return False
    
    finally:
        try:
		# Chiude il socket
            sock.close()
        except Exception as e: 
            print(f"Errore durante la chiusura del socket: {e}")
def monitor_connection(host, port):
    attempts = 0
    #resetCMD="ps -ef | grep /usr/local/bin/rtkrcv | awk '{print $2}' | xargs kill -9"
    resetCMD="ps -ef | grep rtkrcv | awk '{print $2}' | xargs kill -9"
    while True:
        if check_connection(host, port):
            print(f"Connessione a {host}:{port} stabilita")
            attempts = 0
        else:
            attempts += 1
            print(f"Impossibile connettersi a {host}:{port}")
            if attempts >= 3:
                print("Uccido il processo")
                subprocess.run(resetCMD, shell=True)
		
		# Ottieni la data e l'ora attuali
                now = datetime.now()
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                
                # Creare il file di log giornaliero
                today = datetime.now().strftime("%Y-%m-%d")
                log_file = f"/home/lzer0/log/{today}-resetrtklib.log"
                
                # Aggiungi una riga al file di log
                with open(log_file, "a") as file:
                    file.write(f"[ {timestamp} ] - Rtkrcv has crashed. Tried connection 5 times in a row without success. Restarting the process. \n")
                time.sleep(50)
                attempts = 0
        # Attendi 30 secondi prima di controllare di nuovo
        time.sleep(20)

monitor_connection(host, port)
