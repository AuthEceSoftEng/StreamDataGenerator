from setuptools import setup, find_packages

setup(
    name="stream-data-generator-dsl",
    version="0.1.0",
    description="DSL for Stream Data Generation",
    packages=find_packages(),
    install_requires=[
        "textX[cli]",
        "regex",
        "PyYAML",
        "jinja2",
    ],
    entry_points={
        "console_scripts": [
            "sdg=sdg.cli:main",
        ],
        "textx_languages": [
            "sdg = sdg.lang:language_desc",
        ],
        "textx_generators": [
            "sdg_gen = sdg.generator.codegenerator:sdg_gen_desc",
        ],
    },
    include_package_data=True,
    package_data={
        "sdg.grammar": ["*.tx"],
    },
)
