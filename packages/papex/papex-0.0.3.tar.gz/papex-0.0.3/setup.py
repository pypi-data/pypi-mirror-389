from setuptools import setup, find_packages

long_description=open("README.md", encoding="utf-8").read()
long_description_content_type="text/markdown"

setup(
    name="papex",
    version="0.0.3",
    description="A library for fetching and normalizing academic papers from various providers (Elsevier, arXiv, PRISM, etc.)",
    #long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="maryamSayagh",
    author_email="maryamsayagho@gmail.com",
    url="https://github.com/maryamSayagh/PapEx",
    packages=find_packages(),
    install_requires=( "requests>=2.25.1",
        "orjson>=3.6.4",
        "lxml>=4.6.3",
        "arxiv>=1.4.8",
                       ),
    python_requires=">=3.7",
    classifiers=[
        #"Programming Language :: Python :: 3",
        #"License :: OSI Approved :: MIT License",
        #"Operating System :: OS Independent",
    ])
