from setuptools import setup, find_packages

setup(
    name="rewind",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pillow",
        "pytesseract",
        "pyyaml",
        "numpy",
        "python-Levenshtein",
        "scipy",
    ],
    entry_points={
        "console_scripts": [
            "rewind=rewind.rewind:main",
        ],
    },
)
