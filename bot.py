"""Telegram numeric ID bot: no persistent application state."""
import threading
import json
import urllib.request
import os
import signal
import sys


def main():
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda signum, frame: stop.set())
    try:
        Bot(TelegramAPI(read_token()), stop).run()
        return 0
    except APIError as error:
        print(f'HTTP {error.status}', file=sys.stderr)
    except Exception:
        print('Errore di avvio o esecuzione.', file=sys.stderr)
    return 1


def read_token():
    path = os.environ.get('TELEGRAM_TOKEN_FILE', '/etc/telegram-id-bot/token')
    with open(path, encoding='utf-8') as source:
        return source.read().strip()



class TelegramAPI:
    def __init__(self, token, opener=urllib.request.urlopen):
        self.token = token
        self.opener = opener

    def call(self, method, **params):
        request = urllib.request.Request(
            f'https://api.telegram.org/bot{self.token}/{method}',
            data=json.dumps(params).encode('utf-8'),
            headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with self.opener(request, timeout=35) as response:
                body = json.load(response)
            if not isinstance(body, dict):
                raise APIError(0)
            if body.get('ok') is not True:
                status = body.get('error_code')
                parameters = body.get('parameters')
                retry_after = parameters.get('retry_after', 1) if isinstance(parameters, dict) else 1
                raise APIError(status if type(status) is int else 0, retry_after)
            if 'result' not in body:
                raise APIError(0)
            return body['result']
        except urllib.error.HTTPError as error:
            retry_after = 1
            if error.code == 429:
                try:
                    body = json.load(error)
                    retry_after = body.get('parameters', {}).get('retry_after', 1)
                except (ValueError, TypeError, AttributeError, OSError):
                    pass
            error.close()
            raise APIError(error.code, retry_after) from None
        except (OSError, ValueError, TypeError):
            raise APIError(0) from None



class APIError(Exception):
    def __init__(self, status, retry_after=1):
        self.status = status
        self.retry_after = (max(1, min(60, retry_after))
                            if type(retry_after) is int else 1)
        super().__init__(f'HTTP {status}')


class Bot:
    def __init__(self, api, stop=None):
        self.api = api
        self.stop = stop if stop is not None else threading.Event()
        self.offset = 0
        self.username = ''

    def run(self):
        self.startup()
        while not self.stop.is_set():
            try:
                self.poll_once()
            except APIError as error:
                if error.status in (401, 403, 409):
                    raise
                self.stop.wait(error.retry_after if error.status == 429 else 1)

    def poll_once(self):
        updates = self.api.call('getUpdates', offset=self.offset, timeout=25,
                                allowed_updates=['message'])
        for update in updates:
            if self.stop.is_set():
                return
            if (not isinstance(update, dict) or type(update.get('update_id')) is not int
                    or update['update_id'] < self.offset):
                continue
            reply = reply_for(update, self.username)
            if reply:
                while True:
                    try:
                        self.api.call('sendMessage', chat_id=reply[0], text=reply[1])
                        break
                    except APIError as error:
                        if error.status == 403:
                            break
                        delay = error.retry_after if error.status == 429 else 1
                        if self.stop.wait(delay):
                            return
            self.offset = update['update_id'] + 1

    def startup(self):
        identity = self.api.call('getMe')
        if (not isinstance(identity, dict) or identity.get('is_bot') is not True
                or not isinstance(identity.get('username'), str) or not identity['username']):
            raise RuntimeError('Identità bot non valida')
        self.username = identity['username']
        webhook = self.api.call('getWebhookInfo')
        if not isinstance(webhook, dict) or webhook.get('url') != '':
            raise RuntimeError('Webhook configurato o risposta non valida')
        updates = self.api.call('getUpdates', offset=-1, timeout=0,
                                allowed_updates=['message'])
        for update in updates:
            if (isinstance(update, dict) and type(update.get('update_id')) is int
                    and update['update_id'] >= 0):
                self.offset = max(self.offset, update['update_id'] + 1)



def reply_for(update, username):
    if not isinstance(update, dict):
        return None
    msg = update.get('message')
    if not isinstance(msg, dict):
        return None
    chat, sender = msg.get('chat'), msg.get('from')
    if not isinstance(chat, dict) or not isinstance(sender, dict):
        return None
    if (type(chat.get('id')) is not int or type(sender.get('id')) is not int
            or sender['id'] <= 0 or sender.get('is_bot') or msg.get('sender_chat')):
        return None
    if chat.get('type') != 'private':
        text = msg.get('text', '')
        if not isinstance(text, str):
            return None
        command = text.split()[0].lower() if text.split() else ''
        if chat.get('type') not in ('group', 'supergroup') or command not in (
                '/id@' + username.lower(), '/start@' + username.lower()):
            return None
    return msg['chat']['id'], f"Il tuo ID Telegram: {msg['from']['id']}"


if __name__ == '__main__':
    sys.exit(main())
