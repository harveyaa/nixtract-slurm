import time
import nixtract
import os

def time_nixtract(path_out):
    start = time.time()
    os.system('nixtract-nifti -c config_test.json {}'.format(path_out))
    dur = time.time() - start
    return dur