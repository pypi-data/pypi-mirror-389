from setuptools import setup, find_packages

setup(
    name="sfn_db_query_builder",
    version="2.1",
    description="Simplify SQL queries across databases",
    author="Rajesh Darak",
    author_email="rajesh@stepfunction.ai",
    url="https://github.com/stepfnAI/db_query_builder",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "SQLAlchemy",
        "snowflake-connector-python",
        "snowflake-snowpark-python",
        "snowflake-sqlalchemy",
        "sqlalchemy-bigquery",
        "sqlalchemy-redshift",
        "redshift-connector",
        "psycopg2-binary",
    ],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
