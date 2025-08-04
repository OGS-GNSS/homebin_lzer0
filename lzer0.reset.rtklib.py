#!/usr/bin/env python3
"""
Creato da Simone Galvi con miglioramenti (Aprile 2025)
Programma che monitora rtkrcv e lo riavvia quando necessario.
Ottimizzato per esecuzione come daemon via crontab @reboot.

Condizioni di riavvio:
1. Servizio non raggiungibile sulla porta
2. Status problematici:
   - "2": attende 5 minuti, se non torna a "1" riavvia
   - "5": se persiste per 3+ letture consecutive (3+ minuti) riavvia
   - Ambiguo/errore: 5 tentativi ogni 40s, poi riavvia
   - Altri valori: riavvia immediatamente
"""

import socket
import time
import os
import subprocess
import sys
import signal
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

# Configurazione
@dataclass
class Config:
    HOST: str = '127.0.0.1'
    PORT: int = 5754
    LOG_DIR: str = "/home/lzer0/log"
    PIDFILE: str = "/home/lzer0/log/lzer0.resetrtklib.pid"
    CHECK_INTERVAL: int = 60
    CONNECTION_RETRY_ATTEMPTS: int = 5
    STATUS_RETRY_INTERVAL: int = 40
    STATUS_RETRY_ATTEMPTS: int = 5
    STATUS_2_WAIT_TIME: int = 300  # 5 minuti
    STATUS_5_TIME_THRESHOLD: int = 180  # 3 minuti
    STATUS_5_COUNT_THRESHOLD: int = 3
    SOCKET_TIMEOUT: int = 10
    SOCAT_TIMEOUT: int = 10
    RESTART_WAIT_TIME: int = 60
    STARTUP_DELAY: int = 120  # Attesa iniziale per stabilizzazione sistema

config = Config()

class RTKMonitor:
    def __init__(self):
        self.connection_attempts = 0
        self.status5_count = 0
        self.status5_start = None
        self.shutdown_requested = False
        self._setup_daemon()
    
    def _setup_daemon(self) -> None:
        """Configura il processo come daemon."""
        self._ensure_log_dir()
        self._write_pidfile()
        self._setup_signal_handlers()
        
        # Redirect stdout/stderr al log per catturare tutti gli output
        log_file = f"{config.LOG_DIR}/lzer0.resetrtklib.log"
        sys.stdout = open(log_file, 'a', buffering=1)
        sys.stderr = sys.stdout
    
    def _write_pidfile(self) -> None:
        """Scrive il PID del processo corrente."""
        try:
            with open(config.PIDFILE, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            print(f"Errore scrittura pidfile: {e}")
    
    def _cleanup_pidfile(self) -> None:
        """Rimuove il pidfile."""
        try:
            if os.path.exists(config.PIDFILE):
                os.remove(config.PIDFILE)
        except Exception as e:
            self._log(f"Errore rimozione pidfile: {e}")
    
    def _setup_signal_handlers(self) -> None:
        """Configura i gestori dei segnali per shutdown pulito."""
        def signal_handler(signum, frame):
            self._log(f"Ricevuto segnale {signum}. Avvio shutdown...")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGHUP, signal_handler)
    
    def _ensure_log_dir(self) -> None:
        """Crea la directory di log se non esiste."""
        os.makedirs(config.LOG_DIR, exist_ok=True)
    
    def _check_connection(self) -> bool:
        """Verifica se il servizio è raggiungibile."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(config.SOCKET_TIMEOUT)
                sock.connect((config.HOST, config.PORT))
                return True
        except socket.error:
            return False
    
    def _get_rtk_status(self) -> str:
        """Ottiene lo stato RTK corrente."""
        try:
            cmd = f"echo 'solution' | socat tcp:{config.HOST}:{config.PORT} - | head -n 1"
            output = subprocess.check_output(
                cmd, shell=True, text=True, timeout=config.SOCAT_TIMEOUT
            )
            values = output.strip().split()
            return values[5] if len(values) >= 6 else "UNKNOWN"
        except Exception as e:
            self._log(f"Errore nell'ottenere lo status: {e}")
            return "ERROR"
    
    def _get_rtk_status_with_retry(self) -> str:
        """Ottiene lo status RTK con tentativi multipli per errori."""
        for attempt in range(config.STATUS_RETRY_ATTEMPTS):
            status = self._get_rtk_status()
            
            if status not in ["ERROR", "UNKNOWN"]:
                return status
            
            self._log(f"Status ambiguo ({status}) - tentativo {attempt + 1}/{config.STATUS_RETRY_ATTEMPTS}")
            if attempt < config.STATUS_RETRY_ATTEMPTS - 1:
                time.sleep(config.STATUS_RETRY_INTERVAL)
        
        self._log(f"Impossibile ottenere status valido dopo {config.STATUS_RETRY_ATTEMPTS} tentativi")
        return "FAILED"
    
    def _restart_rtkrcv(self) -> bool:
        """Uccide e riavvia il processo rtkrcv."""
        try:
            self._log("Riavvio rtkrcv in corso...")
            
            # Uccidi tutti i processi rtkrcv più robustamente
            kill_commands = [
                "pkill -f rtkrcv",
                "ps -ef | grep '[r]tkrcv' | awk '{print $2}' | xargs -r kill -9"
            ]
            
            for cmd in kill_commands:
                try:
                    subprocess.run(cmd, shell=True, check=False, timeout=30)
                    time.sleep(2)
                except subprocess.TimeoutExpired:
                    self._log("Timeout durante kill del processo")
            
            time.sleep(config.RESTART_WAIT_TIME)
            self._reset_status5_tracking()
            return True
        except Exception as e:
            self._log(f"Errore durante il riavvio di rtkrcv: {e}")
            return False
    
    def _reset_status5_tracking(self) -> None:
        """Resetta il tracking dello status 5."""
        self.status5_count = 0
        self.status5_start = None
    
    def _handle_status5(self) -> bool:
        """Gestisce lo status 5. Restituisce True se il processo deve essere riavviato."""
        if self.status5_count == 0:
            self.status5_start = time.time()
        
        self.status5_count += 1
        elapsed = time.time() - (self.status5_start or 0)
        
        if elapsed >= config.STATUS_5_TIME_THRESHOLD and self.status5_count >= config.STATUS_5_COUNT_THRESHOLD:
            self._log("Status '5' persistente per oltre 3 minuti. Riavvio necessario.")
            return True
        
        return False
    
    def _handle_status2(self) -> bool:
        """Gestisce lo status 2. Restituisce True se il processo deve essere riavviato."""
        self._log(f"Status 2: attendo {config.STATUS_2_WAIT_TIME//60} minuti per verifica...")
        time.sleep(config.STATUS_2_WAIT_TIME)
        
        new_status = self._get_rtk_status()
        self._log(f"Status dopo attesa: {new_status}")
        
        if new_status != "1":
            self._log("Status non tornato a 1. Riavvio necessario.")
            return True
        
        return False
    
    def _process_status(self, status: str) -> bool:
        """Processa lo status e determina se è necessario un riavvio."""
        if status == "FAILED":
            self._log("Status fallito dopo tutti i tentativi. Riavvio necessario.")
            return True
        
        self._log(f"Status rtkrcv: {status}")
        
        if status == "1":
            self._reset_status5_tracking()
            return False
        elif status == "2":
            restart_needed = self._handle_status2()
            self._reset_status5_tracking()
            return restart_needed
        elif status == "5":
            return self._handle_status5()
        else:
            self._log(f"Status non riconosciuto ({status}). Riavvio necessario.")
            return True
    
    def _handle_connection_failure(self) -> bool:
        """Gestisce i fallimenti di connessione. Restituisce True se è necessario un riavvio."""
        self.connection_attempts += 1
        self._log(f"Connessione fallita ({self.connection_attempts}/{config.CONNECTION_RETRY_ATTEMPTS})")
        
        if self.connection_attempts >= config.CONNECTION_RETRY_ATTEMPTS:
            self._log("Troppi fallimenti di connessione consecutivi. Riavvio necessario.")
            self.connection_attempts = 0
            return True
        
        return False
    
    def _log(self, message: str) -> None:
        """Registra un evento nel log con flush immediato."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[ {timestamp} ] [PID:{os.getpid()}] - {message}\n"
        
        try:
            log_file = f"{config.LOG_DIR}/lzer0.resetrtklib.log"
            with open(log_file, "a") as f:
                f.write(log_entry)
                f.flush()  # Forza la scrittura immediata
            
            # Output anche su stdout per crontab
            print(log_entry.strip())
            sys.stdout.flush()
        except Exception as e:
            # Fallback su stderr se il log file non è accessibile
            print(f"ERRORE LOG: {e} - {log_entry.strip()}", file=sys.stderr)
    
    def monitor(self) -> None:
        """Funzione principale di monitoraggio."""
        self._log("Monitoraggio rtkrcv avviato")
        self._log(f"Attesa iniziale di {config.STARTUP_DELAY} secondi per stabilizzazione sistema...")
        time.sleep(config.STARTUP_DELAY)
        
        while not self.shutdown_requested:
            try:
                if self._check_connection():
                    self.connection_attempts = 0
                    status = self._get_rtk_status_with_retry()
                    
                    if self._process_status(status):
                        self._restart_rtkrcv()
                else:
                    if self._handle_connection_failure():
                        self._restart_rtkrcv()
                
                # Check periodico per shutdown durante il sleep
                for _ in range(config.CHECK_INTERVAL):
                    if self.shutdown_requested:
                        break
                    time.sleep(1)
                
            except Exception as e:
                self._log(f"Errore imprevisto: {e}")
                # Attesa breve prima di riprovare
                for _ in range(min(config.CHECK_INTERVAL, 30)):
                    if self.shutdown_requested:
                        break
                    time.sleep(1)
        
        self._log("Shutdown del monitoraggio completato")
        self._cleanup_pidfile()

def main():
    """Punto di ingresso principale per daemon."""
    # Verifica se un'altra istanza è già in esecuzione
    if os.path.exists(config.PIDFILE):
        try:
            with open(config.PIDFILE, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Controlla se il processo è ancora attivo
            try:
                os.kill(old_pid, 0)  # Signal 0 solo per verificare esistenza
                print(f"ERRORE: Un'altra istanza è già in esecuzione (PID: {old_pid})")
                sys.exit(1)
            except OSError:
                # Il processo non esiste più, rimuovi il pidfile stale
                os.remove(config.PIDFILE)
                print("Rimosso pidfile obsoleto")
        except (ValueError, FileNotFoundError):
            # Pidfile corrotto o non trovato, procedi
            pass
    
    monitor = RTKMonitor()
    try:
        monitor.monitor()
    except Exception as e:
        monitor._log(f"Errore fatale: {e}")
        sys.exit(1)
    finally:
        monitor._cleanup_pidfile()

if __name__ == "__main__":
    main()
