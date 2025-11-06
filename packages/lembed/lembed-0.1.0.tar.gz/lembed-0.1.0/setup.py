from setuptools import setup, find_packages

setup(
    name='lembed',
    version='0.1.0',
    description='Python extension to embed live webpages with PyQt6.',
    author='Shanveer Singh Sodha',
    packages=find_packages(),
    install_requires=[
        'PyQt6',
        'PyQt6-WebEngine',
    ],
    python_requires='>=3.6',
)
