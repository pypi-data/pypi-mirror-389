import os
from setuptools import setup, find_packages

def read_version():
    version_file = os.path.join(os.path.dirname(__file__), 'WebDesignTaal', 'version.txt')
    with open(version_file, 'r', encoding="utf-8") as f:
        return f.read().strip()

def read_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    with open(readme_file, 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name="WebDesignTaal",
    version=read_version(),
    author="TJouleL",
    description="Een programmeertaal die compileert naar HTML met een Nederlandse syntax.",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/TJouleL/WebDesignTaal",
    packages=find_packages(
        where='.',
        include=['WebDesignTaal*']
    ),
    include_package_data=True,
    package_data={
        'WebDesignTaal': ['version.txt'],
    },
    install_requires=[],
    entry_points={
        'console_scripts': [
            'wdt=WebDesignTaal.file_handler:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Topic :: Software Development :: Compilers",
        "Topic :: Text Processing :: Markup :: HTML",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    keywords='html compiler webdesign educatie',
    python_requires='>=3.6',
)