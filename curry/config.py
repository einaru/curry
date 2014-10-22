"""
    Curry - configuration
    ~~~~~~~~~~~~~~~~~~~~~

    Copyright: (c) 2014 Einar Uvsløkk
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
    cache_path = os.path.join(os.path.expanduser('~/.cache'), prog_name)

__all__ = ['Config']

config_file = os.path.join(config_path, 'config.ini')

log = logging.getLogger(__name__)


class Config:
    DEFAULTS = {'curry': {'api': 'finance.yahoo.com'}}

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read_dict(self.DEFAULTS)
        if os.path.exists(config_file):
            self.config.read(config_file)

    def get(self, key, val=None, section='curry'):
        if section not in self.config:
            return val
        return self.config[section].get(key, val)

    def set(self, key, val, section='curry'):
        if not val:
            log.warn('skipping {}: {} ({})'.format(key, val, type(val)))
        else:
            if section not in self.config:
                self.config.add_section(section)
            self.config.set(section, key, val)

    def save(self):
        with open(config_file, 'w') as f:
            self.config.write(f)
