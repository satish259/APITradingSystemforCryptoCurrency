import datetime
import logging
import requests
import uuid

from requestConstants import (
    apiToken,
    baseAPI,
    errors,
    APIError
)


class RequestHandler(object):
    def __init__(self):
        self._headers = {'Authorization': 'Token %s' % apiToken}
        self._instrument = None
        self._side = None
        self._quantity = None
        self._price = None
        self._valid_until = None
        self._valid_until_dateTime = None
        self._tradableInstruments = []
        self._trades = []

    @staticmethod
    def _isFloat(string):
        """
        Checks if string is float
        """
        try:
            float(string)
            return True
        except ValueError:
            return False

    def _requestHandler(self, request, post_data=None):
        """
        Generic request handler to deal with most frequent connection and HTTP errors.
        All other errors would be caught by generic error handler
        """
        try:
            url = baseAPI + request
            logging.info('url = ' + url)
            if post_data:
                logging.info('post_data = {post_data}'.format(post_data=post_data))
                response = requests.post(url, json=post_data, headers=self._headers)
            else:
                response = requests.get(url, headers=self._headers)
            if response.status_code in errors:
                logging.info(
                    'Error code {c}: {e}'.format(c=response.status_code, e=errors[response.status_code]))
                if 400 >= response.status_code < 500:
                    raise requests.exceptions.HTTPError
                elif 500 >= response.status_code < 1000:
                    raise requests.exceptions.ConnectionError
                else:
                    raise APIError
            else:
                # response.raise_for_status()
                return response.json()
        except Exception as e:
            raise e

    def getBalances(self, ccy=None):
        """
        Fetches balances from 
        ccy is optional should
        """
        try:
            data = self._requestHandler('/balance/')
            if ccy:
                return {ccy: data[ccy]} if ccy in data else None
            else:
                return data
        except Exception as e:
            raise e

    def RFQ(self, instrument, side, quantity):
        """
        Calls RFQ and stored data within class to enable faster trading
        """
        if self._isValid(instrument, side, quantity):
            post_data = {
                'instrument': instrument,
                'side': side,
                'quantity': quantity,
                'client_rfq_id': str(uuid.uuid4())
            }
            try:
                logging.info('Requesting RFQ...')
                data = self._requestHandler('/request_for_quote/', post_data=post_data)
                logging.info(' RFQ received {data}'.format(data=data))
                self._instrument = data["instrument"]
                self._side = data["side"]
                self._quantity = data["quantity"]
                self._price = data["price"]
                self._valid_until = data["valid_until"]
                self._valid_until_dateTime = datetime.datetime.strptime(data["valid_until"], '%Y-%m-%dT%H:%M:%S.%fZ')
                return data
            except Exception as e:
                raise e

    def trade(self):
        """
        Executes the trade based on what is stored in class.
        """
        post_data = {
            'instrument': self._instrument,
            'side': self._side,
            'quantity': self._quantity,
            'client_order_id': str(uuid.uuid4()),
            'price': self._price,
            'order_type': 'FOK',
            'valid_until': self._valid_until,
            'acceptable_slippage_in_basis_points': '0.00',
        }
        if datetime.datetime.utcnow() < self._valid_until_dateTime:  # assuming 1 sec delay and UTC.
            try:
                logging.info('Instructing trade...')
                data = self._requestHandler('/order/', post_data=post_data)
                logging.info(' Trade received {data}'.format(data=data))
                if data['executed_price'] != 'null':
                    self._trades.append(data['client_order_id'])
                    return data
                else:
                    logging.error('Trade failed to execute. Please try again with RFQ.')
                self._reset()  # reset RFQ specific values stored in class
            except Exception as e:
                self._reset()
                raise e
        else:
            self._reset()
            logging.error('Unable to trade as RFQ is out of date.')

    def _isValid(self, instrument, side, quantity):
        """
        Checks the validity of instrument, side and quantity.
        Throws ValueError if they are invalid.
        Note: checks one at a time for better error handling
        """
        out = True
        if instrument not in self._getInstruments():
            raise ValueError('Invalid instrument ' + instrument + '. Please check if instrument is tradable by '
                                                                  'calling _getInstruments.')
        if side not in ['buy', 'sell']:
            raise ValueError("Invalid side " + side + ". 'buy' or 'sell' are the only allowable side.")
        if not self._isFloat(quantity) or float(quantity) < 0:
            raise ValueError('Invalid quantity ' + str(quantity) + ". Quantity must be numeric and greater than zero.")
        return out

    def _getInstruments(self):
        """
        Fetches list of tradable instruments.
        Reuses if already fetched.
        """
        if len(self._tradableInstruments) == 0:
            try:
                logging.info('Fetching instruments...')
                data = self._requestHandler('/instruments/')
                logging.info(' instruments received {data}'.format(data=data))
                self._tradableInstruments = [n['name'] for n in data]
            except Exception as e:
                raise e
        return self._tradableInstruments

    def _reset(self):
        """
        Resets stored values, ready for next RFQ
        This may not be needed unless running in loop
        """
        self._instrument = None
        self._side = None
        self._quantity = None
        self._price = None
        self._valid_until = None
        self._valid_until_dateTime = None

    def getAccountInfo(self):
        """
        Fetches account information related to trading: current risk exposure, maximum risk exposure and
        maximum quantity allowed per trade.
        Note that the risk exposure can be computed by doing the sum of all of the negative balances in USD.
        """
        try:
            logging.info('Fetching account_info...')
            data = self._requestHandler('/account_info/')
            logging.info(' account_info received {data}'.format(data=data))
            return data
        except Exception as e:
            raise e

    def getCurrencies(self):
        """
        Fetches all currencies supported by  and the minimum trade sizes.
        Note that “long_only” means that your balance in this currency cannot be negative.
        """
        try:
            logging.info('Fetching currency...')
            data = self._requestHandler('/currency/')
            logging.info(' currency received {data}'.format(data=data))
            return data
        except Exception as e:
            raise e

    def getAllTrades(self):
        """
        Fetches all your executed trades.
        """
        try:
            logging.info('Fetching trade...')
            data = self._requestHandler('/trade/')
            logging.info(' trade received {data}'.format(data=data))
            return data
        except Exception as e:
            raise e
