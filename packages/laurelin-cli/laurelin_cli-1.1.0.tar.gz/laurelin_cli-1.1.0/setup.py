"""Setup configuration for Laurelin CLI."""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name='laurelin-cli',
    version='1.1.0',
    description='Terminal interface for Laurelin nuclear fusion chat platform',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Laurelin Inc.',
    author_email='support@laurelin-inc.com',
    url='https://laurelin-inc.com',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'click>=8.0.0',
        'requests>=2.28.0',
    ],
    entry_points={
        'console_scripts': [
            'laurelin=laurelin_cli.cli:main',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    keywords='laurelin nuclear fusion plasma chat cli terminal',
)
