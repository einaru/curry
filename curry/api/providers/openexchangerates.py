"""
    Curry
    ~~~~~

    API provider for: openexchangerates.org

    Copyright: (c) 2014 Einar Uvsløkk
    License: GNU General Public License (GPL) version 3 or later
"""
import os
import json
import time
import logging
import requests

from curry.config import get_cache_file
from curry.api import (APIProvider, APIError, register_api_provider,
                       cache_has_expired)

log = logging.getLogger(__name__)


class OpenExchangeRates(APIProvider):
    id_ = 'openexchangerates.org'
    url = 'http://openexchangerates.org/api/latest.json?app_id={}'

    def __init__(self, **kwargs):
        APIProvider.__init__(self, **kwargs)
        self.cache_file = get_cache_file(self.id_)

    def get_exchange_rate(self, transaction, payment):
        """Get the exchange rate for a currency pair (transaction
        currency -> payment currency).

        :param transaction: transaction (from) currency.
        :param payment: payment (to) currency.

        :returns: the exchange rate or raises an APIError.
        """
        self.load_cache()

        base = self.cache.get('base')
        rates = self.cache.get('rates')
        # Since no APIError is raised, we can assume that both currency
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
        """Override the parent class implementation to take advantage
        of the HTML headers that openexchangerates.org provides. All
        exchange rates relative to a base currency is saved, together
        with a timestamp, and the etag and last modified fields from the
        response headers.

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
        log.info('Saving cache.')
        with open(self.cache_file, 'w') as f:
            f.write(json.dumps(self.cache))

    def load_cache(self):
        """Override the parent class implementation, to take advantage
        of HTML headers that openexchangerates.org provides. Local cache
        is loaded if found, and updated if it is outdated.
        """
        if os.path.isfile(self.cache_file):
            log.info('Loading cache from file.')
            with open(self.cache_file) as f:
                self.cache = json.load(f)

        url = self.url.format(self.api_key)

        # Possible scenarios:
        # 1. cache is empty       => fetch new rates
        # 2. cache_refresh = True => check for updated rates
        # 3. cache has expired    => check for updated rates

        # Scenraio 1. Here we must fetch new rates wether cache_refresh
        # is True or False
        if not self.cache:
            status_code, data = self.do_request(url)
            self.save_cache(*data)
            return

        # Scenraio 2. and 3. Here we take advantage of the etag and last
        # modifed keys, stored in our local cache, to do a request for
        # rates only if our cache is outdated.
        timestamp = self.cache.get('timestamp')
        if self.refresh_cache or cache_has_expired(timestamp):
            headers = {
                'If-None-Match': "{}".format(self.cache.get('etag')),
                'If-Modified-Since': self.cache.get('last_modified'),
            }

            log.info('Requesting updated exchange rates')
            status_code, data = self.do_request(url, headers=headers)
            if status_code == 304:
                log.info('Local cache is up-to-date')
            else:
                # TODO:2014-10-22:einar: safe to assume status code 200?
                log.info('Local cache is outdated')
                self.save_cache(*data)

    def do_request(self, url, headers={}):
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
            # TODO:2014-10-22:einar: provide an else cause here?
            if message == 'not_allowed':
                raise APIError('Not allowed to access requested feature')
        if status_code == 429:
            raise APIError('Access restricted for over-use', self.id_)
        # TODO:2014-10-22:einar: use 'description' for better feedback
        if status_code == 403:
            raise APIError('Access restricted', self.id_)
        if status_code == 400:
            raise APIError('Invalid base currency', self.id_)

        if status_code == 200 or status_code == 304:
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
