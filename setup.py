from setuptools import setup

setup(
    name='nixtract-slurm',
      version='0.1.4',
      description='A wrapper for nixtract that enables SLURM job submission.',
      url='https://github.com/harveyaa/nixtract-slurm',
      author='Annabelle Harvey',
      author_email='annabelle.harvey@umontreal.ca',
      license='MIT',
      packages=['nslurm','tests'],
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
    ],
      entry_points={
        'console_scripts': [
            'nixtract-slurm = nslurm.nslurm:main',
        ],
      },
)