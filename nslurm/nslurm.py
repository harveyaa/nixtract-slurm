# For now just for nixtract-nifti, TODO include -cifti and -gifti 
# TODO write tests

import os
import glob
import json
import natsort
import nixtract
import pandas as pd
from string import Template
from argparse import ArgumentParser

def generate_parser():
    parser = ArgumentParser()
    parser.add_argument("--out_path",dest='out_path',required=True)
    parser.add_argument("--config_path",dest='config_path',required=True)
    parser.add_argument("--account",dest='account',required=True)
    parser.add_argument("--time",dest='time',required=False)
    parser.add_argument("--mem",dest='mem',required=False)
    parser.add_argument("--n_jobs",dest='n_jobs',required=False)
    parser.add_argument("--rerun_completed",dest='rerun_completed',action='store_true')
    return parser

def check_glob(x):
    """Get files based on glob pattern
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
    """Make a file.nii.gz from file_timeseries.tsv
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
    completed = [ i for i in os.listdir(out_path) if i.endswith('_timeseries.tsv')]
    return [i for i in map(replace_file_ext,completed)]

def get_todo(inputs, conf, out_path):
    completed = get_completed(out_path)
    if len(conf) != 0:
        df = pd.DataFrame([inputs,conf],index = ['inputs','conf']).transpose()
        todo = df[~df['inputs'].isin(completed)].dropna()
        return todo['inputs'].tolist(), todo['conf'].tolist()
    else:
       return [i for i in inputs if i not in completed], conf

def get_slurm_params(n,time,mem,n_jobs):
    #NEED TO TEST FOR ACTUAL VALUES
    if n < 1000:
        n_jobs = int(n/50) # eg 7.9 -> 7
        time = '30:00'
        mem = '1G'
        if n_jobs == 0:
            n_jobs = 1
    elif n < 10000:
        n_jobs = int(n/100) # eg 7.9 -> 7
        time = '1:00:00'
        mem = '2G'
    else:
        n_jobs = int(n/500) # eg 7.9 -> 7
        time = '2:00:00'
        mem = '3G'
    return time,mem,n_jobs

def split_list(n,ls):
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
    batches = split_list(n_jobs,files)
    batches_conf = split_list(n_jobs,conf_files)
    return batches, batches_conf

def log_batches(batches,out_path):
    d = dict(zip(range(len(batches)),batches))
    with open(os.path.join(out_path,'file_to_job.json'), 'w') as json_file:
        json.dump(d, json_file)

def make_config(batches,batches_conf,params,out_path):
    for i in range(len(batches)):
        p = params.copy()
        p['input_files'] = batches[i]
        p['regressor_files'] = batches_conf[i]
        with open(os.path.join(out_path,'config_{}.json'.format(i)), 'w') as json_file:
            json.dump(p, json_file)
    

def make_sh(account,time,mem,n_jobs,out_path):
    d = {'account':account,'time': time,'mem': mem,'n_jobs': (n_jobs-1),'out_path':out_path,'command':'nixtract-nifti'}
    with open('../templates/submit_template.sh', 'r') as f:
        src = Template(f.read())
        result = src.substitute(d)
    sh = open(os.path.join(out_path,"logs/submit.sh"), "w")
    sh.write(result)
    sh.close()

def submit_jobs(out_path):
    p = os.path.join(out_path,'/logs/submit.sh')
    os.system('sbatch {}'.format(p))

def main():
    parser = generate_parser()
    args = parser.parse_args()

    params = read_config(args.config_path)
    input_files = check_glob(params['input_files'])
    confound_files = check_glob(params['regressor_files'])

    # Create logs dir.
    if not os.path.isdir(os.path.join(args.out_path, 'logs')):
        os.makedirs(os.path.join(args.out_path, 'logs'))

    # Create slurm output dir.
    if not os.path.isdir(os.path.join(args.out_path, 'logs/slurm_output')):
        os.makedirs(os.path.join(args.out_path, 'logs/slurm_output'))

    #Check which files have already been completed
    if not args.rerun_completed:
        input_files, confound_files = get_todo(input_files, confound_files, args.out_path)
    
    #TO DO: only want to fill in missing arg with best choice based on provided
    if (args.time == None) or (args.mem == None) or (args.n_jobs == None):
        time, mem, n_jobs = get_slurm_params(len(input_files), args.time,args.mem,args.n_jobs)

    input_batches, confound_batches = get_batches(n_jobs, input_files, confound_files)
    log_batches(input_batches, args.out_path)

    make_config(input_batches,confound_batches, params, args.out_path)
    make_sh(args.account,time,mem,n_jobs,args.out_path)
    submit_jobs(args.out_path)