from setuptools import setup

setup(
    name="ccc",
    version="0.1",
    entry_points={
        "console_scripts": [
            "ccc = ccc_cli.cli:main",
        ],
    },
    install_requires=["requests"],
    python_requires=">=3.8",
)
