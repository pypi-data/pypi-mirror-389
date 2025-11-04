
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="abetworks-agentwork",
    version="1.0.0",
    author="Abetworks",
    author_email="contact@abetworks.in",
    description="SDK for building AI agents that integrate with Abetworks platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abetworks/abetworks-agentwork",
    project_urls={
        "Bug Tracker": "https://github.com/abetworks/abetworks-agentwork/issues",
        "Documentation": "https://docs.abetworks.in",
        "Source Code": "https://github.com/abetworks/abetworks-agentwork",
        "Website": "https://abetworks.in",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Flask",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "flask": ["flask>=2.3.0"],
        "fastapi": ["fastapi>=0.100.0", "uvicorn>=0.23.0"],
        "all": ["flask>=2.3.0", "fastapi>=0.100.0", "uvicorn>=0.23.0"],
    },
    keywords="ai agents automation abetworks sdk flask fastapi",
)
