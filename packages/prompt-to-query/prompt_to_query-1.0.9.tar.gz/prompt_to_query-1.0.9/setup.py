from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent.parent.parent / "README.md"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "High-performance SDK to convert natural language prompts to MongoDB queries using AI"

setup(
    name="prompt-to-query",
    version="1.0.4",
    author="Dimar Borda",
    author_email="dimarborda@gmail.com",
    description="High-performance SDK to convert natural language prompts to MongoDB queries using AI (OpenAI GPT or Anthropic Claude)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dimarborda/prompt-to-query",
    project_urls={
        "Bug Tracker": "https://github.com/dimarborda/prompt-to-query/issues",
        "Documentation": "https://github.com/dimarborda/prompt-to-query#readme",
        "Source Code": "https://github.com/dimarborda/prompt-to-query",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
    ],
    keywords=[
        "mongodb", "query", "natural-language", "nlp", "ai", "llm",
        "openai", "gpt", "gpt-4", "anthropic", "claude",
        "database", "text-to-query", "prompt-engineering", "sdk"
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies needed - uses ctypes from stdlib
    ],
    package_data={
        "prompt_to_query": [
            "lib/*.so",
            "lib/*.dylib",
            "lib/*.dll",
        ],
    },
    include_package_data=True,
    zip_safe=False,  # Important for loading shared libraries
)
