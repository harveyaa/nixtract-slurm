import nslurm.nslurm as ns
import json
import pytest
import os
import tempfile
import subprocess
import time
import csv
# from nilearn import datasets


class TestInternal:
    def test_read_config_correct(self,tmpdir):
        d = {'input_files':['a.nii.gz','b.nii.gz'],'regressor_files':['a.csv','b.csv']}
        with open(tmpdir / 'test.json', 'w') as json_file:
            json.dump(d, json_file)

        config = ns.read_config(tmpdir/'test.json')
        assert len(config['input_files']) == len(config['regressor_files'])

    def test_read_config_missing_reg_file(self,tmpdir):
        d = {'input_files':['a.nii.gz','b.nii.gz'],'regressor_files':['a.csv']}
        with open(tmpdir / 'test.json', 'w') as json_file:
            json.dump(d, json_file)

        with pytest.raises(ValueError):
            ns.read_config(tmpdir/'test.json')

    def test_read_config_no_reg_files(self,tmpdir):
        d = {'input_files':['a.nii.gz','b.nii.gz'],'regressor_files':[]}
        with open(tmpdir / 'test.json', 'w') as json_file:
            json.dump(d, json_file)

        config = ns.read_config(tmpdir/'test.json')
        assert len(config['input_files']) == 2
        assert len(config['regressor_files']) == 0
        
    def test_check_glob(self,tmpdir):
        open(tmpdir / "a.py","x")
        open(tmpdir / "b.py","x")
        ls = ns.check_glob(str(os.path.join(tmpdir,'*.py')))
        assert len(ls) == 2
        assert ls[0].endswith('a.py')

    def test_replace_file_ext(self):
        ts = ['a_timeseries.tsv','/path/to/b_timeseries.tsv','../path/to/c_timeseries.tsv']
        nii = [ns.replace_file_ext(t) for t in ts]
        assert nii == ['a.nii.gz','/path/to/b.nii.gz','../path/to/c.nii.gz']
        
    def test_get_completed_none_completed(self,tmpdir):
        completed = ns.get_completed(tmpdir)
        assert completed == []

    def test_get_completed_some_completed(self,tmpdir):
        for i in range(3):
            open(tmpdir / "{}_timeseries.tsv".format(i),"x")

        completed = ns.get_completed(tmpdir)
        assert len(completed) == 3

    def test_get_todo_none_completed_with_reg_files(self,tmpdir):
        todo,todo_conf = ns.get_todo(['a.nii.gz','b.nii.gz'],['a.csv','b.csv'],tmpdir)

        assert todo[0].endswith('.nii.gz')
        assert todo[-1].endswith('.nii.gz')
        assert len(todo) == 2
        assert len(todo) == len(todo_conf)

    def test_get_todo_none_completed_no_reg_files(self,tmpdir):
        todo,todo_conf = ns.get_todo(['a.nii.gz','b.nii.gz'],[],tmpdir)

        assert todo[0].endswith('.nii.gz')
        assert todo[-1].endswith('.nii.gz')
        assert len(todo) == 2
        assert len(todo_conf) == 0

    def test_get_todo_some_completed_with_reg_files(self,tmpdir):
        open(tmpdir / "a_timeseries.tsv","x")

        todo,todo_conf = ns.get_todo(['a.nii.gz','b.nii.gz'],['a.csv','b.csv'],tmpdir)

        assert todo[0].endswith('.nii.gz')
        assert todo[-1].endswith('.nii.gz')
        assert len(todo) == 1
        assert len(todo) == len(todo_conf)

    def test_get_todo_some_completed_no_reg_files(self,tmpdir):
        open(tmpdir / "a_timeseries.tsv","x")

        todo,todo_conf = ns.get_todo(['a.nii.gz','b.nii.gz'],[],tmpdir)

        assert todo[0].endswith('.nii.gz')
        assert todo[-1].endswith('.nii.gz')
        assert len(todo) == 1
        assert len(todo_conf) == 0

    def test_get_slurm_params_n10(self):
        rtime,mem,n_jobs = ns.get_slurm_params(10,runtime=None,mem=None,n_jobs=None)
        assert rtime == '0:08:20'
        assert mem == '1G'
        assert n_jobs == 1
    
    def test_get_slurm_params_n2000(self):
        rtime,mem,n_jobs = ns.get_slurm_params(2000,runtime=None,mem=None,n_jobs=None)
        assert rtime == '0:33:20'
        assert mem == '1G'
        assert n_jobs == 10
    
    def test_get_slurm_params_n20000(self):
        rtime,mem,n_jobs = ns.get_slurm_params(20000,runtime=None,mem=None,n_jobs=None)
        assert rtime == '1:23:20'
        assert mem == '1G'
        assert n_jobs == 40
    
    def test_get_slurm_params_n2000_mem_set(self):
        rtime,mem,n_jobs = ns.get_slurm_params(2000,runtime=None,mem='5G',n_jobs=None)
        assert rtime == '0:33:20'
        assert mem == '5G'
        assert n_jobs == 10

    def test_get_slurm_params_n2000_n_jobs_set(self):
        rtime,mem,n_jobs = ns.get_slurm_params(2000,runtime=None,mem=None,n_jobs=20)
        assert rtime == '0:16:40'
        assert mem == '1G'
        assert n_jobs == 20
    
    def test_get_slurm_params_n2000_time_set(self):
        rtime,mem,n_jobs = ns.get_slurm_params(2000,runtime='1:00:00',mem=None,n_jobs=None)
        assert rtime == '1:00:00'
        assert mem == '1G'
        assert n_jobs == 5
    
    def test_get_slurm_params_n2000_time__n_jobs_set(self):
        rtime,mem,n_jobs = ns.get_slurm_params(2000,runtime='1:00:00',mem=None,n_jobs=10)
        assert rtime == '1:00:00'
        assert mem == '1G'
        assert n_jobs == 10

    def test_split_list_non_empty(self):
        a = [1,2,3,4,5,6,7]
        splits = ns.split_list(3,a)
        assert len(splits) == 3
        assert len(splits[0]) == 2
        assert len(splits[-1]) == 3

    def test_split_list_empty(self):
        splits = ns.split_list(3,[])
        assert len(splits) == 3
        assert splits[0] == []

    def test_log_batches(self,tmpdir):
        batches,_ = ns.get_batches(2,[1,2,3,4,5,6,7],[])
        os.mkdir(tmpdir/"logs")
        ns.log_batches(batches,tmpdir)

        assert os.path.exists(tmpdir / "logs/file_to_job.json")

        with open(tmpdir / "logs/file_to_job.json") as f:
            log = json.load(f)
        assert list(log.keys()) == ['0','1']

    def test_make_config(self,tmpdir):
        d = {'input_files':[],'regressor_files':[]}
        batches,batches_conf = ns.get_batches(2,[1,2,3,4,5,6,7],[])
        ns.make_config(batches,batches_conf,d,tmpdir)
        configs = [i for i in os.listdir(tmpdir) if i.endswith('.json')]
        assert len(configs) == 2

    def test_make_sh(self,tmpdir):
        os.mkdir(tmpdir / "logs")
        ns.make_sh('ACCOUNT','TIME','MEM',10,tmpdir)
        assert os.path.exists(tmpdir / 'logs/submit.sh')
        with open(tmpdir / 'logs/submit.sh', 'r') as f:
            lines = f.readlines()
        assert lines[2] == "#SBATCH --time=TIME\n"
        assert lines[-2] == "nixtract-nifti -c {}/logs/config_${{SLURM_ARRAY_TASK_ID}}.json {}\n".format(tmpdir,tmpdir)
        assert len(lines) == 9

#@pytest.fixture(scope="session")
#def fmridata(tmpdir_factory):
#    data_dir = str(tmpdir_factory.mktemp("data"))
#    data = datasets.fetch_development_fmri(n_subjects=3,data_dir=data_dir)
#    return data.func, data.confounds

#@pytest.fixture(scope="session")
#def atlas(tmpdir_factory):
#    atlas_dir = str(tmpdir_factory.mktemp("atlas"))
#    datasets.fetch_atlas_talairach('hemisphere', data_dir=atlas_dir)
#    return os.path.join(atlas_dir,'talairach_atlas/talairach.nii')

def make_test_config(batches,batches_conf,out_path):
    params = {
            "input_files": [],
            "roi_file": '/home/harveyaa/projects/def-pbellec/ATLAS/MIST/Parcellations/MIST_12.nii.gz',
            "mask_img": None,
            "labels": [],
            "regressor_files": None,
            "regressors": ['Params6'],
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

def get_test_data():
    data_base = '/home/harveyaa/nixtract-slurm_aux/development_fmri/development_fmri'
    input_files = [data_base + '/sub-pixar001_task-pixar_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz',
                    data_base + '/sub-pixar002_task-pixar_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz',
                    data_base + '/sub-pixar123_task-pixar_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz']
    conf_files = [data_base + '/sub-pixar001_task-pixar_desc-confounds_regressors.tsv',
                    data_base + '/sub-pixar002_task-pixar_desc-confounds_regressors.tsv',
                    data_base + '/sub-pixar123_task-pixar_desc-confounds_regressors.tsv']
    return input_files, conf_files

def wait_for_slurm():
    no_jobs = '          JOBID     USER      ACCOUNT           NAME  ST  TIME_LEFT NODES CPUS TRES_PER_N MIN_MEM NODELIST (REASON) \n'
    while True:
            print('Waiting for SLURM...')
            stdout = subprocess.run(['squeue','-u','harveyaa'],capture_output=True,text=True).stdout
            if stdout == no_jobs:
                print('SLURM jobs finished')
                break
            else:
                time.sleep(10)

#These can only be run on compute canada by me with my set up.
#TODO figure out why data downloaded to tmpdir_factory can't bee seen by nixtract.
class TestProgram:
    #def test_data_download(self,fmridata):
    #    input_files = fmridata[0]
    #    conf_files = fmridata[1]
    #    for i in range(3):
    #        assert os.path.exists(input_files[i])
    #        assert os.path.exists(conf_files[i])

    #def test_atlas_download(self,atlas):
    #    assert os.path.exists(atlas)

    #def test_starts(self,tmpdir,atlas,fmridata):
    #    input_files = fmridata[0]
    #    conf_files = fmridata[1]
    #    make_test_config(input_files,conf_files,tmpdir,atlas)
    #    command = "nixtract-slurm --out_path={} --config_path={}/config_0.json --account=rrg-jacquese"
    #    os.system(command.format(tmpdir,tmpdir))
    #    #check logs dir created
    #    logs_path = os.path.join(tmpdir,"logs")
    #    assert os.path.exists(logs_path)
    
    def test_no_reg_files(self,tmpdir):
        input_files,conf_files = get_test_data()
        conf_files = []
        make_test_config([input_files],[conf_files],tmpdir)

        command = "nixtract-slurm --out_path={} --config_path={}/config_0.json --account=rrg-jacquese"
        os.system(command.format(tmpdir,tmpdir))

        #check logs dir created
        logs_path = os.path.join(tmpdir,"logs")
        assert os.path.exists(logs_path)

        #check that job started
        time.sleep(5)
        no_jobs = '          JOBID     USER      ACCOUNT           NAME  ST  TIME_LEFT NODES CPUS TRES_PER_N MIN_MEM NODELIST (REASON) \n'
        stdout = subprocess.run(['squeue','-u','harveyaa'],capture_output=True,text=True).stdout
        assert stdout != no_jobs

        wait_for_slurm()

        #check tmp configs deleted
        configs = [i for i in os.listdir(logs_path) if i.startswith('config')]
        assert len(configs) == 0

        #check output exists
        timeseries = [i for i in os.listdir(tmpdir) if i.endswith('_timeseries.tsv')]
        assert len(timeseries) == 3
    
    def test_with_reg_files(self,tmpdir):
        input_files,conf_files = get_test_data()
        make_test_config([input_files],[conf_files],tmpdir)

        command = "nixtract-slurm --out_path={} --config_path={}/config_0.json --account=rrg-jacquese"
        os.system(command.format(tmpdir,tmpdir))

        #check logs dir created
        logs_path = os.path.join(tmpdir,"logs")
        assert os.path.exists(logs_path)

        #check that job started
        time.sleep(5)
        no_jobs = '          JOBID     USER      ACCOUNT           NAME  ST  TIME_LEFT NODES CPUS TRES_PER_N MIN_MEM NODELIST (REASON) \n'
        stdout = subprocess.run(['squeue','-u','harveyaa'],capture_output=True,text=True).stdout
        assert stdout != no_jobs

        wait_for_slurm()

        #check tmp configs deleted
        configs = [i for i in os.listdir(logs_path) if i.startswith('config')]
        assert len(configs) == 0

        #check output exists
        timeseries = [i for i in os.listdir(tmpdir) if i.endswith('_timeseries.tsv')]
        assert len(timeseries) == 3

    def test_one_completed(self,tmpdir):
        input_files,conf_files = get_test_data()
        make_test_config([input_files],[conf_files],tmpdir)

        #make blank timeseries output
        tsv = open(tmpdir +  "/sub-pixar001_task-pixar_space-MNI152NLin2009cAsym_desc-preproc_bold_timeseries.tsv","x")
        tsv.close()

        command = "nixtract-slurm --out_path={} --config_path={}/config_0.json --account=rrg-jacquese"
        os.system(command.format(tmpdir,tmpdir))

        #check logs dir created
        logs_path = os.path.join(tmpdir,"logs")
        assert os.path.exists(logs_path)

        #check that job started
        time.sleep(5)
        no_jobs = '          JOBID     USER      ACCOUNT           NAME  ST  TIME_LEFT NODES CPUS TRES_PER_N MIN_MEM NODELIST (REASON) \n'
        stdout = subprocess.run(['squeue','-u','harveyaa'],capture_output=True,text=True).stdout
        assert stdout != no_jobs

        wait_for_slurm()

        #check tmp configs deleted
        configs = [i for i in os.listdir(logs_path) if i.startswith('config')]
        assert len(configs) == 0

        #check output exists
        timeseries = [i for i in os.listdir(tmpdir) if i.endswith('_timeseries.tsv')]
        assert len(timeseries) == 3

        #check fake output still blank
        tsv = csv.reader(open(tmpdir + "/sub-pixar001_task-pixar_space-MNI152NLin2009cAsym_desc-preproc_bold_timeseries.tsv"),delimiter="\t")
        assert len(list(tsv)) == 0

    def test_two_batches(self,tmpdir):
        input_files,conf_files = get_test_data()
        make_test_config([input_files],[conf_files],tmpdir)

        command = "nixtract-slurm --out_path={} --config_path={}/config_0.json --account=rrg-jacquese --n_jobs=2"
        os.system(command.format(tmpdir,tmpdir))

        #check logs dir created
        logs_path = os.path.join(tmpdir,"logs")
        assert os.path.exists(logs_path)

        #check that job started
        time.sleep(5)
        no_jobs = '          JOBID     USER      ACCOUNT           NAME  ST  TIME_LEFT NODES CPUS TRES_PER_N MIN_MEM NODELIST (REASON) \n'
        stdout = subprocess.run(['squeue','-u','harveyaa'],capture_output=True,text=True).stdout
        assert stdout != no_jobs

        wait_for_slurm()

        #check tmp configs deleted
        configs = [i for i in os.listdir(logs_path) if i.startswith('config')]
        assert len(configs) == 0

        #check output exists
        timeseries = [i for i in os.listdir(tmpdir) if i.endswith('_timeseries.tsv')]
        assert len(timeseries) == 3



