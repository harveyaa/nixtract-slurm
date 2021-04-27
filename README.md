# nixtract-slurm
[![harveyaa](https://circleci.com/gh/harveyaa/nixtract-slurm.svg?style=svg)](<LINK>)
[![PyPI version shields.io](https://img.shields.io/pypi/v/pynm.svg)](https://pypi.org/project/nixtract-slurm/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project is a wrapper for [`nixtract`](https://github.com/danjgale/nixtract), that splits up the files to be processed into batches and submits them to SLURM.
`nixtract` (NeuroImaging eXTRACTion) is a collection of simple command-line tools that provide a decently unified interface to extract and process timeseries data from NIFTI, GIFTI, and CIFTI neuroimaging files.

### Warning:
  - Currently only NIFTI files are supported by `nixtract-slurm`, see this [issue](https://github.com/harveyaa/nixtract-slurm/issues/3).
  - Currently probabilistic atlases are not supported by `nixtract`, see this [issue](https://github.com/danjgale/nixtract/issues/15).
  - In order to use `load_confounds` input data must have been preprocessed with [fMRIprep](https://fmriprep.org/en/stable/). See `nixtract` [documentation](https://github.com/danjgale/nixtract) for the `--regressors` flag, under the section 'NIFTIs'.


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

### 3. Install nixtract-slurm
`pip install nixtract-slurm`

### 4. Launch nixtract-slurm
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
  
  --time TIME                 Optional: Specify time (per job) for SLURM. 
                              Must be formatted "hours:minutes:seconds".
                              
  --mem MEM                   Optional: Specify memory (per job) for SLURM.
                              Must be formatted for SLURM e.g. '1G', '500MB'.
  
  --n_jobs N_JOBS             Optional: Specify number of jobs for SLURM.
  
  --rerun_completed           Flag to ignore completed output in out_path and process all input.

```
## Description of `nixtract-slurm` output
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

## SLURM parameters
The only required parameter is `account`. If left to default:
  - `n_jobs` will be determined based on the number of files to be processed:
      - Less than 1000: ~50 files per job
      - Less than 10,000: ~200 files per job
      - Otherwise: ~500 files per job
  - `time` (per job) will be set as a function of the number of files per job, ~10s per file.
  - `mem` (per job) will be set to '1G'.
 
If any of the parameters are specified, the remaining defaults will be set in accordance. The default parameters were determined using subjects from the [ADHD200](https://nilearn.github.io/modules/generated/nilearn.datasets.fetch_adhd.html) and [development fMRI](https://nilearn.github.io/modules/generated/nilearn.datasets.fetch_development_fmri.html) datasets and the [MIST](https://mniopenresearch.org/articles/1-3) 64 and 444 atlases. If input data is considerably larger (longer scans or finer grained parcellation) the parameters should be adjusted accordingly.

## Hot restart
In case SLURM jobs are killed or fail for whatever reason, after debugging and tweaking the SLURM parameters, just rerun `nixtract-slurm` with the same parameters and `out_path`. Before launching another set of jobs to SLURM, `nixtract-slurm` will search in the `out_path` directory for finished files and omit the corresponding input files from the TODO list.
To disable this behaviour and run all the files, use the `--rerun_completed` flag.
