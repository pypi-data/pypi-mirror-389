from setuptools import setup, find_packages

setup(
    name="ez-skelgen",
    version="0.1.2",
    author="y1cho-HIU",
    author_email="yongil4209@gmail.com",
    description="project skeleton generator with templates",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/y1cho-HIU/ez-skelgen",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.7",
    entry_points={
        "console_scripts":[
            "ez-skelgen=skelgen.main:main",
        ],
    },
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)