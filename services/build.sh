#!/bin/bash

# Script dir
scriptDir=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd )
echo "Current script dir: ${scriptDir}"

# Need to build a custom image for the Jupyter notebook since it has some dependencies
docker build -f "${scriptDir}/Dockerfile.jupyter.txt" -t 'msds_data_mgmt_t12_final_project/jupyter:latest' ${scriptDir}