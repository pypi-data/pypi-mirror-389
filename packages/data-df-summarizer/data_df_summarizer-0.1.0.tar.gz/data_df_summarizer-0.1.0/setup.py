from setuptools import setup, find_packages

setup(
    name="data_df_summarizer",
    version="0.1.0",
    author="anushhhka-jain",
    author_email="anushkaj2211@gmail.com",
    description="A simple DataFrame summarizer to get summary of huge datasets in just one line of code.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
