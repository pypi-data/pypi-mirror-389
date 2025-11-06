from setuptools import setup, find_packages

# Read README for long description
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "RobinApi Framework - A comprehensive solution for LLM APIs and vector database management"

setup(
    name='robin_api',
    version='2.24',
    packages=find_packages(),
    description="RobinApi Framework - LLM API integration and vector database management",
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=False,
    install_requires=[
        'httpx',
        'pydantic',
        'distro',
        'validators',
        'pandas'
    ],
    python_requires='>=3.3',
    author='William Gomez',
    author_email='william.gomez712@gmail.com',
    url='https://github.com/williamgomez71/RobinApi',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)