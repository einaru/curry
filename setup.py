import os
from setuptools import setup, find_packages

from curry import prog_name, version, author, author_email, description

here = os.path.abspath(os.path.dirname(__file__))

# Remember to adjust the number of lines that cover the desceription
N_LINES = 3
with open(os.path.join(here, 'README.md')) as f:
    long_description = ''.join([next(f) for i in range(N_LINES)])

setup(
    name=prog_name,
    version=version,
    description=description,
    long_description=long_description,
    url='http://github.com/einaru/curry',
    author=author,
    author_email=author_email,
    license='GPLv3+',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: X11 Applications :: Gnome',
        'Environment :: X11 Applications :: GTK',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)'
        'Operating System :: MacOSX',
        'Operating System :: POSIX',
        'Operating System :: UNIX',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
        'Topic :: Office/Business :: Financial',
    ],
    keywords='cli currency converter',
    packages=find_packages(exclude=[]),
    install_requires=[],
    data_files=[],
    entry_points={
        'console_scripts': [
            'curry=curry.cli:main'
        ],
    },
)
