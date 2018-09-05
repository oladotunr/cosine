import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cosine-crypto",
    version="0.1.0",
    author="Oladotun Rominiyi",
    author_email="dotun@voxex.io",
    description="A modular open source cryptocurrency trading algo framework.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oladotunr/cosine",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords='cryptocurrency algo trading blockex',
    project_urls={
        'Documentation': 'https://packaging.python.org/tutorials/distributing-packages/',
        'Funding': 'https://donate.pypi.org',
        'Say Thanks!': 'http://saythanks.io/to/example',
        'Source': 'https://github.com/pypa/sampleproject/',
        'Tracker': 'https://github.com/pypa/sampleproject/issues',
    },
)

