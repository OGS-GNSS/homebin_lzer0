
---

## Introduzione

Il progetto **lzer0** è una soluzione integrata per la gestione e l’elaborazione in tempo reale dei dati GNSS. Esso sfrutta una serie di script che vengono eseguiti tramite il crontab per automatizzare attività come:

- **Monitoraggio delle risorse:** Controllo della temperatura e dell’utilizzo della CPU.
- **Gestione dei dati U-Blox:** Reindirizzamento dello stream in tempo reale su porte TCP.
- **Verifica e gestione della connessione RTK:** Controllo della connessione RTK e reset in caso di necessità.
- **Sincronizzazione data/ora:** Configurazione della data e dell’ora basata su messaggi NMEA.
- **Gestione dello storage:** Montaggio e verifica di dischi USB esterni, controllo dello spazio libero.
- **Elaborazione dei dati GNSS:** Compressione periodica dei dataset GNSS e registrazione in tempo reale delle posizioni.

Tutti questi script necessitano di **RTKLIB** per il loro corretto funzionamento, in quanto questa libreria open-source permette la post-elaborazione e il calcolo in tempo reale delle soluzioni GNSS, garantendo la precisione necessaria per le applicazioni di posizionamento.

---

## Struttura dei Crontab

Il funzionamento del sistema è gestito da due crontab distinti: uno per l’utente **lzer0** e uno per **root**.

### Crontab Utente

Il crontab dell’utente **lzer0** contiene le seguenti configurazioni:

```
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
 
PATH=/home/lzer0/bin:/usr/local/bin:/usr/bin:/bin
 
### Check on temp and cpu usage
* * * * * /home/lzer0/bin/lzer0.log.temp >/dev/null 2>&1
 
### U-blox real-time stream to TCP ports redirections
@reboot sleep 30; /home/lzer0/bin/lzer0.ser2tcp.ubx >/dev/null 2>&1
 
### Check rtk connection
@reboot sleep 60; nohup python3 /home/lzer0/bin/lzer0.reset.rtklib.py >&1
 
### Set up date and time management (it uses also NMEA message from TCP ports redirected from U-BLOX device)
* * * * * /home/lzer0/bin/lzer0.get.datetime >/dev/null 2>&1
#@reboot sleep 60; /home/lzer0/bin/lzer0.set.datetime >/dev/null 2>&1
 
### External USB disk management
@reboot sleep 80; /home/lzer0/bin/lzer0.mount.storage >/dev/null 2>&1
@reboot sleep 100; /home/lzer0/bin/lzer0.check.storage >/dev/null 2>&1
### Check empty space on disk every minute
1 * * * * /home/lzer0/bin/lzer0.check.storage >/dev/null 2>&1
 
### Redirections to files (it must start at reboot and later on lzer0.mount.storage and lzer0.check.storage)
@reboot sleep 120; /home/lzer0/bin/lzer0.tcp2file.ubx -f /home/lzer0/cfg/sites.cfg >/dev/null 2>&1
*/10 * * * * /home/lzer0/bin/lzer0.manage.serialport check
 
### GNSS data set management
0 * * * * sleep 5; /home/lzer0/bin/lzer0.compress.hourlygnss -f /home/lzer0/cfg/sites.cfg >/dev/null 2>&1
30 */6 * * * /home/lzer0/bin/lzer0.compress.hourlygnss -f /home/lzer0/cfg/sites.cfg -p 96 >/dev/null 2>&1
 
### GNSS real time processing (it must start at reboot and later on lzer0.ser2tcp.ubx and lzer0.tcp2file.ubx)
@reboot sleep 45; /home/lzer0/bin/lzer0.start.rtk -f /home/lzer0/cfg/rtkrcv.curr.conf >/dev/null 2>&1
* * * * * /home/lzer0/bin/lzer0.check.rtk -f /home/lzer0/cfg/rtkrcv.curr.conf >/dev/null 2>&1
 
### GNSS real time processing pos recording (it must start at reboot and later on lzer0.start.rtkrcv)
@reboot sleep 50; /home/lzer0/bin/lzer0.record.hourlypos -f /home/lzer0/cfg/sites.cfg >/dev/null 2>&1
@reboot sleep 55; /home/lzer0/bin/lzer0.check.recordhourlypos -f /home/lzer0/cfg/sites.cfg >/dev/null 2>&1 
1 * * * * /home/lzer0/bin/lzer0.check.recordhourlypos -f /home/lzer0/cfg/sites.cfg >/dev/null 2>&1
```

### Crontab Root

Il crontab di **root** contiene invece le seguenti configurazioni:

```
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

I vari script, gestiti tramite i crontab, costituiscono il cuore del sistema **lzer0**. Ecco una sintesi del loro ruolo:

- **Crontab Utente (lzer0):**  
  Pianifica e gestisce le operazioni quotidiane e periodiche legate alla gestione dei dati GNSS, alla sincronizzazione dell'orario, al controllo delle risorse e alla gestione dello storage USB.
  
- **Crontab Root:**  
  Si occupa principalmente della connettività, avviando il modulo di rete 4G e monitorando costantemente lo stato della rete per garantire la stabilità della comunicazione.

Ogni script è strettamente integrato nel flusso di lavoro del progetto, garantendo un’automazione continua e affidabile. La necessità di **RTKLIB** è centrale per la corretta elaborazione dei dati GNSS, fornendo le correzioni in tempo reale necessarie per ottenere posizioni precise.

---

## Conclusioni

Questa guida fornisce una panoramica del progetto **lzer0** e riproduce esattamente i crontab dell’utente e di root, così da facilitare la replica e l’implementazione del sistema.  
Utilizzando questi file di configurazione, il sistema assicura il monitoraggio costante delle risorse, la gestione dei flussi dati GNSS e la stabilità della connettività, offrendo una soluzione robusta per applicazioni di posizionamento e monitoraggio in tempo reale.

Puoi utilizzare i crontab sopra riportati copiandoli direttamente nei rispettivi file per configurare il sistema in modo identico.
