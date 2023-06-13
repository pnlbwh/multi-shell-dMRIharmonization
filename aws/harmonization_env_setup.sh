#!/bin/bash

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    chmod +x Miniconda3-latest-Linux-x86_64.sh
    sh Miniconda3-latest-Linux-x86_64.sh -b
    echo 'source ~/miniconda3/bin/activate' >> ~/.bashrc
    source ~/.bashrc
fi

# Check if MCR is installed
if [ ! -d "/usr/local/MATLAB/MATLAB_Runtime/v92" ]; then
    wget https://ssd.mathworks.com/supportfiles/downloads/R2017a/deployment_files/R2017a/installers/glnxa64/MCR_R2017a_glnxa64_installer.zip
    unzip MCR_R2017a_glnxa64_installer.zip -d MCR_R2017_glnxa64/
    sudo MCR_R2017_glnxa64/install -mode silent -agreeToLicense yes
    echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/MATLAB/MATLAB_Runtime/v92/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v92/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v92/sys/os/glnxa64:' >> ~/.bashrc
    source ~/.bashrc
fi

# Check if MCR update is installed
if ! find /usr/local/MATLAB/MATLAB_Runtime/v92 -name "MCR_R2017a_Update_3_glnxa64.sh" &> /dev/null; then
    wget https://ssd.mathworks.com/supportfiles/downloads/R2017a/deployment_files/R2017a/installers/glnxa64/MCR_R2017a_Update_3_glnxa64.sh
    chmod +x MCR_R2017a_Update_3_glnxa64.sh
    yes | sudo ./MCR_R2017a_Update_3_glnxa64.sh
fi

# Check if unring is cloned
if [ ! -d "~/unring" ]; then
    git clone https://bitbucket.org/reisert/unring.git
    cd unring/fsl || exit
    echo 'export PATH=$PATH:~/unring/fsl' >> ~/.bashrc
fi

# Check if fftw-libs-double is installed
if ! yum list installed fftw-libs-double &> /dev/null; then
    sudo yum install fftw-libs-double -y
fi

# Check if multi-shell-dMRIharmonization is cloned
if [ ! -d "~/multi-shell-dMRIharmonization" ]; then
    git clone https://github.com/RyanZurrin/multi-shell-dMRIharmonization.git
    cd multi-shell-dMRIharmonization || exit
fi

# Check if the conda environment exists
if ! conda env list | grep -q 'harmonization'; then
    conda env create -f environment.yml
fi

# Provide instructions to activate the environment
echo "To activate the environment, use the command: conda activate harmonization"