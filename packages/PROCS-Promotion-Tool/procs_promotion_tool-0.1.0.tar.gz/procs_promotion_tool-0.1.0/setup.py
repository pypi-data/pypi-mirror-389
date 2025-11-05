from setuptools import setup, find_packages # type: ignore

setup(
    name="PROCS_Promotion_Tool",
    version="0.1.0",
    author="surapatsue",
    author_email="NAKARINSUE@outlook.com",
    description="Automated Excel & SQL Promotion Data Flow",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # "pandas>=1.5.0",
        # "openpyxl>=3.0.0",
        # "pyodbc>=4.0.0",
        # "tqdm",
        "SQLAlchemy==2.0.41",
        "pyodbc==5.2.0",
        "openpyxl==3.1.5",
        "pandas==2.3.0",
        "python-dotenv==1.1.1",
        "python-barcode==0.15.1",
        "pillow==11.3.0",
        "barcode",
        "watchdog==4.0.0",
        "pyinstaller==6.16.0",
        "requests==2.32.4",
        "tqdm==4.66.4"
    ],
    entry_points={
        "console_scripts": [
            "Promotion=Promotion_Counter.__main__:main",
            "RunPromotion=Promotion.__main__:main"
        ],
    },
    python_requires=">=3.9",
)
