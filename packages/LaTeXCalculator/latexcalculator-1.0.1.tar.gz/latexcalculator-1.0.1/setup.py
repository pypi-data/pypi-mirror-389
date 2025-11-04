from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='LaTeXCalculator',
    version='1.0.1',
    author='Zhu Chongjing',
    author_email='zhuchongjing_pypi@163.com',
    description='A Python package for performing mathematical calculations using LaTeX syntax.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'latexcalc=LaTeXCalculator.interactive_calculator:interactive_calculator',
        ],
    },
    install_requires=[
        'sympy>=1.13.2',
        'rich>=14.2.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)