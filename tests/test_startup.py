import contextlib
import io
import unittest
from unittest.mock import mock_open, patch

import bot


class StartupTests(unittest.TestCase):
    def test_main_stops_on_signals_and_redacts_errors(self):
        self.assertTrue(hasattr(bot, 'main'), 'entrypoint missing')
        handlers = {}
        def register(sig, handler):
            handlers[sig] = handler
        with patch.object(bot, 'read_token', return_value='123:test-token'), \
                patch.object(bot.Bot, 'run', side_effect=RuntimeError('PRIVATE')), \
                patch('signal.signal', side_effect=register), \
                contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(bot.main(), 1)
        self.assertEqual(output.getvalue(), 'Startup or runtime error.\n')
        self.assertEqual(len(handlers), 2)
        for handler in handlers.values():
            handler(None, None)

    def test_token_read_only_from_dedicated_file(self):
        self.assertTrue(hasattr(bot, 'read_token'), 'token reader missing')
        with patch.dict('os.environ', {'TELEGRAM_TOKEN_FILE': '/dedicated/token'}, clear=True):
            with patch('builtins.open', mock_open(read_data='123:test-token\n')) as opened:
                self.assertEqual(bot.read_token(), '123:test-token')
            opened.assert_called_once_with('/dedicated/token', encoding='utf-8')
        with patch.dict('os.environ', {}, clear=True):
            with patch('builtins.open', mock_open(read_data='123:test-token')) as opened:
                bot.read_token()
            opened.assert_called_once_with('/etc/telegram-id-bot/token', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
