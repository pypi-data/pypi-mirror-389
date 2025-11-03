from setuptools import setup, find_packages

setup(
    name='structuralpy',
    version='0.0.4',
    description='A library for analysis and design of structures based on NSCP 2015.',
    long_description=open('USAGE.md').read(),
    long_description_content_type='text/markdown',
    author='Jaydee Lucero',
    author_email='jaydee.lucero@gmail.com',
    packages=find_packages(),
    install_requires=[
        "pytest", "sympy"
    ],
    license='MIT',
    python_requires='>=3.7',
)