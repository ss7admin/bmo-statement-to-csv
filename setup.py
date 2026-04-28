from setuptools import setup, find_packages

setup(
    name="bmo-statement-to-csv",
    version="0.1.0",
    description="Convert BMO bank statement PDFs to CSV",
    packages=find_packages(),
    install_requires=[
        "pdfplumber",
    ],
    entry_points={
        "console_scripts": [
            "bmo2csv=bmo_statement.cli:main",
        ],
    },
    python_requires=">=3.8",
)
