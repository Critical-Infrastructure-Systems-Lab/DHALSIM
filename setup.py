import setuptools

setuptools.setup(
    name="dhalsim",
    version="1.1.0",
    url="https://github.com/afmurillo/DHALSIM",
    project_urls={
        "Bug Tracker": "https://github.com/afmurillo/DHALSIM/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        # "Operating System :: OS Independent",
    ],
    license='MIT',
    packages=['dhalsim'],
    install_requires=[
        'PyYAML==5.4.1',
        'pyyaml-include',
        'antlr4-python3-runtime==4.7.2',
        'progressbar2',
        'pandas==1.3.4',
        'matplotlib==3.5.0',
        'schema',
        'scapy',
        'fnfqueue'
    ],
    extras_require={
        'test': ['pytest', 'pytest-mock', 'mock', 'wget', 'coverage', 'pytest-cov', 'flaky'],
        'doc': ['sphinx', 'sphinx-rtd-theme', 'sphinx-prompt'],
    },
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'dhalsim = dhalsim.command_line:main',
        ],
    },
)
