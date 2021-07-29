from setuptools import setup

setup(name='django_payflow',
      version='2.0.0',
      description="A django app for interaction with the django_payflow api",
      install_requires=(
          'requests',
      ),
      packages=['django_payflow']
)
