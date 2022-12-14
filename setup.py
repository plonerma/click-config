from setuptools import find_packages, setup


with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", encoding="utf-8") as f:
    required = f.read().splitlines()


setup(
    name="click_config",
    version="0.0.1",
    description=(
        "Small wrapper around dataclass to enable use with click (as config)"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Max Ploner",
    author_email="click_config@maxploner.de",
    url="https://github.com/plonerma/click-config",
    packages=find_packages(where="src", exclude="tests"),
    package_dir={"": "src"},
    license="MIT",
    install_requires=required,
    include_package_data=True,
    python_requires=">=3.6",
)
