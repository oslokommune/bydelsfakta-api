import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bydelsfakta-api",
    version="0.0.1",
    author="Origo Dataplattform",
    author_email="dataplattform@oslo.kommune.no",
    description="Lambda function fetch bydelsfaktas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.oslo.kommune.no/origodigi/bydelsfakta-api",
    packages=setuptools.find_packages(),
    install_requires=[
        "aws_xray_sdk>=2.7",
        "boto3",
        "requests",
    ],
)
