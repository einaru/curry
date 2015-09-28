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
import time
from requests.exceptions import RequestException

from curry.config import config

log = logging.getLogger(__name__)

Providers = {}
"""A dictionary containing all available API providers."""

START_ENUMERATE_ON = 1


def register_api_provider(api, klass, requires=[]):
    Providers[api] = {'klass': klass, 'requires': requires}


def _emphasis(text):
    """Wrap text in terminal escape codes for bold text."""
    return '\033[1m{}\033[0m'.format(text)


def list_api_providers():
    """Print an enumerated sorted list of available API providers."""
    print('Available API providers:')
    default_api = config.get('api')
    for id_, api in enumerate(sorted(Providers.keys()), START_ENUMERATE_ON):
        requires = ', '.join(Providers[api].get('requires', []))
        if api == default_api or id_ == default_api:
            api = _emphasis(api + '*')
        output = '{:>4} {}'.format('({})'.format(id_), api)
        if len(requires) > 0:
            output = '{} (requires: {})'.format(output, requires)
        print(output)


def get_api_provider(api):
    """Get a registered API provider either by the registred API name,
    or by the enumerated id shown when `list_api_providers` is called.
    """
    try:
        api = sorted(Providers.keys())[int(api) - START_ENUMERATE_ON]
    except ValueError:
        pass

    if api not in Providers:
        raise APIError('Unknown API provider: {}'.format(api))

    return Providers[api]


def cache_has_expired(timestamp):
    """Check the timestamp of local cache has expired according to
    the configured cache_timeout.

    :param timestamp: timestamp of the local cache.

    :returns: True if the cache has expired, False otherwise.
    """
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
        provider = get_api_provider(api)

        if self.api:
            log.info('Switching API provider: {} -> {}'
                     .format(self.api.id_, api))

        self.api = provider['klass'](**kwargs)

    def get_exchange_rate(self, transaction, payment):
        """Get the exchange rate for a currency pair (transaction
        currency -> payment currency).

        :param transaction: transaction (from) currency.
        :param payment: payment (to) currency.

        :returns: the exchange rate or raises an APIError.
        """
        if not self.api:
            raise APIError('No API provider is set!')

        transaction, payment = transaction.upper(), payment.upper()
        log.info('Using API provider: {}'.format(self.api.id_))

        rate = -1
        try:
            rate = self.api.get_exchange_rate(transaction, payment)
        # XXX:2014-10-22:einar: do HTTP error handling more granular?
        except RequestException as e:
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

    def __init__(self, api_key=None, refresh_cache=False):
        self.api_key = api_key
        self.cache = {}
        self.refresh_cache = refresh_cache

    def get_exchange_rate(self, transaction, payment):
        """Must be implemented in every subclass."""

    def get_exchange_rate_from_cache(self, transaction, payment):
        """Try to get the exchange rate from cache.

        :param transaction: the transaction (from) currency.
        :param payment: the payment (to) currency.

        :returns: the exchange rate, if found and the cache timeout is
            not reached, None otherwise.
        """
        self.load_cache()
        rate = None
        if not self.refresh_cache and transaction in self.cache:
            data = self.cache[transaction].get(payment)
            if data and not cache_has_expired(data.get('timestamp')):
                rate = data.get('rate')
        return rate

    def save_cache(self, transaction, payment, rate):
        """Generic caching for API providers where a request is needed
        for every currency pair. The exchange rate for a currency pair
        (transaction currency and payment currency) is saved together
        with a timestamp.

        :param transaction: the transaction (from) currency.
        :param payment: the payment (to) currency.
        :param rate: the exchange rate for the currency pair.
        """
        if not hasattr(self, 'cache_file'):
            log.warn('Trying to save cache, but no cache_file is declared')
            return

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

        log.info('Saving cache.')
        with open(self.cache_file, 'w') as f:
            f.write(json.dumps(self.cache))

    def load_cache(self):
        """Load saved cache from disk.

        :returns: True if the cache file is loaded, False if its not,
            and None if no cache_file attribute is declared.
        """
        if not hasattr(self, 'cache_file'):
            log.warn('Trying to load cache, but no cache_file is declared')
            return

        if os.path.isfile(self.cache_file):
            log.info('Loading cache.')
            with open(self.cache_file) as f:
                self.cache = json.load(f)

    def dump_http_response(self, response):
        log.debug('*** Start: HTTP Response DUMP ***')
        log.debug('  Status code: {}'.format(response.status_code))
        log.debug('  Headers:')
        for k, v in response.headers.items():
            log.debug('    {}: {}'.format(k, v))
        log.debug('  Content:')
        log.debug('    {}'.format(response.content))
        log.debug('*** End ***')


# Loads and registers API providers
from curry.api.providers import *
