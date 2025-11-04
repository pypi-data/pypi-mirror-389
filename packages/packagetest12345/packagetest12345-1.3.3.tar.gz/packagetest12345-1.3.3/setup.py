from setuptools import setup, find_packages


# load version
with open("packagetest123/__version__.py") as f:
    exec(f.read(), globals())


# requirements
with open("requirements.txt", "r") as f:
    requirements = f.readlines()

# Project description
with open("README.md", "r") as f:
  long_description = f.read()


setup(
        name = 'packagetest12345',
        version = __version__,

        author = 'Lukas Freter',
        author_email = 'lukas.freter@aalto.fi',

        packages=find_packages(),

        #install_requires= requirements,
        description = 'Test package',
        long_description = long_description,
        long_description_content_type = 'text/markdown',
        keywords = ['test', 'key'],

        )
