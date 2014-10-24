"""
    Curry
    ~~~~~

    API provider for: finance.yahoo.com

    Copyright: (c) 2014 Einar Uvsløkk
    License: GNU General Public License (GPL) version 3 or later
"""
import logging
import requests

from curry.config import get_cache_file
from curry.api import APIProvider, APIError, register_api_provider

log = logging.getLogger(__name__)


class Yahoo(APIProvider):
    id_ = 'finance.yahoo.com'
    url = 'http://download.finance.yahoo.com/d/quotes.csv?s={}{}=X&f=l1'

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
