from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh.readlines()]

setup(
    name="mcp-registry",
    version="0.1.0",
    author="MCP Team",
    author_email="example@example.com",
    description="A high-performance, LLM-friendly Model Context Protocol registry server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mcp-registry",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/mcp-registry/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mcp-registry=mcp_registry.server:main",
        ],
    },
)
