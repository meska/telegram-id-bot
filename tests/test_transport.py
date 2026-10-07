import contextlib
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

import bot


class TransportTests(unittest.TestCase):
    def test_http_errors_expose_only_status(self):
        def fail(request, timeout):
            raise urllib.error.HTTPError('https://secret/token', 429, 'private payload', {},
                                         io.BytesIO(b'{"parameters":{"retry_after":9999}}'))
        with contextlib.redirect_stderr(io.StringIO()) as output:
            with self.assertRaises(bot.APIError) as raised:
                bot.TelegramAPI('synthetic-test-token', fail).call('sendMessage')
        self.assertEqual(str(raised.exception), 'HTTP 429')
        self.assertEqual(raised.exception.retry_after, 60)
        self.assertEqual(output.getvalue(), '')
        self.assertTrue(raised.exception.__suppress_context__)

    def test_invalid_transport_responses_are_redacted(self):
        for payload in (b'private payload', b'[]', b'{}', b'{"ok":true}',
                        b'{"ok":false,"error_code":403,"description":"private"}'):
            def open_request(request, timeout):
                return io.BytesIO(payload)
            with self.subTest(payload=payload), self.assertRaises(bot.APIError) as raised:
                bot.TelegramAPI('synthetic-test-token', open_request).call('getMe')
            self.assertNotIn('private', str(raised.exception))
        def fail(request, timeout):
            raise urllib.error.URLError('private token')
        with self.assertRaises(bot.APIError) as raised:
            bot.TelegramAPI('synthetic-test-token', fail).call('getMe')
        self.assertEqual(str(raised.exception), 'HTTP 0')

    def test_post_json_and_return_result(self):
        self.assertTrue(hasattr(bot, 'TelegramAPI'), 'transport missing')
        def open_request(request, timeout):
            self.assertEqual(request.get_method(), 'POST')
            self.assertEqual(json.loads(request.data), {'offset': 3})
            self.assertEqual(timeout, 35)
            return io.BytesIO(b'{"ok":true,"result":[]}')
        api = bot.TelegramAPI('synthetic-test-token', opener=open_request)
        self.assertEqual(api.call('getUpdates', offset=3), [])


if __name__ == '__main__':
    unittest.main()
