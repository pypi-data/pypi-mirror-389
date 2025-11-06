from setuptools import setup, find_packages

setup(
    name="crekai-verify",
    version="1.0.0",
    author="Vishal",
    author_email="realvixhal@gmail.com",
    description="Universal CrekAI Verification Tool for Colab",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/thevixhal/crekai-verify",  # optional
    packages=find_packages(),
    install_requires=[
        "requests>=2.20.0"
    ],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
