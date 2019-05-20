from setuptools import setup, find_packages

setup(
    name='mercator',
    version='3.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mercator = mercator.__main__:main'
        ]
    }
)