import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cosine-crypto",
    version="0.1.39",
    author="Oladotun Rominiyi",
    author_email="dotun@voxex.io",
    description="A modular open source cryptocurrency trading algo framework.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oladotunr/cosine",
    packages=setuptools.find_packages(exclude=['contrib', 'docs', 'tests*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords='cryptocurrency algo trading blockex',
    project_urls={
        'Documentation': 'https://github.com/oladotunr/cosine',
        'Source': 'https://github.com/oladotunr/cosine',
    },
    package_data={
        'cosine': ['config.yaml.example'],
    },
)

