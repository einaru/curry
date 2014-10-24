"""
    Curry
    ~~~~~

    API provider for: oanda.com

    Copyright: (c) 2014 Einar Uvsløkk
    License: GNU General Public License (GPL) version 3 or later
"""
import os
import io
import csv
import time
import json
import logging
import requests

from bs4 import BeautifulSoup

from curry.config import get_cache_file
from curry.api import (APIProvider, APIError, register_api_provider,
                       cache_has_expired)

log = logging.getLogger(__name__)

base_currency = 'USD'
currencies = [
    'ADF', 'ADP', 'AED', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'AON', 'ARS',
    'ATS', 'AUD', 'AWG', 'AZM', 'AZN', 'BAM', 'BBD', 'BDT', 'BEF', 'BGN',
    'BHD', 'BIF', 'BMD', 'BND', 'BOB', 'BRL', 'BSD', 'BTN', 'BWP', 'BYR',
    'BZD', 'CAD', 'CDF', 'CHF', 'CLP', 'CNY', 'COP', 'CRC', 'CUC', 'CUP',
    'CVE', 'CYP', 'CZK', 'DEM', 'DJF', 'DKK', 'DOP', 'DZD', 'ECS', 'EEK',
    'EGP', 'ESP', 'ETB', 'EUR', 'FIM', 'FJD', 'FKP', 'FRF', 'GBP', 'GEL',
    'GHC', 'GHS', 'GIP', 'GMD', 'GNF', 'GRD', 'GTQ', 'GYD', 'HKD', 'HNL',
    'HRK', 'HTG', 'HUF', 'IDR', 'IEP', 'ILS', 'INR', 'IQD', 'IRR', 'ISK',
    'ITL', 'JMD', 'JOD', 'JPY', 'KES', 'KGS', 'KHR', 'KMF', 'KPW', 'KRW',
    'KWD', 'KYD', 'KZT', 'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LTL', 'LUF',
    'LVL', 'LYD', 'MAD', 'MDL', 'MGA', 'MGF', 'MKD', 'MMK', 'MNT', 'MOP',
    'MRO', 'MTL', 'MUR', 'MVR', 'MWK', 'MXN', 'MYR', 'MZM', 'MZN', 'NAD',
    'NGN', 'NIO', 'NLG', 'NOK', 'NPR', 'NZD', 'OMR', 'PAB', 'PEN', 'PGK',
    'PHP', 'PKR', 'PLN', 'PTE', 'PYG', 'QAR', 'ROL', 'RON', 'RSD', 'RUB',
    'RWF', 'SAR', 'SBD', 'SCR', 'SDD', 'SDG', 'SDP', 'SEK', 'SGD', 'SHP',
    'SIT', 'SKK', 'SLL', 'SOS', 'SRD', 'SRG', 'STD', 'SVC', 'SYP', 'SZL',
    'THB', 'TJS', 'TMM', 'TMT', 'TND', 'TOP', 'TRL', 'TRY', 'TTD', 'TWD',
    'TZS', 'UAH', 'UGX', 'USD', 'UYU', 'UZS', 'VEB', 'VEF', 'VND', 'VUV',
    'WST', 'XAF', 'XAG', 'XAU', 'XCD', 'XEU', 'XOF', 'XPD', 'XPF', 'XPT',
    'YER', 'YUN', 'ZAR', 'ZMK', 'ZMW', 'ZWD'
]


class Oanda(APIProvider):
    id_ = 'oanda.com'
    base_currency = 'USD'
    url = 'http://www.oanda.com/currency/table?date=10/24/14&' \
          'date_fmt=us&exch={}&sel_list={}&value=1&format=CSV&redirected=1'

    def __init__(self, **kwargs):
        APIProvider.__init__(self, **kwargs)
        self.cache_file = get_cache_file(self.id_)

    def get_exchange_rate(self, transaction, payment):
        self.load_cache()

        base = self.cache.get('base')
        rates = self.cache.get('rates')
        # TODO:2014-10-24:einar: take advantage of cached inverse rates

        t_rate = rates.get(transaction)
        p_rate = rates.get(payment)

        if transaction == base:
            return p_rate

        if payment == base:
            return 1 / t_rate

        return p_rate * (1 / t_rate)

    def save_cache(self, rates, inverse_rates):
        self.cache.update({
            'base': self.base_currency,
            'rates': rates,
            'inverse_rates': inverse_rates,
            'timestamp': time.time()
        })
        log.debug('Saving cache.')
        with open(self.cache_file, 'w') as f:
            f.write(json.dumps(self.cache))

    def load_cache(self):
        if os.path.isfile(self.cache_file):
            log.info('Loading cache from file.')
            with open(self.cache_file) as f:
                self.cache = json.load(f)

        # Incase of no cache, timestamp will be None
        timestamp = self.cache.get('timestamp')
        has_expired = not timestamp or cache_has_expired(timestamp)
        if not self.cache or self.refresh_cache or has_expired:
            url = self.url.format(self.base_currency, '_'.join(currencies))
            log.debug('Request url: {}'.format(url))

            r = requests.get(url)
            self.dump_http_response(r)

            if r.status_code == 200:
                data = self._parse_html(r.content)
                self.save_cache(*data)
            else:
                raise APIError('Unable to fetch data.', self.id_)

    def _parse_html(self, html):
        """Parse the return HTML document for exchange rate data.

        :param html: the HTML content to parse.

        :returns: two dictionaries (rates and inverse_rates), which
            contains exchange rates on success, or is empty otherwise.
        """
        soup = BeautifulSoup(html)
        content = soup.find(id='content_section').find('table').find('font')

        f = io.StringIO(content.text)
        reader = csv.reader(f)
        data = [row for row in reader if len(row) > 0][1:]

        assert len(data) > 0
        assert len(data[0]) == 4

        rates, inverse_rates = {}, {}
        for row in data:
            name, code, inverse, rate = row
            rates[code] = float(rate)
            inverse_rates[code] = float(inverse)

        return rates, inverse_rates


register_api_provider(Oanda.id_, Oanda)
