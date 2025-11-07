from setuptools import setup, find_packages

setup(
    name='colocal',
    version='2025.11.06.1340',  # GitHub Actions will auto-update this
    url='https://github.com/project-ida/colocal',
    license='MIT',
    author='project-ida',
    description='Harmonises Jupyter and Colab notebook environments for consistent paths, imports, and working directories',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "ipynbname",
    ],
    python_requires=">=3.8",
    zip_safe=False,
)
