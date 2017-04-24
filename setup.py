from setuptools import setup, find_packages
from setuptools.command.install import install

if __name__ == '__main__':
    setup(
            name='genesis',
            version='0.0.1',
            packages=find_packages(exclude=['test']),
            install_requires=[
                'spacy==1.7.0',
                'tripsmodule==1.1.0',
                'diesel>=1.0.0',
                'progressbar2==3.16.0'
                ],
            dependence_links=[
                "git+https://github.com/mrmechko/tripsmodule@v1.1.0",
                "git+https://github.com/mrmechko/diesel-python"
                ]
            )
