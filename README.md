# Telegram ID Bot

A tiny open-source Telegram bot by meskatech. Python 3.9+, standard library only.

**Open the bot:** https://t.me/get_myuidBot

**Source code:** https://github.com/meska/telegram-id-bot

[![Scan with Telegram to open the bot](assets/telegram-qr.png)](https://t.me/get_myuidBot)

## Usage

Send any private message, including a photo, sticker or voice message. The bot replies with **only your numeric Telegram user ID**:

```text
123456789
```

On your phone, long-press the reply and choose **Copy**. There is no surrounding text to remove.

In groups, use `/id@get_myuidBot` or `/start@get_myuidBot`. The reply is visible to the group, so prefer a private chat. Messages from bots, channels or users posting on behalf of a channel are ignored.

## Privacy: no user records

No database, user registry, analytics, message history, update files or user-data logs. Updates are processed temporarily in RAM; the polling offset is also held only in memory. Attachments are never downloaded. The bot token is read from a dedicated file outside the repository.

Errors contain only HTTP status codes (0 means a network or invalid-response error) or a generic message, never token-bearing URLs, payloads or exception details.

**Telegram itself stores and manages chats according to its own policies.** This bot does not anonymize conversations or delete Telegram messages. Application-level non-persistence does not prevent operating-system swap or hibernation; disable those if required. The supplied systemd unit disables core dumps. The hosted container has swap disabled.

## Startup and reliability

- Validates the bot identity with `getMe`.
- Checks `getWebhookInfo` and exits if a webhook exists, without deleting it.
- Discards the previous backlog using `getUpdates(offset=-1)` without replying to historical messages.
- Runs one serial long-polling process. No inbound ports are required.

A send failure is retried without advancing the offset; HTTP 403 skips the update. HTTP 429 waits for `retry_after`, bounded to 1–60 seconds. Other retries wait one second. Startup errors and polling HTTP 401/403/409 exit for systemd to restart. Malformed updates without a valid update ID are ignored. SIGTERM/SIGINT stop the service; an outstanding request may take up to 35 seconds to finish.

**Delivery is not exactly-once.** If Telegram accepts a reply but its HTTP response is lost, a retry may duplicate the reply. Volatile offsets can also cause duplicates after a crash. Startup backlog discard can lose unprocessed messages, including messages received while the service was down. There is intentionally no persistent recovery. Do not run multiple instances with the same token.

## Linux installation with systemd

Requires Python 3, CA certificates and systemd with `LoadCredential` support (Debian 12).

1. Copy `bot.py` to `/opt/telegram-id-bot/bot.py`, readable but not writable by the service.
2. Provision `/etc/telegram-id-bot/token` outside the repository through a secure channel: root-owned, mode `0600`, parent directory mode `0700`. Never put the token in command-line arguments, logs or shell history.
3. Copy `deploy/telegram-id-bot.service` to `/etc/systemd/system/`.
4. Start the service:

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-id-bot.service
sudo systemctl status telegram-id-bot.service
```

The unit runs as a non-root dynamic user. `LoadCredential` provides the token at `%d/token`, referenced by `TELEGRAM_TOKEN_FILE`. No state directory is created. The filesystem is protected and capabilities are dropped. Allow outbound DNS and HTTPS to Telegram.

For manual execution, use a token file readable only by the running user:

```sh
TELEGRAM_TOKEN_FILE=/path/to/private/token python3 -B bot.py
```

The default path is `/etc/telegram-id-bot/token`. Never run manual execution alongside the service. `.gitignore` is a precaution, not a substitute for keeping secrets outside the repository.

## Tests and CI

Run from the repository root:

```sh
python3 -B -m unittest discover -s tests -v
```

Tests are offline, with simulated transport and synthetic tokens. They do not contact Telegram or read real credentials. GitHub Actions runs unittest without pip dependencies.

## Bot information

The hosted bot's public information links to this repository. Suggested description for another deployment:

> Send any message to get your numeric Telegram user ID. No user records, tracking or ads.
> Open source: https://github.com/meska/telegram-id-bot

## Artwork

The pixel-art avatar was generated with PixelLab (one generation). The original 128×128 PNG is preserved; the Telegram upload is a 512×512 nearest-neighbor JPEG derivative. The generation recipe is in `pixellab-pip-generations/avatar/`. The QR code opens the bot's public Telegram link.

[MIT license](LICENSE), copyright meskatech.
