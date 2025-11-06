from setuptools import setup, find_packages

setup(
    name="github-actions-python-component",
    version="1.0.0",
    description="GitHub Actions workflow templates for Python projects",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=5.4.0",
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "github-actions-python=installer:main",
        ],
    },
    package_data={
        "": ["workflows/*.yml", "configs/*"],
    },
    include_package_data=True,
)