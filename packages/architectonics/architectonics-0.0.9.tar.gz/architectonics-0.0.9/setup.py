# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['architectonics',
 'architectonics.config',
 'architectonics.models',
 'architectonics.repositories',
 'architectonics.schemas',
 'architectonics.services',
 'architectonics.views']

package_data = \
{'': ['*']}

install_requires = \
['SQLAlchemy==2.0.43',
 'aio-pika>=9.5.7,<10.0.0',
 'alembic==1.16.5',
 'asyncpg==0.30.0',
 'dotenv==0.9.9',
 'fastapi==0.116.1',
 'pydantic==2.11.7',
 'uvicorn==0.35.0']

setup_kwargs = {
    'name': 'architectonics',
    'version': '0.0.9',
    'description': '',
    'long_description': None,
    'author': 'kirshuvl',
    'author_email': 'kirshuvl@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.11,<4.0',
}


setup(**setup_kwargs)
