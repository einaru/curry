"""
    Curry
    ~~~~~

    API provider for: exchangerate-api.com

    Copyright: (c) 2014 Einar Uvsløkk
    License: GNU General Public License (GPL) version 3 or later
"""
import logging
import requests

from curry.config import get_cache_file
from curry.api import APIProvider, APIError, register_api_provider

log = logging.getLogger(__name__)


class ExchangeRateAPI(APIProvider):
    id_ = 'exchangerate-api.com'
    url = 'http://www.exchangerate-api.com/{}/{}?k={}'

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
        rate = self.get_exchange_rate_from_cache(transaction, payment)

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
