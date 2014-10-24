"""
    Curry
    ~~~~~

    API providers

    Copyright: (c) 2014 Einar Uvsløkk
    License: GNU General Public License (GPL) version 3 or later
"""
from .yahoo import Yahoo
from .rate_exchange import RateExchange
from .exchangerate_api import ExchangeRateAPI
from .openexchangerates import OpenExchangeRates

__all__ = ['Yahoo', 'RateExchange', 'ExchangeRateAPI', 'OpenExchangeRates']
