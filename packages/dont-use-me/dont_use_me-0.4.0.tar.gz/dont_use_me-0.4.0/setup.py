from setuptools import setup, find_packages
with open("README.md", "r") as fh:
    description = fh.read()
setup(
    name="dont_use_me",
    version="0.4.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "say-hello=dont_use_me.main:hello"
        ]
        },
    install_requires=[],   
    long_description=description,
    long_description_content_type="text/markdown"
)