from setuptools import setup, find_packages

setup(
    name="akscmd",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "akscmd=akscmd.cli:main",
        ],
    },
    author="Amit Kumar Singh",
    author_email="aksmlibts@gmail.com",
    description="AI-powered terminal assistant",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
)
