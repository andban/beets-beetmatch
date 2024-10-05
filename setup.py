import pathlib

from setuptools import setup, find_packages

PACKAGE_DIR = pathlib.Path(__file__).parent
README_TXT = (PACKAGE_DIR / "README.md").read_text()

setup(
    name='beets-beetmatch',
    version='0.1.0',
    description='beets plugin for generating playlists by matching songs that have similar properties',
    long_description=README_TXT,
    long_description_content_type='text/markdown',
    author='Andreas Bannach',
    author_email='andreas@borntohula.de',
    url='https://github.com/andban/beets-beetmatch',
    license='MIT',
    platforms='ALL',

    test_suite='test',
    packages=find_packages(exclude=['ez_setup', 'test', 'test.*']),
    include_package_data=True,

    python_requires='>=3.7',
    install_requires=[
        'beets>=1.6.0',
    ],

    extras_require={
        'test': [
            'coverage'
        ]
    },

    classifiers=[
        'Topic :: Multimedia :: Sound/Audio',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',

    ]
)
