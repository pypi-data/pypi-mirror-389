from setuptools import setup

setup(name='pythonwhois2',
      version='2.5.3',
      description='Module for retrieving and parsing the WHOIS data for a domain. Supports most domains. No dependencies.',
      author='Nathan Nguyen',
      author_email='nathannn702@gmail.com',
      url='http://github.com/froztty/pythonwhois2',
      packages=['pythonwhois'],
      package_dir={"pythonwhois":"pythonwhois"},
      package_data={"pythonwhois":["*.dat"]},
      install_requires=['argparse'],
      provides=['pythonwhois'],
      scripts=["pwhois"],
      license="WTFPL"
     )
