from setuptools import setup, find_packages

setup(
    name="pdfmang",
    version="1.0.0",
    author="Yatin Annam",
    author_email="ninjayatin@gmail.com",
    description="A lightweight all-in-one PDF utility for merging, splitting, encrypting, compressing, and converting PDFs.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yatinannam/pdfmang",  # optional but recommended
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyPDF2",
        "pdf2image",
        "pdf2docx",
        "Pillow",
        "ttkthemes",
    ],
    entry_points={
        "console_scripts": [
            "pdfmang=pdfmang.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
