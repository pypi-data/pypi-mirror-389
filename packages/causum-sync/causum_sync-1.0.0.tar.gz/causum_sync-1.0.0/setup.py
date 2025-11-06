from setuptools import setup, find_packages

setup(
    name="causum-sync",
    version="1.0.0",
    author="Causum™ Analytics",
    author_email="info@causum.ai",
    description="Local connector runner that verifies, migrates, and loads data to your analytics database.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://gitlab.com/causum/causum-sync",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "psycopg2-binary>=2.9.0",
        "colorama>=0.4.6",
        "tqdm>=4.66,<5.0",
    ],
    entry_points={
        "console_scripts": [
            "causum-sync=cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
