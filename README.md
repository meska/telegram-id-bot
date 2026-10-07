# Telegram ID Bot

Bot minimale open source di meskatech, Python 3.9+ e sola libreria standard.

**Apri il bot:** https://t.me/get_myuidBot
**Codice pubblico:** https://github.com/meska/telegram-id-bot

[![QR per aprire il bot Telegram](assets/telegram-qr.png)](https://t.me/get_myuidBot)

## Uso

In chat privata invia qualsiasi messaggio (anche foto, sticker o audio):

```text
Il tuo ID Telegram: 123456789
```

Nei gruppi risponde solo a `/id@get_myuidBot` e `/start@get_myuidBot`.
Non risponde ad altri bot, canali o messaggi inviati per conto di un canale.
L'ID è quello numerico del mittente, non lo username. Nei gruppi la risposta
è visibile ai partecipanti: preferisci la chat privata.

## Privacy: nessun archivio degli utenti

Il programma non registra nessuno: niente database, file di stato, analytics,
storico o log di ID, messaggi e aggiornamenti. Elabora temporaneamente i dati
in RAM per rispondere; anche l'offset vive solo in memoria. Non conserva gli
aggiornamenti dopo l'elaborazione e non scarica gli allegati.
Il token viene letto da un file dedicato e resta in memoria, mai nel codice.
Gli errori non mostrano URL, token, payload o testo delle eccezioni: soltanto
codici HTTP (0 indica errore di rete/risposta invalida) o un messaggio generico.

**Telegram stesso conserva e gestisce le chat secondo le proprie politiche.**
Questo bot non rende anonime le conversazioni né cancella i messaggi Telegram.
L'assenza di persistenza nell'app non garantisce che il sistema operativo non
usi swap: per requisiti rigorosi disabilitare swap/ibernazione e core dump.
L'unità fornita disabilita i core dump.

## Avvio e affidabilità

1. Verifica il token tramite `getMe`.
2. Controlla `getWebhookInfo`: se esiste un webhook, termina senza cancellarlo.
3. Scarta volontariamente la coda pregressa usando `getUpdates(offset=-1)`;
   avanza l'offset in RAM senza rispondere ai messaggi storici.
4. Esegue long polling seriale (un solo processo), senza porte in ascolto.

Un 403 durante l'invio fa saltare l'aggiornamento; errori di invio vengono
ritentati mantenendo il messaggio e senza avanzare l'offset. Un 429 attende
`retry_after` limitato a 1–60 secondi. Gli altri retry attendono un secondo.
Errori iniziali causano uscita e restart systemd; 401/403/409 nel polling
causano uscita (409 può indicare un altro processo o un webhook).
Gli aggiornamenti malformati senza ID valido vengono ignorati.
SIGTERM/SIGINT interrompono il lavoro; una richiesta già avviata può richiedere
fino a 35 secondi per terminare.

**Non c'è garanzia exactly-once:** dopo una risposta accettata da Telegram ma
con esito HTTP perso, un retry può duplicarla. L'offset volatile può causare
duplicati dopo un crash; al riavvio lo scarto della coda può invece perdere
messaggi ancora non elaborati, inclusi quelli arrivati durante il fermo.
Nessun recupero persistente è previsto. Non avviare più istanze con lo stesso token.

## Installazione Linux con systemd

Richiede Python 3, certificati CA e systemd con `LoadCredential` (Debian 12).
Copia `bot.py` in `/opt/telegram-id-bot/bot.py`, leggibile ma non scrivibile dal
servizio. Predisponi fuori dal repository `/etc/telegram-id-bot/token`, di
proprietà root con permessi `0600` (directory `0700`), usando un canale sicuro:
non mettere il token nella riga di comando, nei log o nella cronologia shell.

Copia `deploy/telegram-id-bot.service` in `/etc/systemd/system/`, poi:

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-id-bot.service
sudo systemctl status telegram-id-bot.service
```

L'unità usa un utente dinamico non root e `LoadCredential` per fornire il token
nel file `%d/token`; `TELEGRAM_TOKEN_FILE` punta a quel file. Nessuna directory
di stato viene creata. Filesystem protetto, nessuna capability e nessuna porta
in ingresso richiesta. Consentire DNS e HTTPS in uscita verso Telegram.

Per un avvio manuale, dopo aver predisposto un file leggibile solo dall'utente:

```sh
TELEGRAM_TOKEN_FILE=/percorso/dedicato/token python3 -B bot.py
```

Se la variabile non è impostata, il percorso è `/etc/telegram-id-bot/token`.
Non eseguire manualmente insieme al servizio. La `.gitignore` è una precauzione,
non un sostituto del tenere i segreti fuori dal repository.

## Test e CI

```sh
python3 -B -m unittest discover -s tests -v
```

I test sono offline: trasporto simulato e token sintetici; non contattano Telegram
né leggono credenziali reali. CI con unittest, nessuna dipendenza pip.

## Informazioni pubbliche del bot

Testo suggerito per la descrizione, da impostare separatamente dall'amministratore:

> Scopri il tuo ID numerico Telegram. Nessun archivio degli utenti nel bot.
> Codice open source: https://github.com/meska/telegram-id-bot

Licenza [MIT](LICENSE), copyright meskatech.
