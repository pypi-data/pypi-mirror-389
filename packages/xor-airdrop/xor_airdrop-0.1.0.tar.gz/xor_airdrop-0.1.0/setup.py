from setuptools import setup, find_packages

setup(
    name="xor-airdrop",
    version="0.1.0",
    author="ack",
    author_email="your.email@example.com",
    description="A short description",
#     long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/my_package",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.1",  # 依赖项
    ],
    extras_require={
        "dev": ["pytest>=6.0"],
    },
)
