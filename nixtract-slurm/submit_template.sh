#!/bin/bash
#SBATCH --job-name=nixtract-slurm
#SBATCH --time=$time
#SBATCH --mem=$mem
#SBATCH --account=$account
#SBATCH --array=0-$n_jobs
#SBATCH -o $out_path/logs/slurm_output/batch_%a.out

$command -c $out_path/logs/config_$${SLURM_ARRAY_ID}.json $out_path

rm $out_path/logs/config_*.json