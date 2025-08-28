from setuptools import setup, find_packages

setup(
    name="switch-inventory-tool",
    version="0.1.0",
    description="Network Switch Inventory Management Tool",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.3.0",
        "openpyxl>=3.0.7",
        "PyYAML>=5.4.0",
        "pytest>=6.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "switch-inventory=main:main",
        ],
    },
)
