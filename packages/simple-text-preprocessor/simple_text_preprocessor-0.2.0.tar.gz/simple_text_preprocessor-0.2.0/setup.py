from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='simple-text-preprocessor',
    version='0.2.0',
    author='Rohan Mudrale',
    author_email='rohan.mudrale60@nmims.in',
    description='A single-function utility for flexible NLP text cleaning.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='',
    entry_points={
        "console_scripts": [
            "nlp = clean_text.main:clean_text"
        ]
    },  # <-- Make sure this comma is present
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires='>=3.7',
    install_requires=[
        'nltk',
    ],
)
