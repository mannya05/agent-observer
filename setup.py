from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="agent-observer-ai",
    version="0.1.0",
    author="Manya",
    description="Real-time observability and auto-debugging toolkit for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mannya05/agent-observer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "dashboard": ["streamlit>=1.32.0", "pandas>=1.5.0"],
        "langchain": ["langchain>=0.1.0", "langchain-core>=0.1.0"],
    },
)
