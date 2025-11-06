from setuptools import setup

setup(
    name = 'python_requestr',
    packages = ['requestr',],
    install_requires=['requests', 'python-objectifier', 'beautifulsoup4', 'requests-futures'],
    version = '0.15',
    description = 'requestr',
    url = 'https://github.com/xjxckk/python-requestr/',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown'
    )