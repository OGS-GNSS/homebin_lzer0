# Implementation proposal: centralized repository configuration

Questo file descrive le variabili raggruppate nel file di configurazione testuale comune `lzer0.env`.

## File proposto

Nome proposto: `lzer0.env`

Formato proposto: sintassi shell `KEY=value`, caricabile dagli script Bash con `source`.

Gli script Bash caricano la configurazione tramite `lzer0.config.sh`; gli script Python tramite `lzer0_config.py`. Il percorso di default e `${HOME}/cfg/lzer0.env`; in alternativa si puo impostare `LZERO_ENV_FILE` o lasciare un `lzer0.env` accanto agli script.

Esempio:

```bash
LZERO_HOME=/home/lzer0
LZERO_BIN_DIR=${LZERO_HOME}/bin
LZERO_CONFIG_DIR=${LZERO_HOME}/cfg
LZERO_LOG_DIR=${LZERO_HOME}/log
LZERO_VAR_DIR=${LZERO_HOME}/var
LZERO_TMP_DIR=${LZERO_HOME}/tmp/tmp.lzer0
LZERO_STORAGE_MOUNT=/mnt/hd
LZERO_GNSS_DIR=${LZERO_STORAGE_MOUNT}/gnss
```

## Variabili richieste

`LZERO_STORAGE_MOUNT`
: Mountpoint della memoria USB o disco esterno. Valore attuale ricorrente: `/mnt/hd`.

`LZERO_LOG_DIR`
: Directory dei log. Valori attuali ricorrenti: `/home/lzer0/log`, `$HOME/log`, `/home/${USER}/log`.

`LZERO_CONFIG_DIR`
: Directory delle configurazioni. Valore attuale ricorrente: `/home/lzer0/cfg` o `$HOME/cfg`.

## Variabili che propongo di aggiungere

`LZERO_HOME`
: Home dell'utente operativo. Utile per eliminare i misti `/home/lzer0`, `$HOME` e `/home/${USER}`.

`LZERO_BIN_DIR`
: Directory degli script eseguibili. Valori attuali: `/home/lzer0/bin`, `$HOME/bin`.

`LZERO_VAR_DIR`
: Directory per stato runtime semplice, per esempio `provider.config`. Valore attuale: `/home/lzer0/var`.

`LZERO_TMP_DIR`
: Directory temporanea condivisa per elaborazioni GNSS. Valori attuali: `$HOME/tmp/tmp.lzer0`, `$HOME/tmp.<script>`.

`LZERO_GNSS_DIR`
: Directory dati GNSS derivata dal mountpoint. Valore attuale: `/mnt/hd/gnss`.

`LZERO_SITE_CONFIG`
: File siti. Valori attuali: `$HOME/cfg/sites.cfg`, `/home/lzer0/cfg/sites.cfg`.

`LZERO_RTKRCV_CONFIG`
: File configurazione RTKRCV corrente. Valore attuale: `/home/lzer0/cfg/rtkrcv.curr.conf` o `$HOME/cfg/rtkrcv.curr.conf`.

`LZERO_RNX2RTKP_CONFIG`
: File configurazione post-processing. Valore attuale: `$HOME/cfg/rnx2rtkp.curr.conf`.

`LZERO_STATION_POS_FILE`
: File coordinate stazioni. Valore attuale: `$HOME/tab/station.pos`.

## Variabili operative opzionali

`LZERO_RTKRCV_TELNET_PORT`
: Porta telnet RTKRCV. Valore attuale: `2950`.

`LZERO_RAW_TCP_PORT`
: Porta TCP dati raw GNSS. Valore attuale: `2222`.

`LZERO_RTCM_TCP_PORT`
: Porta TCP RTCM. Valore attuale: `3333`.

`LZERO_POS_TCP_PORT`
: Porta TCP coordinate POS da RTKRCV. Valore attuale: `5754`.

`LZERO_SERIAL_USB_DEVICE`
: Dispositivo seriale USB u-blox. Valore attuale: `ttyACM0`.

`LZERO_SERIAL_UART_DEVICE`
: Dispositivo seriale UART fallback. Valore attuale: `ttyS0`.

`LZERO_STORAGE_USE_LIMIT`
: Soglia percentuale per cleanup storage. Valore attuale: `90`.

`LZERO_CLEANUP_MIN_FREE_GB`
: Soglia cleanup in `lzer0.cleanup.oldgnss`, se si vuole uniformare anche quello script.


## Proposta di priorita

1. Implementare subito le variabili richieste e quelle derivate strettamente collegate: `LZERO_HOME`, `LZERO_BIN_DIR`, `LZERO_CONFIG_DIR`, `LZERO_LOG_DIR`, `LZERO_VAR_DIR`, `LZERO_TMP_DIR`, `LZERO_STORAGE_MOUNT`, `LZERO_GNSS_DIR`.
2. Centralizzare i file di configurazione applicativa: `LZERO_SITE_CONFIG`, `LZERO_RTKRCV_CONFIG`, `LZERO_RNX2RTKP_CONFIG`, `LZERO_STATION_POS_FILE`.
3. Valutare le variabili operative opzionali solo se vuoi rendere il repository portabile tra installazioni con porte, device seriali o binari diversi.

## Nota implementativa

Per evitare regressioni, ogni script usa default compatibili se `lzer0.env` non esiste. In pratica:

```bash
CONFIG_FILE="${LZERO_ENV_FILE:-${HOME}/cfg/lzer0.env}"
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
fi
LZERO_STORAGE_MOUNT="${LZERO_STORAGE_MOUNT:-/mnt/hd}"
```
