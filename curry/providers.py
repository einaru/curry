"""
    Curry - Exchange-rate API providers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Copyright: (c) 2014 Einar Uvsløkk
"""
import json
import logging
import urllib.request

log = logging.getLogger(__name__)

# Available API providers
Providers = {}


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


class Provider:
    """Main interface for the providers."""

    def __init__(self, **kwargs):
        self.api = None
        self.use_api(**kwargs)

    def use_api(self, **kwargs):
        assert 'api' in kwargs
        api = kwargs.pop('api')
        log.debug('trying to use api: {}'.format(api))
        if api not in Providers:
            raise ApiError('Unknown API provider: {}'.format(api))

        if self.api:
            log.info('switching API provider: {} -> {}'.format(self.api, api))

        self.api = Providers[api]['class'](**kwargs)

    def get_exchange_rate(self, _from, to):
        if not self.api:
            raise ApiError('No Api provider is set!')

        return self.api.get_exchange_rate(_from, to)


class ApiError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'ApiError: {}'.format(self.message)


class ProviderApi:
    """Super class for API providers."""

    def __init__(self, api_key=None):
        self.api_key = api_key

    def get_exchange_rate(self, _from, to):
        """Must be implemented in every subclass."""


class Yahoo(ProviderApi):
    url = 'http://download.finance.yahoo.com/d/quotes.csv?s={f}{t}=X&f=l1&e=.cs'

    def get_exchange_rate(self, _from, to):
        req_url = self.url.format(f=_from, t=to)
        log.debug('request url: {}'.format(req_url))

        # FIXME:2014-10-21:einar: response value is of type 'bytes'
        res = urllib.request.urlopen(req_url.format(_from, to)).read()
        log.debug('got response: {}'.format(res))

        try:
            rate = float(res)
        except ValueError as e:
            log.error(e)
            raise ApiError(6, 'Unkown error occured')

        # TODO:2014-10-21:einar: add better error handling for yahoo api
        return rate


register_api_provider('finance.yahoo.com', Yahoo)


class ExchangeRateApi(ProviderApi):

    url = 'http://www.exchangerate-api.com/{f}/{t}?k={k}'

    def get_exchange_rate(self, _from, to):
        req_url = self.url.format(f=_from, t=to, k=self.api_key)
        log.debug('request url: {}'.format(req_url))
        res = urllib.request.urlopen(req_url).read()

        try:
            rate = float(res)
        except ValueError as e:
            log.error(e)

        # FIXME:2014-10-21:einar: update API error handling
        if rate == -1:
            raise ApiError('Invalid amount used')
        if rate == -2:
            raise ApiError('Invalid currency code: {} -> {}'.format(_from, to))
        if rate == -3:
            raise ApiError('Invalid API key: {}'.format(self.api_key))
        if rate == -4:
            raise ApiError('API query limit reached')
        if rate == -5:
            raise ApiError('Unresolved IP address used')

        return rate


register_api_provider('exchangerate-api.com', ExchangeRateApi, ['api_key'])


class RateExchange(ProviderApi):
    url = 'http://rate-exchange.appspot.com/currency?from={f}&to={t}'

    def get_exchange_rate(self, _from, to):
        req_url = self.url.format(f=_from, t=to)
        log.debug('request url: {}'.format(req_url))
        json_res = urllib.request.urlopen(req_url).read()

        # Post process JSON response
        # FIXED:2014-10-21:einar: response value is of type 'bytes'
        res = json.loads(json_res.decode('utf-8'))
        log.debug('got json response: {}'.format(res))

        try:
            rate = float(res['rate'])
        except KeyError as ke:
            log.error(ke)
            raise ApiError('Unable to extract rate key from json response')
        except ValueError as ve:
            log.error(ve)
            raise ApiError('Unable to convert response rate to float')

        return rate


register_api_provider('rate-exchange.appspot.com', RateExchange)
