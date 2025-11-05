from setuptools import setup, find_packages

setup(
    name="fastfeatures",
    version="0.1.4",
    description="Modular features discovery system for FastAPI projects.",
    author="Yuri Seki",
    author_email="yuriseki@gmail.com",
    url="https://github.com/yuriseki/fastfeatures",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.118.3,<0.119.0",
        "sqlalchemy>=2.0.44,<3.0.0",
        "sqlmodel>=0.0.27,<0.0.28",
        "click>=8.1.7,<9.0.0",
        "setuptools>=69.0.3,<70.0.0",
        "python-dotenv>=1.0.0,<2.0.0",
        "alembic>=1.17.1,<2.0.0",
        "uvicorn>=0.38.0,<0.39.0",
        "pydantic-settings>=2.11.0,<3.0.0",
        "aiosqlite>=0.21.0,<0.22.0",
        "asyncpg>=0.30.0,<0.31.0",
    ],
    entry_points={
        "console_scripts": [
            "fastfeatures-scaffold=fastfeatures.core.generate_project_scaffolding:generate_project_scaffolding_cli",
            "fastfeatures-settings=fastfeatures.core.generate_settings:generate_settings_cli",
            "fastfeatures-feature=fastfeatures.core.generate_feature:generate_feature_cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    license="MIT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
