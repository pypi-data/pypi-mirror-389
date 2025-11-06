#!/usr/bin/env bash

source /cvmfs/sft.cern.ch/lcg/releases/LCG_102b/Python/3.9.12/x86_64-centos7-gcc11-opt/Python-env.sh
export PYTHONPATH=$path_to_python_dependencies
export PYTHONNOUSERSITE=1
cd $code_location
python $code_location/availsim4.py --system $system_file_location --simulation $simulation_file_location --output_folder $output_folder $other_availsim_arguments
