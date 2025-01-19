from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='FlightScrapper',
    version='0.1.0',  # Update this with your version
    author='Your Name',
    author_email='your.email@example.com',
    description='A FastAPI application that scrapes and tracks flight information',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/your-username/FlightScrapper',  # Replace with your repository URL
    packages=find_packages(),
    install_requires=[
        'fastapi==0.95.0',
        'pydantic==1.10.7',
        'requests==2.28.1',
        'beautifulsoup4==4.11.1',
        'sqlalchemy==1.4.46',
        'pytest==7.2.0',
        'uvicorn[standard]==0.20.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # or whatever license you're using
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'run_flight_scrapper=main:run',  # Assuming you have a function named 'run' in 'main.py'
        ],
    },
)