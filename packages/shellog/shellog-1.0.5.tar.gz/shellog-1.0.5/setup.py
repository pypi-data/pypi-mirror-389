from setuptools import setup

# Read the long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='shellog',
    version='1.0.5',    
    description='A Python package to get notifications about the logs of a process',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/danmargs/shellog',
    author='Daniele Margiotta',
    author_email='daniele.margiotta11@gmail.com',
    license='BSD 2-clause',
    packages=['shellog'],
    install_requires=['requests>=2.25.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',  
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.6',
)
