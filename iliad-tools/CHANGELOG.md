# Changelog

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
