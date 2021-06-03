import setuptools

setuptools.setup(
    name="dhalsim",
    version="0.0.1",
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
    packages=['dhalsim'],
    install_requires=[
        'PyYAML',
        'pyyaml-include',
        'antlr4-python3-runtime==4.7.2',
        'progressbar2',
        'wntr',
        'pandas',
        'schema',
        'scapy',
        'fnfqueue'
    ],
    extras_require={
        'test': ['pytest', 'pytest-mock', 'mock', 'wget', 'flaky', 'netaddr'],
        'doc': ['sphinx', 'sphinx-rtd-theme', 'sphinx-prompt'],
    },
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'dhalsim = dhalsim.command_line:main',
        ],
    },
)
