"""
    Curry
    ~~~~~

    Configuration

    Copyright: (c) 2014 Einar Uvsløkk
    License: GNU General Public License (GPL) version 3 or later
"""
import os
import logging
import configparser

from curry import prog_name

try:
    from xdg import BaseDirectory
    config_path = BaseDirectory.save_config_path(prog_name)
    cache_path = BaseDirectory.save_cache_path(prog_name)
except:
    config_path = os.path.join(os.path.expanduser('~/.config'), prog_name)
    if not os.path.isdir(config_path):
        os.makedirs(config_path)
    cache_path = os.path.join(os.path.expanduser('~/.cache'), prog_name)
    if not os.path.isdir(cache_path):
        os.makedirs(cache_path)

__all__ = ['config', 'get_cache_file']

config_file = os.path.join(config_path, 'config.ini')

log = logging.getLogger(__name__)


def get_cache_file(filename):
    return os.path.join(cache_path, filename)


class Config:
    """A simple wrapper for `configparser.ConfigParser`, implemented as
    a Singleton [1]_.

    .. [1]: http://goo.gl/pVpkxe
    """
    DEFAULTS = {
        'curry': {
            'api': 'finance.yahoo.com',
            'cache_timeout': 60 * 60 * 12,
        }
    }

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'self'):
            cls.self = object.__new__(cls)
            cls.self.config = configparser.ConfigParser()
            cls.self.config.read_dict(Config.DEFAULTS)
            if os.path.exists(config_file):
                cls.self.config.read(config_file)
        return cls.self

    def default_api(self):
        return self.DEFAULTS['curry']['api']

    def default_cache_timeout(self):
        return self.DEFAULTS['curry']['cache_timeout']

    def get(self, key, val=None, section='curry'):
        if section not in self.config:
            return val
        v = self.config[section].get(key, val)
        try:
            return float(v)
        except:
            return v

    def set(self, key, val, section='curry'):
        if not val:
            log.debug('Skipping {}: {} ({})'.format(key, val, type(val)))
        else:
            if section not in self.config:
                self.config.add_section(section)
            self.config.set(section, key, val)

    def save(self):
        log.info('Saving config file: {}'.format(config_file))
        with open(config_file, 'w') as f:
            self.config.write(f)


config = Config()
