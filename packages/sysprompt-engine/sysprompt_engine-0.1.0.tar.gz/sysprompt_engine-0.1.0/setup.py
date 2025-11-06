from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sysprompt-engine",
    version="0.1.0",
    author="Salahuddin Yousaf",  # TODO: Update with your name
    author_email="salahuddiny8@gmail.com",  # TODO: Update with your email
    description="A flexible system prompt creator with version control and validation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Salahuddin-Yousaf12/promptengine",  # TODO: Update with your GitHub repo URL
    project_urls={
        "Bug Reports": "https://github.com/Salahuddin-Yousaf12/promptengine/issues",
        "Source": "https://github.com/Salahuddin-Yousaf12/promptengine",
        "Documentation": "https://github.com/Salahuddin-Yousaf12/promptengine#readme",
    },
    packages=find_packages(),
    keywords="prompt, ai, llm, prompt-engineering, template, version-control",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "jinja2>=3.0.0",
        "pyyaml>=6.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
)
