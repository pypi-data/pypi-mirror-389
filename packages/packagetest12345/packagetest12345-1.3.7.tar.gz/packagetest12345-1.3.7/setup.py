from setuptools import setup, find_packages
import os
import sys

current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)

# load version
with open(os.path.join(current_dir, "packagetest123/__version__.py"), "r") as f:
    exec(f.read(), globals())


# requirements
with open(os.path.join(current_dir,"requirements.txt"), "r") as f:
    requirements = f.readlines()

# Project description
with open(os.path.join(current_dir,"README.md"), "r") as f:
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
