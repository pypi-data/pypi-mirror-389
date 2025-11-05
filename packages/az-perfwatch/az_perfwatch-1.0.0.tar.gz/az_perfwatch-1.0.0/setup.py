from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="az-perfwatch",
    version="1.0.0",
    author="Shahabaz Alam",
    author_email="shahabazalam1@gmail.com",
    description="Production-ready performance monitoring library for Python web applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ShahabazAlam/az-perfwatch",
    project_urls={
        "Bug Reports": "https://github.com/ShahabazAlam/az-perfwatch/issues",
        "Source": "https://github.com/ShahabazAlam/az-perfwatch",
        "Documentation": "https://github.com/ShahabazAlam/az-perfwatch#readme",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.100.0",
        "flask>=2.3.2",
        "django>=4.2",
        "sqlalchemy>=2.0",
        "pymongo>=4.10.0",
        "requests>=2.31.0",
        "httpx>=0.24.0",
        "pydantic>=2.5.0",
        "rich>=13.4",
        "jinja2>=3.1",
        "uvicorn>=0.25.0",
        "toml>=0.10",
        "passlib[bcrypt]>=1.7.4",
        "typer>=0.9.0",
        "psycopg2-binary>=2.9.0",
        "mysql-connector-python>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=24.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "perfwatch=perfwatch.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "perfwatch": [
            "dashboard/templates/**/*",
            "dashboard/static/**/*",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Flask",
        "Framework :: FastAPI",
        "Operating System :: OS Independent",
    ],
    keywords="performance monitoring profiling django flask fastapi metrics",
    zip_safe=False,
)
