from setuptools import setup, find_packages




setup(
    name="defoldsdk",
    version="1.3.2",
    author="issam Mhadhbi",
    author_email="mhadhbixissam@gmail.com",
    description="Defold protobuff compiled to python package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/MhadhbiXissam/defoldsdk.git",
    packages=find_packages(),
    install_requires=[
        "protobuff","requests"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.8",
)
