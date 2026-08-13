# Iliad Tools

Portale di amministrazione per **iliadbox**, il router di Iliad Italia (firmware
Freebox OS). Espone le API del router in un'interfaccia unica, raggiungibile dal
pannello laterale di Home Assistant.

## Funzionalità

- **Stato** — connessione WAN, IP pubblico v4/v6, grafico di banda in tempo
  reale, storico da RRD, porte LAN dello switch, log degli eventi di linea
- **DHCP statici** — lease con stato online/offline, ricerca, ordinamento,
  export CSV/JSON/Markdown
- **Dispositivi** — device LAN con vendor, tipo, qualità del collegamento
  (Ethernet o Wi-Fi con dBm) e Wake on LAN
- **Port forwarding** — regole con toggle, verifica delle porte dall'esterno
- **Wi-Fi** — reti e cifratura effettiva, QR di connessione, analisi delle reti
  vicine e occupazione dei canali
- **VPN** — server WireGuard/OpenVPN/IPsec, utenti, profili riutilizzabili,
  connessioni attive, config e QR
- **Asterisk** — generatore di configurazione per il trunk SIP Iliad, gli
  interni e i trunk 3CX multi-tenant, con archivio pronto da applicare

## Configurazione

| Opzione | Default | Descrizione |
|---------|---------|-------------|
| `port` | `31996` | Porta HTTP dell'app. Lasciare il default salvo conflitti |

## Primo avvio

Al primo accesso compare il wizard: si sceglie una **master password** e si
aggiunge il primo router, indicandone l'indirizzo LAN e la password
dell'interfaccia web dell'iliadbox.

La master password non viene salvata da nessuna parte — nel file resta solo un
hash di verifica. Da essa si deriva, con PBKDF2, la chiave AES-256-GCM che cifra
le credenziali dei router. **Se la si perde, i dati non sono recuperabili** e va
rifatta la configurazione.

## Accesso

- **Ingress**, dal pannello laterale di Home Assistant: nessuna porta da aprire
- Oppure `http://<indirizzo-ha>:31996`, se si è mappata la porta

## Dove finiscono i dati

L'app scrive in `/config/data/` dentro il container, che corrisponde a
`/addon_configs/<slug>_iliad_tools/data/` visto da Home Assistant:

| File | Contenuto |
|------|-----------|
| `routers.enc` | Credenziali dei router, cifrate |
| `vpn_data.json` | Profili VPN e associazione utente → profilo, per router |
| `asterisk_data.enc` | Interni SIP e trunk 3CX, cifrati |

Sono i file da copiare per spostare la configurazione su un'altra istanza.

## Licenza

Copyright (C) 2026 Riccardo Riina (driin0) — AGPL-3.0-or-later.

Il codice dell'applicazione vive in
[driin0/iliad-tools](https://github.com/driin0/iliad-tools); questa app ne
distribuisce l'immagine come app di Home Assistant.

## Marchi

**Iliad** e **iliadbox** sono marchi di Iliad Italia S.p.A.; **Freebox** di
Free SAS; **Home Assistant** della Open Home Foundation; **3CX** di 3CX Ltd.
Progetto indipendente, non affiliato né approvato da nessuna di queste società.
