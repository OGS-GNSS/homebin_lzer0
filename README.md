# LZER0 Bin

**lzer0** è una soluzione integrata per la gestione ed elaborazione in tempo reale dei dati GNSS. Il progetto sfrutta una serie di script eseguiti tramite crontab per automatizzare diverse attività fondamentali, garantendo una gestione completa e affidabile del sistema.

---

## Introduzione

Il progetto **lzer0** permette di:

- **Monitoraggio delle risorse:**  
  Controlla temperatura e utilizzo della CPU.
  
- **Gestione dei dati U-Blox:**  
  Reindirizza lo stream in tempo reale su porte TCP.
  
- **Verifica e gestione della connessione RTK:**  
  Monitora la connessione RTK e, se necessario, esegue il reset.
  
- **Sincronizzazione data/ora:**  
  Imposta la data e l’ora basandosi sui messaggi NMEA.
  
- **Gestione dello storage:**  
  Monta e verifica dischi USB esterni, controllando lo spazio libero.
  
- **Elaborazione dei dati GNSS:**  
  Comprimi periodicamente i dataset GNSS e registra in tempo reale le posizioni.

> **Nota:** Tutti gli script richiedono **RTKLIB** per il corretto funzionamento, poiché questa libreria open-source consente la post-elaborazione e il calcolo in tempo reale delle soluzioni GNSS, garantendo la precisione necessaria per le applicazioni di posizionamento.

---

## Guida all'Uso

Gli script sono progettati per funzionare su tutti i modelli interni di **lzer0**:
- **Dispositivi con HAT 4G**
- **Dispositivi con modulo PiJuice**

La cartella `bin` deve essere posizionata nella home dell’utente (ad esempio `/home/lzer0/bin`).

---

## Struttura dei Crontab

Il funzionamento del sistema si basa su due crontab distinti: uno per l’utente **lzer0** e uno per **root**.

### Crontab Utente (lzer0)

Il crontab dell’utente **lzer0** contiene le seguenti configurazioni:

```bash
#
# Each task to run has to be defined through a single line
# indicating with different fields when the task will be run
# and what command to run for the task
#
# To define the time you can provide concrete values for
# minute (m), hour (h), day of month (dom), month (mon),
# and day of week (dow) or use '*' in these fields (for 'any').
#
# Notice that tasks will be started based on the cron's system
# daemon's notion of time and timezones.
#
# Output of the crontab jobs (including errors) is sent through
# email to the user the crontab file belongs to (unless redirected).
#
#  _                     _____ 
# | |                   / __  \
# | |    ____  ___ _ __| | / / |
# | |   |_  / / _ \ '__| |/ /| |
# | |___ / / |  __/ |  | ' /_| |
# |_____/___| \___|_|   \_____/
#
# * * * * *
# - - - - -
# | | | | |
# | | | | +----- day of week (0-6) (Sunday=0)
# | | | +------- month (1 - 12)
# | | +-------- day of month (1 - 31)
# | +--------- hour (0 - 23)
# +---------- min (0 - 59)
#
# Impostazioni generali per il PATH
PATH=/home/lzer0/bin:/usr/local/bin:/usr/bin:/bin

### Monitoraggio della temperatura e utilizzo CPU
* * * * * /home/lzer0/bin/lzer0.log.temp >/dev/null 2>&1

### Reindirizzamento stream U-Blox su porte TCP (avvio al reboot)
@reboot sleep 30; /home/lzer0/bin/lzer0.ser2tcp.ubx >/dev/null 2>&1

### Controllo e reset della connessione RTK (avvio al reboot)
@reboot sleep 60; nohup python3 /home/lzer0/bin/lzer0.reset.rtklib.py >&1

### Gestione data/ora (utilizza messaggi NMEA da porte TCP U-Blox)
* * * * * /home/lzer0/bin/lzer0.get.datetime >/dev/null 2>&1
#@reboot sleep 60; /home/lzer0/bin/lzer0.set.datetime >/dev/null 2>&1

### Gestione storage USB
@reboot sleep 80; /home/lzer0/bin/lzer0.mount.storage >/dev/null 2>&1
@reboot sleep 100; /home/lzer0/bin/lzer0.check.storage >/dev/null 2>&1
### Verifica spazio libero ogni ora
1 * * * * /home/lzer0/bin/lzer0.check.storage >/dev/null 2>&1

### Reindirizzamento dei dati su file (avvio al reboot)
@reboot sleep 120; /home/lzer0/bin/lzer0.tcp2file.ubx -f /home/lzer0/cfg/sites.cfg >/dev/null 2>&1

### Gestione porta seriale
*/10 * * * * /home/lzer0/bin/lzer0.manage.serialport check

### Gestione dei dataset GNSS
0 * * * * sleep 5; /home/lzer0/bin/lzer0.compress.hourlygnss -f /home/lzer0/cfg/sites.cfg >/dev/null 2>&1
30 */6 * * * /home/lzer0/bin/lzer0.compress.hourlygnss -f /home/lzer0/cfg/sites.cfg -p 96 >/dev/null 2>&1

### Elaborazione in tempo reale dei dati GNSS
@reboot sleep 45; /home/lzer0/bin/lzer0.start.rtk -f /home/lzer0/cfg/rtkrcv.curr.conf >/dev/null 2>&1
* * * * * /home/lzer0/bin/lzer0.check.rtk -f /home/lzer0/cfg/rtkrcv.curr.conf >/dev/null 2>&1

### Registrazione in tempo reale delle posizioni GNSS
@reboot sleep 50; /home/lzer0/bin/lzer0.record.hourlypos -f /home/lzer0/cfg/sites.cfg >/dev/null 2>&1
@reboot sleep 55; /home/lzer0/bin/lzer0.check.recordhourlypos -f /home/lzer0/cfg/sites.cfg >/dev/null 2>&1 
1 * * * * /home/lzer0/bin/lzer0.check.recordhourlypos -f /home/lzer0/cfg/sites.cfg >/dev/null 2>&1
```

### Crontab Root

Il crontab di **root** è configurato per garantire la connettività e il monitoraggio della rete:

```bash
#
# Each task to run has to be defined through a single line
# indicating with different fields when the task will be run
# and what command to run for the task
#
# To define the time you can provide concrete values for
# minute (m), hour (h), day of month (dom), month (mon),
# and day of week (dow) or use '*' in these fields (for 'any').
#
# Notice that tasks will be started based on the cron's system
# daemon's notion of time and timezones.
#
# Output of the crontab jobs (including errors) is sent through
# email to the user the crontab file belongs to (unless redirected).
#
#  _                     _____ 
# | |                   / __  \
# | |    ____  ___ _ __| | / / |
# | |   |_  / / _ \ '__| |/ /| |
# | |___ / / |  __/ |  | ' /_| |
# |_____/___| \___|_|   \_____/
#
# * * * * *
# - - - - -
# | | | | |
# | | | | +----- day of week (0-6) (Sunday=0)
# | | | +------- month (1 - 12)
# | | +-------- day of month (1 - 31)
# | +--------- hour (0 - 23)
# +---------- min (0 - 59)
#
@reboot /home/lzer0/bin/lzer0.start.4GNet >/dev/null 2>&1
@reboot /home/lzer0/bin/network.watchdog >/dev/null 2>&1
```

---

## Funzionamento Complessivo

Il sistema **lzer0** si basa su una rigorosa automazione tramite i crontab, che consentono di:

- **Gestire operazioni quotidiane e periodiche:**  
  Monitoraggio delle risorse, gestione dello storage, sincronizzazione oraria e reindirizzamento dei dati.
  
- **Garantire la stabilità della comunicazione:**  
  Tramite il monitoraggio della connettività 4G e l'attivazione del watchdog di rete.
  
- **Assicurare la precisione dei dati GNSS:**  
  Utilizzando **RTKLIB** per il calcolo e la post-elaborazione in tempo reale.

---

## Conclusioni

Questa guida fornisce una panoramica completa del progetto **lzer0** e include i file di configurazione dei crontab per l’utente **lzer0** e **root**.  
Per configurare il sistema in modo identico, copia i contenuti riportati nei rispettivi file di crontab.

Il sistema offre una soluzione robusta per il monitoraggio in tempo reale e il posizionamento, ideale per applicazioni avanzate basate su dati GNSS.
