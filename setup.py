import os
from setuptools import setup, find_packages

# single source of truth for package version
version_ns = {}
with open(os.path.join('concierge', 'version.py')) as f:
    exec(f.read(), version_ns)

install_requires = []
with open('requirements.txt') as reqs:
    for line in reqs.readlines():
        req = line.strip()
        if not req or req.startswith('#'):
            continue
        install_requires.append(req)

setup(
    name="concierge-cli",
    description="Client for the Concierge Service",
    url='https://github.com/fair-research/concierge-cli',
    maintainer='Fair Research',
    maintainer_email='',
    version=version_ns['__version__'],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cbag = concierge.client:main',
            'concierge = concierge.client:usage',
        ]
    },
    requires=[],
    install_requires=install_requires,
    dependency_links=[],
    license='Apache 2.0',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ]
)
