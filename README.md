![](doc/pnl-bwh-hms.png)
10.5281/zenodo.3451427

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.3451427.svg)](https://doi.org/10.5281/zenodo.3451427) [![Python](https://img.shields.io/badge/Python-3.6-green.svg)]() [![Platform](https://img.shields.io/badge/Platform-linux--64%20%7C%20osx--64-orange.svg)]()

*multi-shell-dMRIharmonization* repository is developed by Tashrif Billah and Yogesh Rathi, Brigham and Women's Hospital (Harvard Medical School).

*multi-shell-dMRIharmonization* is an extension of [dMRIharmonization](https://github.com/pnlbwh/dMRIharmonization) for single-shell dMRI.


Table of Contents
=================

   * [Algorithm](#algorithm)
   * [Citation](#citation)
   * [Dependencies](#dependencies)
   * [Installation](#installation)
      * [1. Install prerequisites](#1-install-prerequisites)
         * [Check system architecture](#check-system-architecture)
         * [Python 3](#python-3)
         * [MATLAB Runtime Compiler](#matlab-runtime-compiler)
         * [unringing](#unringing)
      * [2. Install pipeline](#2-install-pipeline)
      * [3. Download IIT templates](#3-download-iit-templates)
      * [4. Configure your environment](#4-configure-your-environment)
   * [Running](#running)
   * [Consistency checks](#consistency-checks)
   * [Varying number of gradients](#varying-number-of-gradients)
   * [Sample commands](#sample-commands)
      * [Create template](#create-template)
      * [Harmonize data](#harmonize-data)
      * [Debug](#debug)
   * [Tests](#tests)
      * [1. pipeline](#1-pipeline)
      * [2. unittest](#2-unittest)
   * [Preprocessing](#preprocessing)
      * [1. Denoising](#1-denoising)
      * [2. Bvalue mapping](#2-bvalue-mapping)
      * [3. Resampling](#3-resampling)
   * [Debugging](#debugging)
      * [1. With the pipeline](#1-with-the-pipeline)
      * [2. Use separately](#2-use-separately)
   * [Caveats/Issues](#caveatsissues)
      * [1. Template path](#1-template-path)
      * [2. Multi-processing](#2-multi-processing)
      * [3. X forwarding error](#3-x-forwarding-error)
      * [4. Tracker](#4-tracker)
   * [Reference](#reference)

Table of Contents created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc)



# Algorithm

1. Extract b-shells from given data
2. Check consistency among bshells and spatial resolution
3. Create ANTs template from highest b-shell
4. Apply the warps and affines obtained from previous step to compute scale maps for all b-shells
5. Template creation being complete, harmonize data for each b-shell using scale maps corresponding to that b-shell
6. Join the harmonized data in the same order of bvalues as that of the given data

Template creation and data harmonization process mentioned in steps 3-5 are described in detail at 
single shell counterpart of the program:

https://github.com/pnlbwh/dMRIharmonization#template-creation

https://github.com/pnlbwh/dMRIharmonization#data-harmonization


# Citation

If this repository is useful in your research, please cite all of the following: 

* Billah T, Rathi Y. Multi-site multi-shell Diffusion MRI Harmonization,
https://github.com/pnlbwh/multi-shell-dMRIharmoniziation, 2019, doi: 10.5281/zenodo.3451427


* Billah T*, Cetin Karayumak S*, Bouix S, Rathi Y. Multi-site Diffusion MRI Harmonization, 
https://github.com/pnlbwh/dMRIharmoniziation, 2019, doi: 10.5281/zenodo.3451427

    \* *denotes equal first authroship*


* Cetin Karayumak S, Bouix S, Ning L, James A, Crow T, Shenton M, Kubicki M, Rathi Y. Retrospective harmonization of multi-site diffusion MRI data 
acquired with different acquisition parameters. Neuroimage. 2019 Jan 1;184:180-200. 
doi: 10.1016/j.neuroimage.2018.08.073. Epub 2018 Sep 8. PubMed PMID: 30205206; PubMed Central PMCID: PMC6230479.


* Mirzaalian H, Ning L, Savadjiev P, Pasternak O, Bouix S, Michailovich O, Karmacharya S, Grant G, Marx CE, Morey RA, Flashman LA, George MS, 
McAllister TW, Andaluz N, Shutter L, Coimbra R, Zafonte RD, Coleman MJ, Kubicki M, Westin CF, Stein MB, Shenton ME, Rathi Y. 
Multi-site harmonization of diffusion MRI data in a registration framework. Brain Imaging Behav. 2018 Feb;12(1):284-295. 
doi:10.1007/s11682-016-9670-y. PubMed PMID: 28176263.


# Dependencies

* ANTs = 2.2.0
* reisert/unring
* FSL = 5.0.11
* numpy = 1.16.2
* scipy = 1.2.1
* scikit-image = 0.15.0
* dipy = 0.16.0
* nibabel = 2.3.0
* pynrrd = 0.3.6
* conversion = 2.0

**NOTE** The above versions were used for developing the repository. However, *multi-shell-dMRIharmonization* should work on 
any advanced version. 


# Installation

## 1. Install prerequisites

You may ignore installation instruction for any software module that you have already.

### Check system architecture

    uname -a # check if 32 or 64 bit

### Python 3

Download [Miniconda Python 3.6 bash installer](https://docs.conda.io/en/latest/miniconda.html) (32/64-bit based on your environment):
    
    sh Miniconda3-latest-Linux-x86_64.sh -b # -b flag is for license agreement

Activate the conda environment:

    source ~/miniconda3/bin/activate # should introduce '(base)' in front of each line



**NOTE** With the current design, *MATLAB Runtime Compiler* and *unringing* are not used. So, you may pass them.
    
### MATLAB Runtime Compiler

In the harmonization process, all volumes have to be resampled to a common spatial resolution. 
We have chosen bspline as the interpolation method. For better result, bspline order has been chosen to be 7. 
Since Python and ANTs provide bspline order less than or equal to 5, we have resorted to [spm package](https://github.com/spm/spm12) for this task.
Using their source codes [bspline.c](https://github.com/spm/spm12/blob/master/src/spm_bsplinc.c) and [bsplins.c](https://github.com/spm/spm12/blob/master/src/spm_bsplins.c), 
we have made a standalone executable that performs the above interpolation. Execution of the standalone executable 
requires [MATLAB Runtime Compiler](https://www.mathworks.com/products/compiler/matlab-runtime.html). It is available free of charge.
Download a suitable version from the above, and install as follows:

    unzip MCR_R2017a_glnxa64_installer.zip -d MCR_R2017a_glnxa64/
    MCR_R2017a_glnxa64/install -mode silent -agreeToLicense yes -destinationFolder `pwd`/MATLAB_Runtime
    

See details about installation [here](https://www.mathworks.com/help/compiler/install-the-matlab-runtime.html).

After successful installation, you should see a suggestion about editing your LD_LIBRARY_PATH. 
You should save the suggestion in a file `env.sh`.

    echo "/path/to/v92/runtime/glnxa64:/path/to/v92/bin/glnxa64:/path/to/v92/sys/os/glnxa64:/path/to/v92/opengl/lib/glnxa64:" > env.sh

Then, every time you run dMRIharmonization, you can just source the `env.sh` for your LD_LIBRARY_PATH to be updated.

**NOTE** If you have MATLAB already installed in your system, replace `/path/to/v92` with `/path/to/Matlab/`


### unringing

    git clone https://bitbucket.org/reisert/unring.git
    cd unring/fsl
    export PATH=$PATH:`pwd`

You should be able to see the help message now:

    unring.a64 --help


**NOTE** FSL unringing executable requires Centos7 operating system.
    
    
## 2. Install pipeline

Now that you have installed the prerequisite software, you are ready to install the pipeline:

    git clone https://github.com/pnlbwh/multi-shell-dMRIharmonization.git && cd multi-shell-dMRIharmonization
    conda env create -f environment.yml    # you may comment out any existing package from environment.yml
    conda activate harmonization           # should introduce '(harmonization)' in front of each line


Alternatively, if you already have ANTs, you can continue using your python environment by directly installing 
the prerequisite libraries:

    pip install -r requirements.txt --upgrade




## 3. Download IIT templates

dMRIharmonization toolbox is provided with a debugging capability to test how good has been the 
harmonization. For debug to work and **tests** to run, download the following data from [IIT HUMAN BRAIN ATLAS](http://www.iit.edu/~mri/IITHumanBrainAtlas.html) 
and place them in `multi-shell-dMRIharmonization/IITAtlas/` directory:

* [IITmean_FA.nii.gz](https://www.nitrc.org/frs/download.php/6898/IITmean_FA.nii.gz) 
* [IITmean_FA_skeleton.nii.gz](https://www.nitrc.org/frs/download.php/6897/IITmean_FA_skeleton.nii.gz)


## 4. Configure your environment

Make sure the following executables are in your path:

    antsMultivariateTemplateConstruction2.sh
    antsApplyTransforms
    antsRegistrationSyNQuick.sh
    unring.a64
    
You can check them as follows:

    which dtifit
    
If any of them does not exist, add that to your path:

    export PATH=$PATH:/directory/of/executable
    
`conda activate harmonization` should already put the ANTs scripts in your path. Yet, you should set ANTSPATH as follows:
    
    export ANTSPATH=~/miniconda3/envs/harmonization/bin/

However, if you choose to use pre-installed ANTs scripts, you can define `ANTSPATH` according to [this](https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS#set-path-and-antspath) instruction.




# Running

Upon successful installation, you should be able to see the help message:

> lib/multi-shell-harmonization.py --help


    Usage:
        multi-shell-harmonization.py [SWITCHES] 
    
    Meta-switches:
        -h, --help                         Prints this help message and quits
        --help-all                         Prints help messages of all sub-commands and quits
        -v, --version                      Prints the program's version and quits
    
    Switches:
        --create                           turn on this flag to create template
        --debug                            turn on this flag to debug harmonized data (valid only with --process)
        --force                            turn on this flag to overwrite existing data
        --nproc VALUE:str                  number of processes/threads to use (-1 for all available, may slow down your system);
                                           the default is 4
        --nshm VALUE:str                   spherical harmonic order, by default maximum possible is used; the default is -1
        --nzero VALUE:str                  number of zero padding for denoising skull region during signal reconstruction; the
                                           default is 10
        --process                          turn on this flag to harmonize
        --ref_list VALUE:ExistingFile      reference csv/txt file with first column for dwi and 2nd column for mask:
                                           dwi1,mask1\ndwi2,mask2\n...
        --ref_name VALUE:str               reference site name; required
        --tar_list VALUE:ExistingFile      target csv/txt file with first column for dwi and 2nd column for mask:
                                           dwi1,mask1\ndwi2,mask2\n...
        --tar_name VALUE:str               target site name; required
        --template VALUE:str               template directory; required
        --travelHeads                      travelling heads
        --verbose                          print everything to STDOUT



For details about the above arguments, see https://github.com/pnlbwh/dMRIharmonization#running



# Consistency checks

A few consistency checks are run to make sure provided data is eligible for harmonization.

1. First image from the reference site is used as reference for all images in reference and target sites. B-shells and 
spatial resolution are extracted from the reference image. The b-shells and spatial resolution are compared against all 
images in reference and target sites. As long as all bvalues of each image falls within +-100 of a b-shell bvalue, the 
image is considered good for harmonization.

2. Spatial resolution should match exactly. If reference image has 2x2x2 resolution, all other images should also have 
this resolution.

3. The program can automatically determine [maximum possible spherical harmonic order](https://github.com/pnlbwh/dMRIharmonization#order-of-spherical-harmonics) (`--nshm`) for each b-shell.
However, if a value is provided with `--nshm`, it is compared against the maximum possible spherical harmonic order to 
continue.


In the event of inconsistency, the program will raise and error and user should remove the case from provided lists 
and try again. 


# Varying number of gradients

A particular strength of the algorithm is its compatiblity with varying number of gradients present in images.
As long as [the number of gradients satisfies minimum required](https://github.com/pnlbwh/dMRIharmonization#order-of-spherical-harmonics) for the spherical harmonic order, determined (`--nshm -1`) 
or provided(--nshm 4), data can be harmonized.


# Sample commands

## Create template

    multi-shell-dMRIharmonization/lib/multi-shell-harmonization.py --ref_list ref_list.txt --tar_list tar_list.txt 
    --ref_name REF --tar_name TAR --template template
    --create


## Harmonize data

    multi-shell-dMRIharmonization/lib/multi-shell-harmonization.py --tar_list tar_list.txt 
    --ref_name REF --tar_name TAR --template template
    --process
    
    multi-shell-dMRIharmonization/lib/multi-shell-harmonization.py --tar_list tar_list.txt 
    --ref_name REF --tar_name TAR --template template
    --process --debug


## Debug

Runs together with `--create` and `--process`

    multi-shell-dMRIharmonization/lib/multi-shell-harmonization.py --ref_list ref_list.txt --tar_list tar_list.txt 
    --ref_name REF --tar_name TAR --template template
    --create --process --debug



# Tests

A small test data is provided with each [release](https://github.com/pnlbwh/multi-shell-dMRIharmonization/releases). 


## 1. pipeline
You may test the whole pipeline as follows:
    
    cd multi-shell-dMRIharmonization/lib/tests
    ./multi_pipeline_test.sh
    
**NOTE** Running the above tests might take six hours.


\* If there is any problem downloading test data, try manually downloading and unzipping it to `lib/tests/` folder.


## 2. unittest
You may run smaller and faster unittest as follows:
    
    python -m unittest discover -v lib/tests/
    
**TBD** This section will be expanded in future.


# Preprocessing

Unlike single-shell dMRIharmonization, multi-shell-dMRIharmonization does **NOT** support data preprocessing as of now. 
This is likely to change in a future release. Hence, the following arguments are present for legacy purpose but you 
should not use them.

## 1. Denoising
    
    --denoise        # turn on this flag to denoise voxel data

## 2. Bvalue mapping

    --bvalMap VALUE  # specify a bmax to scale bvalues into    

## 3. Resampling

    --resample VALUE # voxel size MxNxO to resample into


After preprocessing, the image lists are saved with `.modified` extension in the same location of provided lists, 
and used for further processing.
 



# Debugging

multi-shell-dMRIharmonization debugging is an extension of [dMRIharmonization debugging](https://github.com/pnlbwh/dMRIharmonization#debugging). In the former case, debugging is 
run at each shell separately. So, at each shell you should see nearly matching mean FA over IITmean_FA_skeleton.nii.gz 
between reference site and target site after harmonization:

    REF mean FA:  0.5217237675408243
    TAR mean FA before harmonization:  0.5072286796848892
    REF mean FA after harmonization:  0.5321998242139347


## 1. With the pipeline

`--debug` should run together with `--create` and `--process` since information from reference and target sites are used 
to obtain the above summary. 


## 2. Use separately

However, if you would like to debug separately or if your target site has more cases than the ones used in template creation, 
we provide you a way to debug manually. `lib/test/fa_skeleton_test.py` script registers each subject FA (reference, 
target before harmonization, and after harmonization), to template space and then to MNI space.


    usage: fa_skeleton_test.py [-h] -i INPUT -s SITE -t TEMPLATE --bshell_b
                               BSHELL_B [--ncpu NCPU]
    
    Warps diffusion measures (FA, MD, GFA) to template space and then to MNI
    space. Finally, calculates mean FA over IITmean_FA_skeleton.nii.gz
    
    optional arguments:
      -h, --help            show this help message and exit
      -i INPUT, --input INPUT
                            input list of FA images
      -s SITE, --site SITE  site name for locating template FA and mask in
                            tempalte directory
      -t TEMPLATE, --template TEMPLATE
                            template directory where Mean_{site}_FA.nii.gz and
                            {site}_Mask.nii.gz is located
      --bshell_b BSHELL_B   bvalue of the bshell
      --ncpu NCPU           number of cpus to use
  
  
Finally, it should print mean FA statistics like above.

`lib/test/fa_skeleton_test.py` performs two registrations:

(i) Subject to site template space

(ii) Site template to MNI space

Thus, subject data is brought to MNI space for comparison. For reference site, it is a straightforward process.
However, for target site, there are two kinds of data: given and harmonized. Since given data and harmonized data reside 
in the same space, registration is performed only once. The script is intelligent enough to exploit relevant registration 
files if registration was performed before.

In multi-shell-dMRIharmonization approach, registration is performed with highest b-shell. Obtained transform files 
are used to warp rest of the b-shells.


# Caveats/Issues

## 1. Template path

`antsMultivariateTemplateConstruction2.sh`: all the images need to have unique
prefix because transform files are created in the same `--template ./template/` directory. The value of `--template` 
should have `/` at the end. The pipeline appends one if there is not, but it is good to include it when specifying.

## 2. Multi-processing

[Multi threading](#-multi-threading) requires memory and processor availability. If pipeline does not continue past 
`unringing` or `shm_coeff` computation, your machine likely ran out of memory. Reducing `--nproc` to lower number of processors (i.e. 1-4) 
or swithcing to a powerful machine should help in this regard.


## 3. X forwarding error

Standalone MATLAB executable `bspline` used for resampling in the pipeline, requires X forwarding to be properly set. 
If it is not properly set, you may notice error like below:
    
    X11 proxy: unable to connect to forwarded X server: Network error: Connection refused
    
Either of the following should fix that:
    
    ssh -X user@remotehost

or
    
    ssh user@remotehost
    unset DISPLAY
    
When using the latter option, be mindful that it may cause other programs requiring `$DISPLAY` 
in that particular terminal to malfunction.
    

## 4. Tracker

In any case, feel free to submit an issue [here](https://github.com/pnlbwh/multi-shell-dMRIharmonization/issues). We shall get back to you as soon as possible.

# Reference

Zhang S, Arfanakis K. Evaluation of standardized and study-specific diffusion tensor imaging templates 
of the adult human brain: Template characteristics, spatial normalization accuracy, and detection of small 
inter-group FA differences. Neuroimage 2018;172:40-50.

Billah, Tashrif; Bouix, Sylvain; Rathi, Yogesh; Various MRI Conversion Tools, 
https://github.com/pnlbwh/conversion, 2019, DOI: 10.5281/zenodo.2584003.

