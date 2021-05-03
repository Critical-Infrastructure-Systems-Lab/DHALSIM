import setuptools

# with open("README.md", "r", encoding="utf-8") as fh:
#     long_description = fh.read()

setuptools.setup(
    name="dhalsim",
    version="0.0.1",
    # author="Example Author",
    # author_email="author@example.com",
    # description="A small example package",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    url="https://gitlab.ewi.tudelft.nl/cse2000-software-project/2020-2021-q4/cluster-06/water-infrastructure/dhalsim",
    project_urls={
        "Bug Tracker": "https://gitlab.ewi.tudelft.nl/cse2000-software-project/2020-2021-q4/cluster-06/water-infrastructure/dhalsim/-/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        # "Operating System :: OS Independent",
    ],
    license='MIT',
    # package_dir={"": "src"},
    packages=['dhalsim'],
    install_requires=[
        'PyYAML',
        'antlr4-python3-runtime',
    ],
    extras_require={
        'test': ['pytest', 'pytest-mock'],
    },
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'dhalsim = dhalsim.command_line:main',
        ],
    },
)
