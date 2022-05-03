import memory_profiler as mem
import time
import json
import os
import subprocess
import nslurm.nslurm as ns

        
def make_test_config(batches,batches_conf,out_path,atlas):
    params = {
            "input_files": [],
            "roi_file": atlas,
            "mask_img": None,
            "labels": [],
            "regressor_files": None,
            "regressors": [],
            "as_voxels": False,
            "sphere_size": None,
            "allow_overlap": False,
            "standardize": False,
            "t_r": None,
            "detrend": False,
            "high_pass": None,
            "low_pass": None,
            "smoothing_fwhm": None,
            "discard_scans": None,
            "n_jobs": 1
            }
    ns.make_config(batches,batches_conf,params,out_path)

def get_data(name):
    if name == 'dev':
        data_base = '/home/harveyaa/nixtract-slurm_aux/development_fmri/development_fmri'
        input_files = [data_base + '/sub-pixar001_task-pixar_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz',
                        data_base + '/sub-pixar002_task-pixar_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz',
                        data_base + '/sub-pixar123_task-pixar_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz']
        conf_files = [data_base + '/sub-pixar001_task-pixar_desc-confounds_regressors.tsv',
                        data_base + '/sub-pixar002_task-pixar_desc-confounds_regressors.tsv',
                        data_base + '/sub-pixar123_task-pixar_desc-confounds_regressors.tsv']
        return input_files, []
    elif name == 'adhd':
        data_base = '/home/harveyaa/nixtract-slurm_aux/adhd/data'
        input_files = [data_base + '/0010042/0010042_rest_tshift_RPI_voreg_mni.nii.gz',
                        data_base + '/0010064/0010064_rest_tshift_RPI_voreg_mni.nii.gz',
                        data_base + '/0010128/0010128_rest_tshift_RPI_voreg_mni.nii.gz']
        conf_files = [data_base + '/0010042/0010042_regressors.csv',
                        data_base + '/0010064/0010064_regressors.csv',
                        data_base + '/0010128/0010128_regressors.csv']
        return input_files, []
    else:
        raise ValueError("Data name not recognized.")

def get_atlas(name):
    if name == 'difumo_64':
        return '/home/harveyaa/nixtract-slurm_aux/difumo_atlases/64/2mm/maps.nii.gz'
    elif name == 'difumo_1024':
        return '/home/harveyaa/nixtract-slurm_aux/difumo_atlases/1024/2mm/maps.nii.gz'
    elif name == 'MIST_64':
        return '/home/harveyaa/projects/def-pbellec/ATLAS/MIST/Parcellations/MIST_64.nii.gz'
    elif name == 'MIST_444':
        return '/home/harveyaa/projects/def-pbellec/ATLAS/MIST/Parcellations/MIST_444.nii.gz'
    else:
        raise ValueError("Atlas name not recognized.")

def resource_test(atlas_name='MIST_64',data_name='adhd'):
    out_path = '/home/harveyaa/nixtract-slurm_aux'
    input_files,conf_files = get_data(data_name)
    atlas = get_atlas(atlas_name)
    make_test_config([input_files],[conf_files],out_path,atlas)

    #command = "nixtract-nifti -c {}/config_0.json {}".format(out_path,out_path)
    start = time.time()
    #command = "subprocess.run(['nixtract-nifti','-c', '/home/harveyaa/nixtract-slurm_aux/config_0.json','/home/harveyaa/nixtract-slurm_aux'])"
    memory = mem.memory_usage(proc = subprocess.Popen(['nixtract-nifti','-c', '/home/harveyaa/nixtract-slurm_aux/config_0.json','/home/harveyaa/nixtract-slurm_aux']))
    dur = time.time() - start

    d = {'atlas':atlas_name,'data':data_name,'time':dur,'memory':memory}
    print('atlas: {}'.format(atlas_name))
    print('data: {}'.format(data_name))
    print('time: {}'.format(dur))
    print('memory: {}'.format(memory))
    print('\n')
    with open('result_{}_{}.json'.format(atlas_name,data_name), 'w') as fp:
        json.dump(d, fp)

if __name__ == '__main__':
    print(mem.memory_usage(-1, interval=.2, timeout=1))

    for atlas in ['difumo_64','difumo_1024','MIST_64','MIST_444']:
        for data in ['dev','adhd']:
            print('Testing with {} data and {} atlas'.format(data,atlas))
            resource_test(atlas_name=atlas,data_name=data)