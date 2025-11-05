from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='investimentpy-dridev',
    version='1.0.2',
    packages=find_packages(),
    description='Uma biblioteca para análise de investimentos',
    author='Adriel Roque',
    author_email='adrielroquedev@gmail.com',
    url='https://github.com/drielDev/InvestPy',  
    license='MIT',  
    long_description=long_description,
    long_description_content_type='text/markdown' 
)