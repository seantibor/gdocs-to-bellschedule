from setuptools import setup

setup(
    name='gdrive',
    version='0.1',
    py_modules=['gdrive'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        gdrive=gdrive:add_schedule_from_url
    ''',
)