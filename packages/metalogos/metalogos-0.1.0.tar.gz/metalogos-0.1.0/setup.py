from setuptools import setup, find_packages

setup(
    name="metalogos",
    version="0.1.0",
    author="Ashar Nasir",
    author_email="asharnasir0800@example.com",
    description="A reflective Python library where logic meets longing — blending AI, philosophy, and aesthetics.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ashar0800/metalogos",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
)
