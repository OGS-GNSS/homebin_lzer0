#!/usr/bin/env python3
"""
Creato da Simone Galvi con miglioramenti (Aprile 2025)
Programma che monitora rtkrcv e lo riavvia quando:
1. è bloccato (non risponde sulla porta)
2. Non è in stato "1" (rtk fix OK) oppure in casi di status problematici:
   - se lo status è "2": attende 5 minuti e, se dopo 5 minuti non torna a "1", uccide il processo
   - se lo status è "5": se appare per 3 letture consecutive (circa 3 minuti) uccide il processo
   - se lo status è ambiguo (diverso da "1", "2" o "5"): uccide il processo
"""

import socket
import time
import os
import subprocess
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5754
LOG_DIR = "/home/lzer0/log"
CHECK_INTERVAL = 40    # Intervallo tra i controlli (in secondi)
RETRY_ATTEMPTS = 3       # Numero di tentativi di connessione prima di agire

def check_connection(host, port, timeout=10):
    """Verifica se il servizio è raggiungibile sulla porta specificata."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        return True
    except socket.error:
        return False
    finally:
        try:
            sock.close()
        except Exception as e:
            print(f"Errore durante la chiusura del socket: {e}")

def get_rtk_status():
    """Ottiene lo stato di rtkrcv eseguendo il comando socat e restituisce il sesto valore."""
    try:
        # Invia il comando "solution" e ottiene la prima riga della risposta
        cmd = f"echo 'solution' | socat tcp:{HOST}:{PORT} - | head -n 1"
        output = subprocess.check_output(cmd, shell=True, text=True, timeout=10)
        values = output.strip().split()
        if len(values) >= 6:
            status = values[5]
            return status
        return "UNKNOWN"
    except Exception as e:
        print(f"Errore durante l'ottenimento dello status: {e}")
        return "ERROR"

def restart_rtkrcv():
    """Uccide e riavvia il processo rtkrcv."""
    try:
        # Uccide il processo rtkrcv
        kill_cmd = "ps -ef | grep rtkrcv | awk '{print $2}' | xargs kill -9"
        subprocess.run(kill_cmd, shell=True)
        
        # Attende un paio di secondi per la chiusura
        time.sleep(2)
        
        # Inserisci qui il comando per riavviare rtkrcv, ad es.:
        # start_cmd = "cd /path/to/rtkrcv && /usr/local/bin/rtkrcv -s -o /path/to/config.conf"
        # subprocess.run(start_cmd, shell=True)
        
        # Attende l'avvio del servizio
        time.sleep(5)
        
        return True
    except Exception as e:
        print(f"Errore durante il riavvio di rtkrcv: {e}")
        return False

def log_event(message):
    """Registra un evento nel log giornaliero."""
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    today = now.strftime("%Y-%m-%d")
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = f"{LOG_DIR}/{today}-resetrtklib.log"
    with open(log_file, "a") as file:
        file.write(f"[ {timestamp} ] - {message}\n")
    print(f"[ {timestamp} ] - {message}")

def monitor_rtkrcv():
    """Funzione principale di monitoraggio di rtkrcv."""
    connection_attempts = 0
    status5_count = 0     # Conta quante volte consecutive lo status è "5"
    status5_start = None  # Memorizza il tempo del primo status "5" della sequenza
    
    print(f"Monitoraggio di rtkrcv su {HOST}:{PORT} avviato...")
    log_event("Monitoraggio rtkrcv avviato")
    
    while True:
        if check_connection(HOST, PORT):
            connection_attempts = 0
            
            status = get_rtk_status()
            if status in ["ERROR", "UNKNOWN"]:
                log_event("Status ambiguo o errore nell'ottenere lo status. Riavvio rtkrcv...")
                restart_rtkrcv()
                # Resetta il contatore status5 se presente
                status5_count = 0
                status5_start = None
            else:
                log_event(f"Status rtkrcv: {status}")
                if status == "1":
                    # Stato OK: resettare qualsiasi contatore
                    status5_count = 0
                    status5_start = None
                elif status == "2":
                    log_event("Status è 2: attendo 5 minuti per verificare la ripresa a '1'...")
                    time.sleep(300)  # Attende 5 minuti
                    new_status = get_rtk_status()
                    log_event(f"Dopo 5 minuti il nuovo status è: {new_status}")
                    if new_status != "1":
                        log_event("Status non è tornato a 1. Riavvio rtkrcv...")
                        restart_rtkrcv()
                    # Resetta i contatori altrimenti
                    status5_count = 0
                    status5_start = None
                elif status == "5":
                    # Se lo status è "5", gestiamo il conteggio e la finestra temporale di 3 minuti
                    if status5_count == 0:
                        status5_start = time.time()
                    status5_count += 1
                    elapsed = time.time() - status5_start if status5_start else 0
                    if elapsed >= 180 and status5_count >= 3:
                        log_event("Status '5' per più di 3 minuti (più di 3 letture consecutive). Riavvio rtkrcv...")
                        restart_rtkrcv()
                        status5_count = 0
                        status5_start = None
                else:
                    # Se lo status non è "1", "2" o "5", consideriamo la situazione ambigua
                    log_event(f"Status ambiguo ({status}). Riavvio rtkrcv...")
                    restart_rtkrcv()
                    status5_count = 0
                    status5_start = None
                    
        else:
            connection_attempts += 1
            log_event(f"Impossibile connettersi a {HOST}:{PORT} (tentativo {connection_attempts}/{RETRY_ATTEMPTS})")
            if connection_attempts >= RETRY_ATTEMPTS:
                log_event(f"Impossibile connettersi per {RETRY_ATTEMPTS} tentativi consecutivi. Riavvio rtkrcv...")
                restart_rtkrcv()
                connection_attempts = 0
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        monitor_rtkrcv()
    except KeyboardInterrupt:
        log_event("Monitoraggio interrotto dall'utente")
        print("\nMonitoraggio interrotto. Uscita...")
    except Exception as e:
        log_event(f"Errore imprevisto: {e}")
        print(f"Errore imprevisto: {e}")

