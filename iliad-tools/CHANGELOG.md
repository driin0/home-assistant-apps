# Changelog

## 1.0.1

Distribuisce `ghcr.io/driin0/iliad-tools:1.0.1`.

Le registrazioni SIP generate non si fermano più dopo un disservizio del
carrier. Asterisk applica per default `max_retries=10` a ogni registrazione in
uscita, con gli altri due intervalli di retry a 0: dieci fallimenti consecutivi
— circa dieci minuti — la fermano per sempre, e le chiamate in uscita cadono
all'istante. Ora il generatore emette `max_retries`, `fatal_retry_interval` e
`forbidden_retry_interval` sia sul trunk Iliad sia sui trunk 3CX.

**La configurazione già installata non si aggiorna da sola**: la modifica sta
nei file generati, non nel portale. Dopo l'aggiornamento va rigenerato
l'archivio dal tab Asterisk e ridistribuito sull'add-on Asterisk, altrimenti la
macchina resta con i default di Asterisk.

Corretto anche il nome del container dell'add-on Asterisk nei comandi stampati:
era fisso a `addon_3e533915_asterisk`, ma su installazioni recenti il container
si chiama `app_3e533915_asterisk` e i comandi copiati dalla UI fallivano con
"No such container". Ora viene risolto al momento.

Note complete nel
[CHANGELOG del progetto](https://github.com/driin0/iliad-tools/blob/main/CHANGELOG.md).

## 1.0.0

Prima pubblicazione come app di Home Assistant.

L'app distribuisce l'immagine `ghcr.io/driin0/iliad-tools:1.0.0`. Le note di
versione dell'applicazione stanno nel
[CHANGELOG del progetto](https://github.com/driin0/iliad-tools/blob/main/CHANGELOG.md),
che parte da aprile 2026: la `1.0.0` dichiara che il progetto non è una beta,
non che nasce oggi.

Chi usava la versione dal repository privato: per Home Assistant è
un'installazione distinta, quindi i dati non vengono migrati da soli. Prima di
disinstallare la vecchia, copiare `routers.enc`, `vpn_data.json` e
`asterisk_data.enc` dalla sua directory in `/addon_configs/` a quella della
nuova.
