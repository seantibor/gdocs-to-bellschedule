from setuptools import setup

setup(
    name='gdocs_to_bell_schedule',
    version='0.1',
    py_modules=['gdrive'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        gdocs_to_bell_schedule=gdrive:add_schedule_from_url
    ''',
)