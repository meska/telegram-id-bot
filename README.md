# Telegram ID Bot

Get your numeric Telegram user ID. No spam, tracking or ads.

**[Open @get_myuidBot](https://t.me/get_myuidBot)** — or scan with Telegram:

[![Open the bot](assets/telegram-qr.png)](https://t.me/get_myuidBot)

## Usage

Send any private message. The bot replies with **only your ID**, ready to copy: long-press the reply and tap **Copy**.

In groups, use `/id@get_myuidBot`. Your ID will be visible to the group.

## Privacy

No database, user records or message logs. Everything is processed temporarily in memory; attachments are never downloaded. Telegram itself retains chats according to its own policies.

## Run your own

Python 3.9+, no external dependencies. Keep your bot token in a private file outside the repository:

```sh
TELEGRAM_TOKEN_FILE=/path/to/token python3 -B bot.py
```

A hardened [systemd service](deploy/telegram-id-bot.service) is included. Run only one instance per token. Pending messages are discarded on startup; delivery may be duplicated after network failures.

## Tests

```sh
python3 -B -m unittest discover -s tests -v
```

---

Made by **meskatech** · [MIT license](LICENSE)  
Pixel-art avatar made with [PixelLab](https://www.pixellab.ai/).
