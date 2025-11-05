from setuptools import setup, find_packages
from pathlib import Path

__version__ = "0.1.1"

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="how2-shell-assistant",
    version=__version__,
    description="`how2` is a command-line tool Powered by Large Language Models (LLMs), it translates your natural language questions into executable shell commands.",
    long_description_content_type="text/markdown",
    long_description=long_description,

    url='https://github.com/DanHUMassMed/how2.git',
    author='Dan Higgins',
    author_email='daniel.higgins@gatech.edu',
    license='MIT',

    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "ollama==0.6.0",
        "pyperclip==1.11.0",
        "psutil==7.1.3"
    ],
    entry_points={
        "console_scripts": [
            "how2=how.cli:main",  
        ],
    },
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False
)
