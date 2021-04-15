This project is in development, soon ready but not yet. TODO:
- [ ] Incorporate nixtract-cifti and nixtract-gifti
- [x] Write tests
  - [x] find best time, memory, n_subs_per_job
  - [x] test functionality
- [x] Set up continuous integration
- [x] Set up package entry points
- [x] Set up command line usage
- [ ] Write documentation
- [ ] Update Pypi

# nixtract-slurm
[![harveyaa](https://circleci.com/gh/harveyaa/nixtract-slurm.svg?style=svg)](<LINK>)

This project is a wrapper for [`nixtract`](https://github.com/danjgale/nixtract), that splits up the files to be processed into batches and submits them to SLURM.
`nixtract` (NeuroImaging eXTRACTion) is a collection of simple command-line tools that provide a decently unified interface to extract and process timeseries data from NIFTI, GIFTI, and CIFTI neuroimaging files.

### Warning:
  - Currently only NIFTI files are supported by `nixtract-slurm`
  - Currently probabilistic atlases are not supported by `nixtract`, see this [issue](https://github.com/danjgale/nixtract/issues/15).
  - In order to use `load_confounds` stratefies input data must have been preprocessed with [fMRIprep](https://fmriprep.org/en/stable/). See `nixtract` [documentation](https://github.com/danjgale/nixtract) for the `--regressors` flag, under the section 'NIFTIs'.


## Installation
For [Compute Canada](https://www.computecanada.ca/):

### 1. Load python
`module load python/3.6`

### 2. Create a venv
#### Make an empty directory for your venv:
`mkdir ENV`

Where `ENV` is the name of your environment.

#### Create the venv:
`virtualenv --no-download ~/ENV`

ENV is name of empty directory containing environment.

#### Activate it:
`source ~/ENV/bin/activate`
#### Upgrade pip:
`pip install --no-index --upgrade pip`

### 3. Install nixtract
#### Clone directory
`git clone https://github.com/danjgale/nixtract.git`
#### Install nixtract
`cd nixtract`

`pip install .`

### 4. Install nixtract-slurm
`pip install nixtract-slurm`

### 5. Launch nixtract-slurm
Must have venv activated and be on the login node. To use nixtract-slurm see documentation below.

## Usage
```
usage: nixtract-slurm [-h] --out_path OUT_PATH --config_path CONFIG_PATH
                      --account ACCOUNT [--time TIME] [--mem MEM]
                      [--n_jobs N_JOBS] [--rerun_completed]

optional arguments:
  -h, --help                  show this help message and exit
  --out_path OUT_PATH         Required: Path to output directory.
  --config_path CONFIG_PATH   Required: Path to config file for nixtract.
  --account ACCOUNT           Required: Account name for SLURM.
  --time TIME                 Optional: Specify time (per job) for SLURM. Must be formatted "hours:minutes:seconds".
  --mem MEM                   Optional: Specify memory (per job) for SLURM.
  --n_jobs N_JOBS             Optional: Specify number of jobs for SLURM.
  --rerun_completed           Flag to ignore completed output in out_path and process all input.

```
### Description of `nixtract-slurm` output
`nixtract-slurm` output in the `out_path` directory:
 - `nixtract_data`
    - See `nixtract` [documentation](https://github.com/danjgale/nixtract).
 - `logs` 
     - `slurm_output`
        - SLURM output for each job eg `batch_0.out`, for debugging. 
     - `file_to_job.json`
        - Mapping from input file to job number, to find corresponding SLURM output.
     - `submit.sh`
        - SLURM submission script of most recent run. 
 - Finished `file_timeseries.tsv` for each input `file.nii.gz`.
