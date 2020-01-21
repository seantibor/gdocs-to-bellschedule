from setuptools import setup

setup(
    name='gdrive',
    version='0.2',
    py_modules=['gdrive'],
    install_requires=[
        'Click',
        'pygsheets',
        'pandas',
        'beautifulsoup4'
    ],
    entry_points='''
        [console_scripts]
        gdrive=gdrive:cli
    ''',
)