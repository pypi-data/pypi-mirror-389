from setuptools import setup, find_packages

setup(
    name='easymathlib',
    version='1.0.0',
    author='Krishna Varshney',
    author_email='your_email@example.com',
    description='A simple Python math library with basic, advanced, and geometry operations.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/mymathlib',  # update after creating GitHub repo
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
