from setuptools import setup, find_packages
from setuptools.command.install import install

if __name__ == '__main__':
    setup(
            name='genesis',
            version='0.7.0',
            packages=find_packages(exclude=['test']),
            install_requires=[
                'spacy==2.0.12',
                'progressbar2==3.16.0'
                ],
            dependency_links=[
                "git+https://github.com/mrmechko/tripsmodule",
                "git+https://github.com/mrmechko/diesel-python"
                ]
            )
