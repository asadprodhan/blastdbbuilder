from setuptools import setup, find_packages

setup(
    name="blastdbbuilder",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "blastdbbuilder=blastdbbuilder.cli:main",
        ],
    },
    install_requires=[
        # Python packages only, no Singularity or BLAST dependencies
    ],
    python_requires=">=3.8",
    include_package_data=True,
    description="Automated genome downloader, concatenator, and BLAST database builder",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AsadProdhan/blastdbbuilder",
    author="Asad Prodhan",
    author_email="prodhan82@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    package_data={
        "blastdbbuilder": ["scripts/*"],  # include your shell scripts
    },
)
