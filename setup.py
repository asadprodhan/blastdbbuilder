from setuptools import setup, find_packages

setup(
    name="blastdbbuilder",
    version="1.0.0",
    author="Asad Prodhan",
    author_email="prodhan82@gmail.com",
    description="Automated genome downloader, concatenator, and BLAST database builder",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    package_data={"blastdbbuilder": ["scripts/*", "containers/*"]},
    entry_points={
        "console_scripts": [
            "blastdbbuilder=blastdbbuilder.cli:main",
        ],
    },
    python_requires=">=3.8",
    license="MIT",
    url="https://github.com/AsadProdhan/blastdbbuilder",
)
