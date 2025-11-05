from setuptools import setup, find_packages

setup(
    name="trigdeg",              
    version="0.1.0",              
    packages=find_packages(),
    install_requires=[],           
    author="Saurabh Pal",
    author_email="spal18102001@gmail.com",
    description="Trigonometry functions using degrees (sin, cos, tan, cot, sec, cosec)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/saurabh18102001/TrigDeg/",  
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
