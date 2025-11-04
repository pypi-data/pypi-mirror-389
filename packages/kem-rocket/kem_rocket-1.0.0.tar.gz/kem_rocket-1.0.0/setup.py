from setuptools import setup, find_packages

setup(
    name='kem-rocket',
    version='1.0.0',
    author='Kambouz Nouha',
    author_email='kambouz907@gmail.com',
    packages=find_packages(),
    url='https://pypi.org/project/my_regression/',
    license='MIT',
    description='A simple linear regression package implemented from scratch.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=['numpy'],
)