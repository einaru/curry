"""
    Curry
    ~~~~~

    Exchange-rate API providers

    Copyright: (c) 2014 Einar Uvsløkk
    License: GNU General Public License (GPL) version 3 or later
"""
# TODO:2014-10-23:einar: review use of appropriate log levels
import os
import json
import logging
import urllib.error
import urllib.request
import time
import requests

from curry.config import config, get_cache_file

log = logging.getLogger(__name__)

Providers = {}
"""A dictionary containing all available API providers."""


def register_api_provider(api, cls, requires=[]):
    Providers[api] = {'class': cls, 'requires': requires}


def list_api_providers():
    print('Available API providers:')
    for api in Providers.keys():
        output = '  {}'.format(api)
        requires = ', '.join(Providers[api].get('requires', []))
        if len(requires) > 0:
            output = '{} (requires: {})'.format(output, requires)
        print(output)


def cache_has_expired(timestamp):
    # Safe guard against user configuration error
    try:
        cache_timeout = config.get('cache_timeout')
    except:
        cache_timeout = config.default_cache_timeout()

    return timestamp < time.time() - cache_timeout


class Provider:
    """Main interface for the providers."""

    def __init__(self, **kwargs):
        self.api = None
        self.use_api(**kwargs)

    def use_api(self, **kwargs):
        assert 'api' in kwargs
        api = kwargs.pop('api')
        if api not in Providers:
            raise APIError('Unknown API provider: {}'.format(api))

        if self.api:
            log.info('Switching API provider: {} -> {}'.format(self.api, api))

        self.api = Providers[api]['class'](**kwargs)

    def get_exchange_rate(self, transaction, payment):
        if not self.api:
            raise APIError('No API provider is set!')

        transaction, payment = transaction.upper(), payment.upper()
        log.info('Using API provider: {}'.format(self.api.id_))
        rate = -1
        try:
            rate = self.api.get_exchange_rate(transaction, payment)
        # XXX:2014-10-22:einar: do HTTP error handling more granular?
        except urllib.error.HTTPError as e:
            log.error(e)

        return rate


class APIError(Exception):
    """Common exception class for all API errors."""

    def __init__(self, message, id_=None):
        self.message = message
        self.id_ = id_

    def __str__(self):
        if self.id_:
            return 'APIError: ({}) {}'.format(self.id_, self.message)
        return 'APIError: {}'.format(self.message)


class APIProvider:
    """Super class for API providers."""

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.cache = {}

    def get_exchange_rate(self, transaction, payment):
        """Must be implemented in every subclass."""

    def save_cache(self, transaction, payment, rate):
        """Save the exchange rate data for a currency pair (transaction
        currency and payment currency), together with a timestamp.

        :param transaction: the transaction (from) currency.
        :param payment: the payment (to) currency.
        :param rate: the exchange rate for the currency pair.

        :returns: True if the cache is saved, False otherwise.
        """
        if not hasattr(self, 'cache_file'):
            log.warn('Trying to save cache, but no cache_file is declared')
            return False

        cache = {
            payment: {
                'rate': rate,
                'timestamp': time.time(),
            }
        }

        if transaction in self.cache:
            self.cache[transaction].update(cache)
        else:
            self.cache[transaction] = cache

        with open(self.cache_file, 'w') as f:
            f.write(json.dumps(self.cache))

        log.info('Cache saved.')
        return True

    def load_cache(self):
        """Load the cache file

        :returns: True if the cache file is loaded, False if its not,
            and None if no cache_file attribute is declared.
        """
        if not hasattr(self, 'cache_file'):
            log.warn('Trying to load cache, but no cache_file is declared')
            return None

        if os.path.isfile(self.cache_file):
            with open(self.cache_file) as f:
                self.cache = json.load(f)
            log.info('Cache loaded.')
            return True

        return False

    def dump_http_response(self, response):
        log.debug('*** Start: HTTP Response DUMP ***')
        log.debug('  Status code: {}'.format(response.status_code))
        log.debug('  Headers:')
        for k, v in response.headers.items():
            log.debug('    {}: {}'.format(k, v))
        log.debug('  Content:')
        log.debug('    {}'.format(response.content))
        log.debug('*** End ***')


class Yahoo(APIProvider):
    id_ = 'finance.yahoo.com'
    url = 'http://download.finance.yahoo.com/d/quotes.csv?s={}{}=X&f=l1'

    def __init__(self, api_key=None):
        APIProvider.__init__(self, api_key)
        self.cache_file = get_cache_file(self.id_)

    def get_exchange_rate(self, transaction, payment):
        self.load_cache()

        rate = None
        if transaction in self.cache:
            data = self.cache[transaction].get(payment, None)
            if data and not cache_has_expired(data.get('timestamp')):
                rate = data.get('rate')

        # If rate is None here the exchange rate was either not cached
        # or its timestamp was too old, therefor we need to do a
        # request for an up-to-date exchange rate.
        if not rate:
            url = self.url.format(transaction, payment)
            log.debug('Request url: {}'.format(url))

            r = requests.get(url)
            self.dump_http_response(r)

            # TODO:2014-10-23:einar: provide better user feedback.
            # Should probably provide some sort of 'contact developer'
            # functionality is implemented.
            if r.status_code != 200:
                raise APIError('Unknown API error happend.', self.id_)

            rate = r.text

            try:
                rate = float(rate)
            except ValueError:
                raise APIError(rate, self.id_)

            self.save_cache(transaction, payment, rate)

        return rate


register_api_provider(Yahoo.id_, Yahoo)


class ExchangeRateAPI(APIProvider):
    id_ = 'exchangerate-api.com'
    url = 'http://www.exchangerate-api.com/{}/{}?k={}'

    def __init__(self, api_key):
        APIProvider.__init__(self, api_key)
        self.cache_file = get_cache_file(self.id_)

    def get_exchange_rate(self, transaction, payment):
        self.load_cache()

        rate = None
        if transaction in self.cache:
            data = self.cache[transaction].get(payment, None)
            if data and not cache_has_expired(data.get('timestamp')):
                rate = data.get('rate')

        if not rate:
            url = self.url.format(transaction, payment, self.api_key)
            log.debug('Request url: {}'.format(url))

            r = requests.get(url)
            self.dump_http_response(r)

            rate = r.text

            try:
                rate = float(rate)
            except ValueError as e:
                raise APIError(e, self.id_)

            if rate == -1:
                raise APIError('Invalid amount used')
            if rate == -2:
                raise APIError('Invalid currency code: {} -> {}'
                               .format(transaction, payment))
            if rate == -3:
                raise APIError('Invalid API key: {}'.format(self.api_key))
            if rate == -4:
                raise APIError('API query limit reached')
            if rate == -5:
                raise APIError('Unresolved IP address used')

            self.save_cache(transaction, payment, rate)

        return rate


register_api_provider(ExchangeRateAPI.id_, ExchangeRateAPI, ['api_key'])


class RateExchange(APIProvider):
    id_ = 'rate-exchange.appspot.com'
    url = 'http://rate-exchange.appspot.com/currency?from={}&to={}'

    def get_exchange_rate(self, transaction, payment):
        url = self.url.format(transaction, payment)
        log.debug('Request url: {}'.format(url))
        res = urllib.request.urlopen(url).read()

        # Post process JSON response
        res = json.loads(res.decode('utf-8'))
        log.debug('Got json response: {}'.format(res))

        try:
            rate = float(res['rate'])
        except KeyError as ke:
            log.error(ke)
            raise APIError('Unable to extract rate key from json response')
        except ValueError as ve:
            log.error(ve)
            raise APIError('Unable to convert exchange rate to float')

        return rate


register_api_provider(RateExchange.id_, RateExchange)


class OpenExchangeRates(APIProvider):
    id_ = 'openexchangerates.org'
    url = 'http://openexchangerates.org/api/latest.json?app_id={}'

    def __init__(self, api_key):
        APIProvider.__init__(self, api_key)
        self.cache = {}
        self.cache_file = get_cache_file(self.id_)
        # TODO:2014-10-22:einar: refactor initial cache loading
        if os.path.isfile(self.cache_file):
            with open(self.cache_file) as f:
                self.cache = json.load(f)

    def get_exchange_rate(self, transaction, payment):
        """Calculates the exchange rate between a transaction currency
        and a payment currency, relative to a given base currency.

        :param transaction: transaction (from) currency.
        :param payment: payment (to) currency

        :returns: the exchange rate for the given currency pair.
        """
        self.load_cache()

        base = self.cache.get('base')
        rates = self.cache.get('rates')
        # Since no APIError is raied, we can assume that both currency
        # codes are valid.
        t_rate = rates.get(transaction)
        p_rate = rates.get(payment)
        log.debug('Using base currency: {}'.format(base))
        log.debug('Calculation currency pair: {}/{} '
                  .format(transaction, payment))

        if transaction == base:
            log.debug('Transaction currency ({}) == base currency ({})'
                      .format(transaction, base))
            return p_rate

        if payment == base:
            log.debug('Payment currency ({}) == base currency ({})'
                      .format(payment, base))
            return 1 / t_rate

        log.debug('1 {} == {} {}'.format(base, t_rate, transaction))
        log.debug('1 {} == {} {}'.format(base, p_rate, payment))
        return p_rate * (1 / t_rate)

    def save_cache(self, base, rates, etag, last_modified):
        """Save exchange rates as local cache.

        :param base: the base currency for the exchange rates
        :param rates: the exchange rates
        :param etag: doubleqouted identifier
        :param last_modified: date string
        """
        self.cache = {
            'etag': etag,
            'last_modified': last_modified,
            'base': base,
            'rates': rates,
            'timestamp': time.time()
        }
        with open(self.cache_file, 'w') as f:
            f.write(json.dumps(self.cache))
        log.info('Saved cache for {}'.format(self.id_))

    def load_cache(self):
        url = self.url.format(self.api_key)
        if not self.cache:
            # Do a regular request for latest currencies and save cache
            status_code, data = self._do_request(url)
            self.save_cache(*data)
        else:
            # Check if our cache is up-to-date
            if cache_has_expired(self.cache.get('timestamp')):
                headers = {
                    'If-None-Match': "{}".format(self.cache.get('etag')),
                    'If-Modified-Since': self.cache.get('last_modified'),
                }

                log.info('Checking cache for "{}"'.format(self.id_))
                status_code, data = self._do_request(url, headers=headers)
                if status_code == 304:
                    log.info('Cache is up-to-date')
                else:
                    # TODO:2014-10-22:einar: safe to assume status code 200?
                    log.info('Cache is out-of-date')
                    self.save_cache(*data)
            else:
                log.info('Current cache has not expired')

    def _do_request(self, url, headers={}):
        """Runs the actual HTTP request, and handles API errors.

        :param url: the request url
        :param headers: additional request headers

        :returns: on success the status code, base currency, exchange
            rates, etag and the last modified is returned, else an
            `APIError` is raised.
        """
        log.debug('Request url: {}'.format(url))
        r = requests.get(url, headers=headers)
        status_code = r.status_code

        self.dump_http_response(r)

        if status_code == 404:
            raise APIError('Non-existent resource requested', self.id_)
        if status_code == 401:
            message = r.json().get('message')
            if message in ['missing_appid_', 'invalid_appid_']:
                raise APIError('Invalid API key: {}'.format(self.api_key),
                               self.id_)
            if message == 'not_allowed':
                raise APIError('Not allowed to access requested feature')
            # TODO:2014-10-22:einar: provide an else cause here?
        if status_code == 429:
            raise APIError('Access restricted for over-use', self.id_)
        if status_code == 403:
            # TODO:2014-10-22:einar: use 'description' for better feedback
            raise APIError('Access restricted', self.id_)
        if status_code == 400:
            raise APIError('Invalid base currency', self.id_)

        if status_code == 200 or status_code == 304:
            # Only return what we care about
            return status_code, (r.json().get('base'),
                                 r.json().get('rates'),
                                 r.headers.get('etag'),
                                 r.headers.get('last_modified'))
        else:
            # TODO:2014-10-22:einar: provide better user feedback.
            # Should probably provide some sort of 'contact developer'
            # functionality is implemented.
            raise APIError('Received unexpected status code: {}'
                           .format(status_code), self.id_)


register_api_provider(OpenExchangeRates.id_, OpenExchangeRates, ['api_key'])
