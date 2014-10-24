"""
    Curry
    ~~~~~

    API provider for: rate-exchange.appspot.com

    Copyright: (c) 2014 Einar Uvsløkk
    License: GNU General Public License (GPL) version 3 or later
"""
import logging
import requests

from curry.config import get_cache_file
from curry.api import APIProvider, APIError, register_api_provider

log = logging.getLogger(__name__)


class RateExchange(APIProvider):
    id_ = 'rate-exchange.appspot.com'
    url = 'http://rate-exchange.appspot.com/currency?from={}&to={}'

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
            url = self.url.format(transaction, payment)
            log.debug('Request url: {}'.format(url))

            r = requests.get(url)
            self.dump_http_response(r)

            if r.status_code == 503:
                # FIXME:2014-10-23:einar: Copy-paste of msg from HTML response
                raise APIError('Application is temporarily over its serving '
                               'quota. Please try again later.', self.id_)

            try:
                rate = r.json().get('rate')
            except KeyError as ke:
                log.error(ke)
                raise APIError('Unable to extract rate key from json response')
            except ValueError as ve:
                log.error(ve)
                raise APIError('Unable to convert exchange rate to float')

        return rate


register_api_provider(RateExchange.id_, RateExchange)
