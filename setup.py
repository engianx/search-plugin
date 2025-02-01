from setuptools import setup, find_packages

setup(
    name="search",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "scrapy",
        "pyyaml",
        "click",  # for CLI
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'search=search:main',
        ],
    },
)