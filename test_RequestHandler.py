import datetime
import requests
from mock import patch
from RequestHandler import RequestHandler
from requestConstants import APIError
from unittest import TestCase


class TestRequestHandler(TestCase):
    def test_isFloat(self):
        rH = RequestHandler()
        self.assertTrue(rH._isFloat('3.1415'))
        self.assertFalse(rH._isFloat('3+6j'))

    def test_requestHandler(self):
        with patch('requests.get') as mRequest:
            mRequest.return_value.status_code = 200
            mRequest.return_value.json.return_value = {"USD": "0"}
            rH = RequestHandler()
            self.assertEqual(rH._requestHandler('/balance/'), {"USD": "0"})

    def test_requestHandler_Post(self):
        with patch('requests.post') as mRequest:
            mRequest.return_value.status_code = 200
            mRequest.return_value.json.return_value = {"USD": "0"}
            rH = RequestHandler()
            self.assertEqual(rH._requestHandler('/request_for_quote/', {"USD": "0"}), {"USD": "0"})

    def test_requestHandler_HTTPError(self):
        with patch('requests.get') as mRequest:
            mRequest.return_value.status_code = 400
            rH = RequestHandler()
            with self.assertRaises(requests.exceptions.HTTPError):
                rH._requestHandler('/balance/')

    def test_requestHandler_ConnectionError(self):
        with patch('requests.get') as mRequest:
            mRequest.return_value.status_code = 500
            rH = RequestHandler()
            with self.assertRaises(requests.exceptions.ConnectionError):
                rH._requestHandler('/balance/')

    def test_requestHandler_APIError(self):
        with patch('requests.get') as mRequest:
            mRequest.return_value.status_code = 1010
            rH = RequestHandler()
            with self.assertRaises(APIError):
                rH._requestHandler('/balance/')

    def test_getBalances(self):
        out = {"USD": "0",}
        with patch('requests.get') as mRequest:
            mRequest.return_value.status_code = 200
            mRequest.return_value.json.return_value = out
            rH = RequestHandler()
            self.assertEqual(rH.getBalances(), out)
            self.assertEqual(rH.getBalances("USD"), {"USD": "0"})

    def test_getInstruments(self):
        out = [{ "name": "BTCUSD.CFD"},]
        with patch('requests.get') as mRequest:
            mRequest.return_value.status_code = 200
            mRequest.return_value.json.return_value = out
            rH = RequestHandler()
            self.assertEqual(rH._getInstruments(),
                             ['BTCUSD.CFD'])

    def test_RFQ(self):
        get = [{"name": "BTCUSD.SPOT"},]
        post = {
            "valid_until": "2020-02-28T11:41:30.023467Z",
            "rfq_id": "some_unique_ID",
            "client_rfq_id": "some_unique_client_id",
            "quantity": "1.0000000000",
            "side": "buy",
            "instrument": "BTCUSD.SPOT",
            "price": "1.00000000",
            "created": "2020-02-28T11:41:15.023467Z"
        }
        with patch('requests.get') as mGet:
            with patch('requests.post') as mPost:
                mGet.return_value.status_code = 200
                mGet.return_value.json.return_value = get
                mPost.return_value.status_code = 200
                mPost.return_value.json.return_value = post
                rH = RequestHandler()
                self.assertEqual(rH.RFQ("BTCUSD.SPOT", "buy", "1.0"), post)
                self.assertEqual(rH._price, "1.00000000")

    def test_trade(self):
        get = [{ "name": "BTCUSD.CFD"},]
        post = {
            "valid_until": "2020-02-28T11:41:30.023467Z",
            "rfq_id": "d4e41399-e7a1-4576-9b46-349420040e1a",
            "client_rfq_id": "149dc3e7-4e30-4e1a-bb9c-9c30bd8f5ec7",
            "quantity": "1.0000000000",
            "side": "buy",
            "instrument": "BTCUSD.SPOT",
            "price": "700.00000000",
            "created": "2018-02-06T16:07:50.122206Z"
        }
        trade = {
            "order_id": "d4e41399-e7a1-4576-9b46-349420040e1a",
            "client_order_id": "d4e41399-e7a1-4576-9b46-349420040e1a",
            "quantity": "3.0000000000",
            "side": "buy",
            "instrument": "BTCUSD.SPOT",
            "price": "11000.00000000",
            "executed_price": "10457.651100000",
            "executing_unit": "risk-adding-strategy",
            "trades": [
                {
                    "instrument": "BTCUSD.SPOT",
                    "trade_id": "b2c50b72-92d4-499f-b0a3-dee6b37378be",
                    "origin": "rest",
                    "rfq_id": 'null',
                    "created": "2018-02-26T14:27:53.675962Z",
                    "price": "10457.65110000",
                    "quantity": "3.0000000000",
                    "order": "d4e41399-e7a1-4576-9b46-349420040e1a",
                    "side": "buy",
                    "executing_unit": "risk-adding-strategy",
                }
            ],
            "created": "2018-02-06T16:07:50.122206Z"
        }

        with patch('requests.get') as mGet:
            with patch('requests.post') as mPost:
                mGet.return_value.status_code = 200
                mGet.return_value.json.return_value = get
                mPost.return_value.status_code = 200
                mPost.return_value.json.side_effect = [post, trade]
                rH = RequestHandler()
                rH.RFQ("BTCUSD.SPOT", "buy", "1.0")
                self.assertEqual(rH._price, "700.00000000")
                rH._valid_until_dateTime = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
                rH.trade()
                self.assertEqual(rH._trades, ["d4e41399-e7a1-4576-9b46-349420040e1a"])

    def test_trade_fail(self):
        get = [{ "name": "BTCUSD.CFD"},]
        post = {
            "valid_until": "2020-02-28T11:41:30.023467Z",
            "rfq_id": "d4e41399-e7a1-4576-9b46-349420040e1a",
            "client_rfq_id": "149dc3e7-4e30-4e1a-bb9c-9c30bd8f5ec7",
            "quantity": "1.0000000000",
            "side": "buy",
            "instrument": "BTCUSD.SPOT",
            "price": "700.00000000",
            "created": "2018-02-06T16:07:50.122206Z"
        }
        trade = {
            "order_id": "d4e41399-e7a1-4576-9b46-349420040e1a",
            "client_order_id": "d4e41399-e7a1-4576-9b46-349420040e1a",
            "quantity": "3.0000000000",
            "side": "buy",
            "instrument": "BTCUSD.SPOT",
            "price": "11000.00000000",
            "executed_price": "10457.651100000",
            "executing_unit": "risk-adding-strategy",
            "trades": [
                {
                    "instrument": "BTCUSD.SPOT",
                    "trade_id": "b2c50b72-92d4-499f-b0a3-dee6b37378be",
                    "origin": "rest",
                    "rfq_id": 'null',
                    "created": "2018-02-26T14:27:53.675962Z",
                    "price": "10457.65110000",
                    "quantity": "3.0000000000",
                    "order": "d4e41399-e7a1-4576-9b46-349420040e1a",
                    "side": "buy",
                    "executing_unit": "risk-adding-strategy",
                }
            ],
            "created": "2018-02-06T16:07:50.122206Z"
        }

        with patch('requests.get') as mGet:
            with patch('requests.post') as mPost:
                mGet.return_value.status_code = 200
                mGet.return_value.json.return_value = get
                mPost.return_value.status_code = 200
                mPost.return_value.json.side_effect = [post, trade]
                rH = RequestHandler()
                rH.RFQ("BTCUSD.SPOT", "buy", "1.0")
                self.assertEqual(rH._price, "700.00000000")
                self.assertIsNone(rH.trade())

    def test_isValid_instrument(self):
        get = [{ "name": "BTCUSD.CFD"},]
        with patch('requests.get') as mGet:
            mGet.return_value.status_code = 200
            mGet.return_value.json.return_value = get
            with self.assertRaises(ValueError):
                rH = RequestHandler()
                rH._isValid('BTCUSD', 'buy', '1')

    def test_isValid_side(self):
        get = [{ "name": "BTCUSD.CFD"},]
        with patch('requests.get') as mGet:
            mGet.return_value.status_code = 200
            mGet.return_value.json.return_value = get
            with self.assertRaises(ValueError):
                rH = RequestHandler()
                rH._isValid('BCHUSD.SPOT', 'funny_side', '1')

    def test_isValid_quantity(self):
        get = [{ "name": "BTCUSD.CFD"},]
        with patch('requests.get') as mGet:
            mGet.return_value.status_code = 200
            mGet.return_value.json.return_value = get
            with self.assertRaises(ValueError):
                rH = RequestHandler()
                rH._isValid('XRPUSD.SPOT', 'buy', '3+6j')

    def test_getAccountInfo(self):
        out = {
            "risk_exposure": "10000.15",
            "max_risk_exposure": "50000",
            "btc_max_qty_per_trade": "100",
            "ust_max_qty_per_trade": "600000"
        }
        with patch('requests.get') as mRequest:
            mRequest.return_value.status_code = 200
            mRequest.return_value.json.return_value = out
            rH = RequestHandler()
            self.assertEqual(rH.getAccountInfo(), out)

    def test_getCurrencies(self):
        out = {
            "BTC": {
                "stable_coin": 'false',
                "is_crypto": 'true',
                "currency_type": "crypto",
                "readable_name": "Bitcoin",
                "long_only": 'false',
                "minimum_trade_size": 0.001
            }
        }
        with patch('requests.get') as mRequest:
            mRequest.return_value.status_code = 200
            mRequest.return_value.json.return_value = out
            rH = RequestHandler()
            self.assertEqual(rH.getCurrencies(), out)

    def test_getAllTrades(self):
        out = [
            {
                "created": "2016-09-27T11:27:46.599039Z",
                "price": "700.0000000000",
                "instrument": "BTCUSD.CFD",
                "trade_id": "5c7e90cc-a8d6-4db5-8348-44053b2dcbdf",
                "origin": "rest",
                "rfq_id": "f7492962-783e-45c7-ae81-6eb61f4d7251",
                "order": 'null',
                "cfd_contract": "945bac72-4d88-401b-9a7f-27bc328a125f",
                "side": "buy",
                "quantity": "0.5000000000",
                "user": "user@.com",
                "executing_unit": "risk-adding-strategy"
            },
        ]

        with patch('requests.get') as mRequest:
            mRequest.return_value.status_code = 200
            mRequest.return_value.json.return_value = out
            rH = RequestHandler()
            self.assertEqual(rH.getAllTrades(), out)
