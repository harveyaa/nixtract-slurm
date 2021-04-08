#import nixtract
import nslurm.nslurm as ns
import json
import pytest
import os
import tempfile
from nilearn import datasets


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
        ls = ns.check_glob(tmpdir / '*.py')
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
        time,mem,n_jobs = ns.get_slurm_params(10,None,None,None)
        assert time == '30:00'
        assert mem == '1G'
        assert n_jobs == 1
    
    def test_get_slurm_params_n2000(self):
        time,mem,n_jobs = ns.get_slurm_params(2000,None,None,None)
        assert time == '1:00:00'
        assert mem == '2G'
        assert n_jobs == 20
    
    def test_get_slurm_params_n20000(self):
        time,mem,n_jobs = ns.get_slurm_params(20000,None,None,None)
        assert time == '2:00:00'
        assert mem == '3G'
        assert n_jobs == 40

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
        ns.log_batches(batches,tmpdir)

        assert os.path.exists(tmpdir / "file_to_job.json")

        with open(tmpdir / "file_to_job.json") as f:
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

@pytest.fixture(scope="session")
def fmridata(tmpdir_factory):
    data_dir = str(tmpdir_factory.mktemp("data"))
    data = datasets.fetch_development_fmri(n_subjects=3,data_dir=data_dir)
    return data.func, data.confounds

@pytest.fixture(scope="session")
def atlas(tmpdir_factory):
    atlas_dir = str(tmpdir_factory.mktemp("atlas"))
    datasets.fetch_atlas_talairach('hemisphere', data_dir=atlas_dir)
    return os.path.join(atlas_dir,'talairach_atlas/talairach.nii')

class TestProgram:
    def test_data_download(self,fmridata):
        input_files = fmridata[0]
        conf_files = fmridata[1]
        for i in range(3):
            assert os.path.exists(input_files[i])
            assert os.path.exists(conf_files[i])

    def test_atlas_download(self,atlas):
        assert os.path.exists(atlas)

    def test_with_reg_files_none_completed(self):
        assert True
    
    def test_no_reg_files_none_completed(self):
        assert True

    def test_with_reg_files_some_completed(self):
        assert True
    
    def test_no_reg_files_some_completed(self):
        assert True
