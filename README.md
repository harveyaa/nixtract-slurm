## 1. Load python
module load python/3.6

## 2. Create a venv
Make an empty directory for your venv:
mkdir ENV
Create the venv:
virtualenv --no-download ~/ENV
ENV is name of empty directory containing environment
Activate it:
source ~/ENV/bin/activate
Upgrade pip:
pip install --no-index --upgrade pip

## 3. Install nixtract
Clone directory
git clone https://github.com/danjgale/nixtract.git
Install nixtract
cd nixtract
pip install .

## 4. Install nixtract-slurm
pip install nixtract-slurm

## 5. Launch nixtract-slurm
Have to have venv open and be on the login node. To use nixtract-slurm see documentation.

