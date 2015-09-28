# Curry

A command-line currency converter.

Curry is able to get exchange rates from the following API providers:

| Name                 | id                        |
| -------------------  | ------------------------- |
| Yahoo                | finance.yahoo.com         |
| Exchang Rate API¹    | exchangerate-api.com      |
| Rate Exchange        | rate-exchange.appspot.com |
| Open Exchange Rates¹ | openexchangerates.org     |
| Oanda                | oanda.com                 |

<small>
¹ requires an external `api key`
</small>


## Dependencies

- [Python](https://www.python.org) 3.x
- [Python-Requests](http://docs.python-requests.org/en/latest/)
- [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/) 4


## Install

``` bash
$ curl -L  http://github.com/einaru/curry/archive/v0.5.1.tar.gz | tar xz
$ cd curry-v0.5.1
$ sudo python3 setup.py install
```

or

```bash
$ git clone https://github.com/einaru/curry
$ cd curry
$ sudo python3 setup.py install
```

or if you're on [Arch Linux](https://www.archlinux.org)

``` bash
$ wget https://raw.githubusercontent.com/einaru/curry/master/arch/PKGBUILD
$ updpkgsums
$ makepkg
$ sudo pacman -U python-curry-*.tar.xz
```


## License

```
Copyright (c) 2014 Einar Uvsløkk

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
