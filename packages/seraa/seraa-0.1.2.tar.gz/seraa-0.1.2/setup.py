"""
SERAA Setup Configuration
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

setup(
    name="seraa",
    version="0.1.2",
    author="Theodore Park",
    author_email="theodore.jb.park@gmail.com.com",  
    description="Stochastic Emergent Reasoning Alignment Architecture - Ethical AI Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tpark216/seraa",  
    project_urls={
        "Bug Tracker": "https://github.com/tpark216/seraa/issues",
        "Documentation": "https://github.com/tpark216/seraa",
        "Source Code": "https://github.com/tpark216/seraa",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",  # For LLM integration (Ollama)
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-xdist>=3.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
        ],
        "llm-full": [
            "openai>=1.0.0",
            "anthropic>=0.7.0",
        ],
        "viz": [
            "matplotlib>=3.5.0",
            "numpy>=1.21.0",
        ],
        "all": [
            "openai>=1.0.0",
            "anthropic>=0.7.0",
            "matplotlib>=3.5.0",
            "numpy>=1.21.0",
        ]
    },
entry_points={
    "console_scripts": [
        "seraa-chat=seraa.cli.chat:main",
        "seraa-eval=seraa.cli.evaluate:main",
    ],
},

    keywords=[
        "ai-ethics",
        "responsible-ai",
        "ethical-ai",
        "agency-preservation",
        "digital-ethics",
        "moral-reasoning",
        "ai-alignment",
        "llm",
        "ethics-framework"
    ],
    include_package_data=True,
    zip_safe=False,
)
