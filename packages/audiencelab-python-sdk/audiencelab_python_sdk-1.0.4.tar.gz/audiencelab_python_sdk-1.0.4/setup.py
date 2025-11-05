from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='audiencelab_python_sdk',
    version='1.0.4',
    description='Python SDK for AudienceLab services',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Nathan Nylund',
    author_email='nathan@geeklab.app',
    url='https://github.com/Geeklab-Ltd/audiencelab_python_sdk',
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        'requests>=2.0.0'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        # License information is defined within the project (see the LICENSE file for details).
    ],
    python_requires='>=3.6',
)