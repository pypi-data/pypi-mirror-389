from setuptools import setup, find_packages
from pathlib import Path

HERE = Path(__file__).parent
long_description = (HERE / "README.md").read_text(encoding="utf-8") if (HERE / "README.md").exists() else ""

setup(
    name="devion_test",
    version="0.0.1",
    description="Test package for Devion workflow",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MattHeeper/Devion",
    author="MattHeeper",
    license="Apache-2.0",
    packages=find_packages(include=["devion_test", "devion_test.*"]),
    include_package_data=True,
    python_requires=">=3.11",
)
