import unittest

try:
    import bot
except ImportError:
    bot = None


def message(chat_type='private', text=None):
    msg = {'chat': {'id': 123, 'type': chat_type}, 'from': {'id': 456}}
    if text is not None:
        msg['text'] = text
    return {'update_id': 1, 'message': msg}


class ReplyTests(unittest.TestCase):
    def test_private_any_content(self):
        self.assertIsNotNone(bot, 'bot implementation missing')
        self.assertEqual(bot.reply_for(message(), 'idbot'), (123, 'Il tuo ID Telegram: 456'))

    def test_group_only_explicitly_addressed_commands(self):
        self.assertIsNone(bot.reply_for(message('group', 'ciao'), 'idbot'))
        self.assertIsNone(bot.reply_for(message('supergroup', '/id'), 'idbot'))
        self.assertIsNone(bot.reply_for(message('group', '/id@other'), 'idbot'))
        self.assertEqual(bot.reply_for(message('group', '/id@IDBOT'), 'idbot'),
                         (123, 'Il tuo ID Telegram: 456'))
        self.assertEqual(bot.reply_for(message('supergroup', '/start@idbot'), 'idbot'),
                         (123, 'Il tuo ID Telegram: 456'))

    def test_malformed_updates_are_ignored(self):
        for update in (None, [], {}, {'message': None}, {'message': []},
                       {'message': {'chat': None}},
                       {'message': {'chat': {'id': 123}, 'from': {'id': 456}}},
                       message('group', 7)):
            with self.subTest(update=update):
                self.assertIsNone(bot.reply_for(update, 'idbot'))
        for key in ('chat', 'from'):
            update = message()
            update['message'][key]['id'] = True
            self.assertIsNone(bot.reply_for(update, 'idbot'))
        update = message()
        update['message']['from']['is_bot'] = True
        self.assertIsNone(bot.reply_for(update, 'idbot'))


class FakeAPI:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def call(self, method, **params):
        self.calls.append((method, params))
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


class PollTests(unittest.TestCase):
    def test_webhook_is_fatal_without_deletion(self):
        api = FakeAPI([{'is_bot': True, 'username': 'idbot'}, {'url': 'configured'}])
        with self.assertRaises(RuntimeError):
            bot.Bot(api).startup()
        self.assertEqual([c[0] for c in api.calls], ['getMe', 'getWebhookInfo'])

    def test_invalid_identity_is_fatal(self):
        for identity in ({}, None, {'username': 'idbot', 'is_bot': False}):
            with self.subTest(identity=identity), self.assertRaises(RuntimeError):
                bot.Bot(FakeAPI([identity])).startup()

    def test_malformed_backlog_is_safe(self):
        runner = bot.Bot(FakeAPI([{'is_bot': True, 'username': 'idbot'},
                                 {'url': ''}, [None, {}, {'update_id': True}, message()]]))
        runner.startup()
        self.assertEqual(runner.offset, 2)

    def test_poll_replies_then_advances_offset(self):
        self.assertTrue(hasattr(bot.Bot, 'poll_once'), 'polling missing')
        api = FakeAPI([[None, {}, {'update_id': True}, message()], True])
        runner = bot.Bot(api)
        runner.username = 'idbot'
        runner.poll_once()
        self.assertEqual(runner.offset, 2)
        self.assertEqual(api.calls[-1], ('sendMessage',
                         {'chat_id': 123, 'text': 'Il tuo ID Telegram: 456'}))
        self.assertEqual(api.calls[0][1]['offset'], 0)

    def test_transient_send_retries_before_advancing(self):
        self.assertTrue(hasattr(bot, 'APIError'), 'safe errors missing')
        class Waiter:
            def is_set(self):
                return False

            def wait(inner, delay):
                self.assertEqual(runner.offset, 0)
                self.assertEqual(delay, 1)
                return False
        api = FakeAPI([[message()], bot.APIError(503), True])
        runner = bot.Bot(api, Waiter())
        runner.poll_once()
        self.assertEqual(runner.offset, 2)
        self.assertEqual([c[0] for c in api.calls],
                         ['getUpdates', 'sendMessage', 'sendMessage'])

    def test_send_403_skips_update(self):
        api = FakeAPI([[message()], bot.APIError(403)])
        runner = bot.Bot(api)
        runner.poll_once()
        self.assertEqual(runner.offset, 2)

    def test_429_delay_is_bounded_and_stop_keeps_offset(self):
        class Waiter:
            def is_set(self):
                return False

            def wait(inner, delay):
                self.assertEqual(delay, 60)
                return True
        api = FakeAPI([[message()], bot.APIError(429, 999999)])
        runner = bot.Bot(api, Waiter())
        runner.poll_once()
        self.assertEqual(runner.offset, 0)
        self.assertEqual(len(api.calls), 2)

    def test_run_retries_poll_failure_and_stops(self):
        self.assertTrue(hasattr(bot.Bot, 'run'), 'run loop missing')
        import threading
        stop = threading.Event()
        class API(FakeAPI):
            def call(inner, method, **params):
                if method == 'getUpdates' and params['offset'] >= 0 and len(inner.calls) == 4:
                    stop.set()
                    inner.calls.append((method, params))
                    return []
                return super().call(method, **params)
        api = API([{'is_bot': True, 'username': 'idbot'}, {'url': ''}, [], bot.APIError(503)])
        runner = bot.Bot(api, stop)
        runner.run()
        self.assertEqual(len(api.calls), 5)
        self.assertEqual(runner.offset, 0)

    def test_stopped_poll_does_not_send_or_advance(self):
        import threading
        stop = threading.Event()
        stop.set()
        runner = bot.Bot(FakeAPI([[message()]]), stop)
        runner.poll_once()
        self.assertEqual(runner.offset, 0)
        self.assertEqual(len(runner.api.calls), 1)

    def test_startup_checks_identity_and_discards_backlog(self):
        self.assertTrue(hasattr(bot, 'Bot'), 'poller missing')
        api = FakeAPI([{'id': 9, 'is_bot': True, 'username': 'idbot'},
                       {'url': ''}, [message()]])
        runner = bot.Bot(api)
        runner.startup()
        self.assertEqual(runner.offset, 2)
        self.assertEqual([c[0] for c in api.calls],
                         ['getMe', 'getWebhookInfo', 'getUpdates'])
        self.assertEqual(api.calls[-1][1]['offset'], -1)
        self.assertEqual(api.calls[-1][1]['timeout'], 0)


if __name__ == '__main__':
    unittest.main()
