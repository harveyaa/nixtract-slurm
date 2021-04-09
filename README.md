This project is in development, soon ready but not yet. TODO:
- [ ] Incorporate nixtract-cifit and nixtract-gifti
- [ ] Write tests
  - [ ] find best time, memory, n_subs_per_job
  - [ ] test functionality
- [x] Set up continuous integration
- [x] Set up package entry points
- [x] Set up command line usage
- [ ] Write documentation
- [ ] Update Pypi

[![harveyaa](https://circleci.com/gh/harveyaa/nixtract-slurm.svg?style=svg)](<LINK>)

# For compute canada:

## 1. Load python
`module load python/3.6`

## 2. Create a venv
### Make an empty directory for your venv:
`mkdir ENV`

Where `ENV` is the name of your environment.

### Create the venv:
`virtualenv --no-download ~/ENV`

ENV is name of empty directory containing environment.

### Activate it:
`source ~/ENV/bin/activate`
### Upgrade pip:
`pip install --no-index --upgrade pip`

## 3. Install nixtract
### Clone directory
`git clone https://github.com/danjgale/nixtract.git`
### Install nixtract
`cd nixtract`

`pip install .`

## 4. Install nixtract-slurm
`pip install nixtract-slurm`

## 5. Launch nixtract-slurm
Have to have venv open and be on the login node. To use nixtract-slurm see documentation.

