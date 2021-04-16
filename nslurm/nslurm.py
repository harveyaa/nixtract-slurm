# For now just for nixtract-nifti, TODO include -cifti and -gifti 

import os
import glob
import json
import natsort
import time
import datetime
import pandas as pd
from string import Template
from argparse import ArgumentParser

def generate_parser():
    parser = ArgumentParser()
    parser.add_argument("--out_path",help='Required: Path to output directory.',dest='out_path',required=True)
    parser.add_argument("--config_path",help='Required: Path to config file for nixtract.',dest='config_path',required=True)
    parser.add_argument("--account",help='Required: Account name for SLURM.',dest='account',required=True)
    parser.add_argument("--time",help='Optional: Specify time (per job) for SLURM. Must be formatted "hours:minutes:seconds".',dest='time',required=False)
    parser.add_argument("--mem",help='Optional: Specify memory (per job) for SLURM.',dest='mem',required=False)
    parser.add_argument("--n_jobs",help='Optional: Specify number of jobs for SLURM.',dest='n_jobs',required=False)
    parser.add_argument("--rerun_completed",help='Flag to ignore completed output in out_path and process all input.',dest='rerun_completed',action='store_true')
    return parser

def check_glob(x):
    """Get files based on glob pattern.

    Parameters
    ----------
    x : str, list
        A glob pattern string or a list of files. If a list, glob pattern 
        matching is not performed.
    Returns
    -------
    list
        List of extracted file names.
    Raises
    ------
    ValueError
       x is neither a string nor list of strings
    """
    if isinstance(x, str):
        return natsort.natsorted(glob.glob(x))
    elif isinstance(x, list):
        return x
    else:
        raise ValueError('Input data files (images and confounds) must be a'
                         'string or list of string')

def read_config(config_path):
    """Read config file for nixtract, expanding glob for input and regressor files. 
    In the case that input and regressor files are specified as lists (not glob), assumes the lists are ordered the same way.

    Parameters
    ----------
    config_path : str
        Path to the config file.
    Returns
    -------
    dict
        Dictionary of key value mappings from config file, with input_files and regressor_files expanded if they were a glob.
    Raises
    ------
    ValueError
       Number of regressor files must be either be 0 or match number of input files.
    """
    with open(config_path) as f:
        config = json.load(f)
    input_files = check_glob(config['input_files'])
    conf_files = check_glob(config['regressor_files'])
    
    if (len(conf_files) != 0) and (len(input_files) != len(conf_files)):
        raise ValueError("Number of regressor files must be either be 0 or match number of input files.")

    config['input_files'] = input_files
    config['regressor_files'] = conf_files
    return config

def replace_file_ext(fname):
    """Format a string from file_timeseries.tsv to file.nii.gz.

    Parameters
    ----------
    fname : str
        Filename ending with _timeseries.tsv
    Returns
    -------
    str
        _timeseries.tsv file to be used for output
    """
    return fname.replace('_timeseries.tsv','.nii.gz')

def get_completed(out_path):
    """Make a list of completed .nii.gz files based on _timeseries.tsv files in the out_path directory.

    Parameters
    ----------
    out_path : str
        Path to output directory.
    Returns
    -------
    list
        List of .nii.gz files that have matching _timeseries.tsv files in the out_path directory.
    """
    completed = [ i for i in os.listdir(out_path) if i.endswith('_timeseries.tsv')]
    print('Found {} completed subjects.'.format(len(completed)))
    return [i for i in map(replace_file_ext,completed)]

def get_todo(inputs, conf, out_path):
    """Get list of input_files and regressor_files filtered to those that haven't been completed on a previous run.

    Parameters
    ----------
    inputs : list of str
        List of input_files
    conf : list of str
        List of regressor_files
    out_path : str
        Path to output directory.
    Returns
    -------
    list
        List of input_files to be processed.
    list
        List of accompanying regressor_files. If conf was an empty list, returns an empty list.
    """
    completed = get_completed(out_path)
    if len(conf) != 0:
        inputs_filt = []
        conf_filt = []
        for i in range(len(inputs)):
            if os.path.basename(inputs[i]) in completed:
                pass
            else:
                inputs_filt.append(inputs[i])
                conf_filt.append(conf[i])
        return inputs_filt,conf_filt
    else:
       return [i for i in inputs if os.path.basename(i) not in completed], conf

def get_slurm_params(n,runtime=None,mem=None,n_jobs=None):
    """Get remaining parameters to submit SLURM jobs based on specified parameters and number of files to process.

    Parameters
    ----------
    n : int
        Number of files to process.
    runtime : str, None
        Time per run, string formatted 'hours:minutes:seconds".
    mem : str, None
        Memory, string formatted for SLURM e.g. '1G', '500MB'.
    n_jobs : int, None
        Number of SLURM jobs to launch.
    Returns
    -------
    str
        Time per job.
    str
        Memory per job.
    int
        Number of jobs.
    """
    #TIME ~5s per subject (ADHD200 and fmri dev dataset)
    #MEM 1G overall (cleans up after each subject, takes about peak around ~500)
    #Tested w/ MIST64 and MIST444
    if mem == None:
        mem = '1G'

    if runtime==None:
        if n_jobs==None:
            if n < 1000:
                n_per_job = 50
            elif n < 10000:
                n_per_job = 200
            else:
                n_per_job = 500

            n_jobs = int(n/n_per_job)
            if n_jobs == 0:
                n_jobs = 1
        else:
            n_per_job = int(n/n_jobs) #round down (add one later to calc for time)

        sec = 2*n_per_job*5 #(seconds)
        runtime = str(datetime.timedelta(seconds=sec))

    else:
        sec = int(runtime.split(':')[0])*3600 + int(runtime.split(':')[1])*60 + int(runtime.split(':')[2])
        if n_jobs == None:
            n_jobs = int((10*n)/sec) 
    return runtime,mem,n_jobs

def split_list(n,ls):
    """Split input list into n chunks, remainder of division by n goes into last chunk.
    If input list is empty, returns list of n empty lists.
    Parameters
    ----------
    n : int
        Number of chunks.
    ls : list
        List to split.
    Returns
    -------
    list
        List of n chunks of input list.
    """
    if len(ls) == 0:
        return [[] for i in range(n)]
    m = int(len(ls)/n)
    chunks = []
    for i in range(0,len(ls),m):
        if i == (n - 1)*m:
            chunks.append(ls[i:])
            break
        chunks.append(ls[i:(i + m)])
    return chunks

def get_batches(n_jobs, files, conf_files):
    """Split input and regressor files into batches.
    Parameters
    ----------
    n_jobs : int
        Number of jobs/batches.
    files : list
        List of input_files.
    conf_files : list
        List of corresponding regressor_files.
    Returns
    -------
    list
        List of n_jobs batches of input_files.
    list
        List of n_jobs batches of corresponding regressor_files. If input was empty list, this will be a list of n_jobs empty lists.
    """
    batches = split_list(n_jobs,files)
    batches_conf = split_list(n_jobs,conf_files)
    return batches, batches_conf

def log_batches(batches,out_path):
    """Write which files are in which batch (for debugging) to file_to_job.json in logs dir.
    Parameters
    ----------
    batches : list
        List of input files.
    out_path : str
        Path to output dir (should already contain logs dir).
    """
    d = dict(zip(range(len(batches)),batches))
    with open(os.path.join(out_path,'logs/file_to_job.json'), 'w') as json_file:
        json.dump(d, json_file)

def make_config(batches,batches_conf,params,out_path):
    """Make config file for each SLURM job with appropriate input and regressor files and params from provided config file.
    These files will get deleted by the SLURM job once it has been run.
    Parameters
    ----------
    batches : list
        List of input files.
    batches_conf : list
        List of conf files.
    params : dict
        Parameters from user provided config file.
    out_path : str
        Path to output dir.
    """
    for i in range(len(batches)):
        p = params.copy()
        p['input_files'] = batches[i]
        p['regressor_files'] = batches_conf[i]
        with open(os.path.join(out_path,'config_{}.json'.format(i)), 'w') as json_file:
            json.dump(p, json_file)
    

def make_sh(account,runtime,mem,n_jobs,out_path):
    """Make .sh file to submit SLURM jobs.
    Parameters
    ----------
    account : str
        Account name for submission.
    runtime : str
        Time per job, formatted for SLURM.
    mem : str
        Memory per job, formatted for SLURM.
    n_jobs: int
        Number of SLURM jobs to submit.
    out_path : str
        Path to output dir.
    """
    src = Template("#!/bin/bash\n"
                    "#SBATCH --job-name=nixtract-slurm\n"
                    "#SBATCH --time=$time\n"
                    "#SBATCH --mem=$mem\n"
                    "#SBATCH --account=$account\n"
                    "#SBATCH --array=0-$n_jobs\n"
                    "#SBATCH -o $out_path/logs/slurm_output/batch_%a.out\n"
                    "$command -c $out_path/logs/config_$${SLURM_ARRAY_TASK_ID}.json $out_path\n"
                    "rm $out_path/logs/config_*.json")

    d = {'account':account,'time': runtime,'mem': mem,'n_jobs': (n_jobs-1),'out_path':out_path,'command':'nixtract-nifti'}
    result = src.substitute(d)
    sh = open(os.path.join(out_path,"logs/submit.sh"), "w")
    sh.write(result)
    sh.close()

def submit_jobs(out_path):
    """Submit the .sh file in the output dir to SLURM.
    Parameters
    ----------
    out_path : str
        Path to output dir (containing the .sh file).
    """
    p = os.path.join(out_path,'logs/submit.sh')
    os.system('sbatch {}'.format(p))

def test_import():
    try:
        import nixtract
    except:
        raise ImportError("nixtract must be installed to use nixtract-slurm. See documentation for installation instructions.")

def main():
    """Entry point to nixtract-slurm."""
    parser = generate_parser()
    args = parser.parse_args()

    test_import()

    params = read_config(args.config_path)
    input_files = check_glob(params['input_files'])
    confound_files = check_glob(params['regressor_files'])
    print('Found {} input file(s), and {} regressor file(s).'.format(len(input_files),len(confound_files)))

    # Create logs dir.
    if not os.path.isdir(os.path.join(args.out_path, 'logs')):
        os.makedirs(os.path.join(args.out_path, 'logs'))

    # Create slurm output dir.
    if not os.path.isdir(os.path.join(args.out_path, 'logs/slurm_output')):
        os.makedirs(os.path.join(args.out_path, 'logs/slurm_output'))

    #Check which files have already been completed
    if not args.rerun_completed:
        print('Making todo list...')
        input_filt, confound_filt = get_todo(input_files, confound_files, args.out_path)
        input_files = input_filt
        confound_files = confound_filt
        print('Processing {} subject(s).'.format(len(input_files)))
    
    #TO DO: only want to fill in missing arg with best choice based on provided
    if (args.time == None) or (args.mem == None) or (args.n_jobs == None):
        runtime, mem, n_jobs = get_slurm_params(len(input_files), args.time,args.mem,args.n_jobs)
        print('Submitting {} SLURM job(s), with time={} and memory={} each...'.format(n_jobs,runtime,mem))

    input_batches, confound_batches = get_batches(n_jobs, input_files, confound_files)
    log_batches(input_batches, args.out_path)

    make_config(input_batches,confound_batches, params, os.path.join(args.out_path,"logs"))
    make_sh(args.account,runtime,mem,n_jobs,args.out_path)
    submit_jobs(args.out_path)
