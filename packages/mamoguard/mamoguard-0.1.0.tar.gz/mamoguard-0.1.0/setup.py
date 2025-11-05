from setuptools import setup, find_packages

setup(
    name='mamoguard', 
    version='0.1.0',
    packages=['cybersec_scanner'],  
    install_requires=[
        'click>=8.0',
        'gitpython>=3.1.0',
        'pydantic>=2.0',
        'langchain-openai>=1.0.0',
        'python-dotenv>=1.0',
    ],
    entry_points={
        'console_scripts': [
            'mamoguard=cybersec_scanner.cli:scan', 
        ],
    },
)