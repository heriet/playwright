from playwright import __version__


from setuptools import find_packages, setup


requires = [
    'Click',
    'future',
    'jinja2',
    'PyYAML',
    'sleety',
    ]

setup(
    name='playwright',
    description='playbook generator for ansible role nifcloud',
    author='heriet',
    author_email='heriet@heriet.info',
    url='https://github.com/heriet/playwright',
    packages=find_packages(exclude=["example", "test"]),
    version=__version__,
    include_package_data=True,
    package_date={
        '': [
            'playwright/templates/*.j2'
        ]
    },
    install_requires=requires,
    license='MIT',
    entry_points='''
        [console_scripts]
        playwright=playwright.cli:cli
    ''',
)
