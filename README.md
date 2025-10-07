![](doc/pnl-bwh-hms.png)

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.3451427.svg)](https://doi.org/10.5281/zenodo.3451427) [![Python](https://img.shields.io/badge/Python-3.8-green.svg)]() [![Platform](https://img.shields.io/badge/Platform-linux--64%20%7C%20osx--64-orange.svg)]()

*multi-shell-dMRIharmonization* repository is developed by Tashrif Billah and Yogesh Rathi, Brigham and Women's Hospital (Harvard Medical School).

*multi-shell-dMRIharmonization* is an extension of single-shell dMRIharmonization.


Table of Contents
=================

   * [Algorithm](#algorithm)
   * [Citation](#citation)
   * [Requirements for data](#requirements-for-data)
   * [Installation](#installation)
   * [Running](#running)
   * [Consistency checks](#consistency-checks)
   * [Varying number of gradients](#varying-number-of-gradients)
   * [Sample commands](#sample-commands)
      * [Create template](#create-template)
      * [Harmonize data](#harmonize-data)
      * [Debug](#debug)
         * [1. Same target list](#1-same-target-list)
         * [2. Different target list](#2-different-target-list)
   * [Tests](#tests)
      * [1. Multi shell](#1-multi-shell)
      * [2. Single shell](#2-single-shell)
   * [Preprocessing](#preprocessing)
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

* Billah T, Cetin Karayumak S, Bouix S, Rathi Y. Multi-site multi-shell Diffusion MRI Harmonization,
https://github.com/pnlbwh/multi-shell-dMRIharmonization, 2019, doi: 10.5281/zenodo.3451427


* Cetin Karayumak S, Bouix S, Ning L, James A, Crow T, Shenton M, Kubicki M, Rathi Y. Retrospective harmonization of multi-site diffusion MRI data 
acquired with different acquisition parameters. Neuroimage. 2019 Jan 1;184:180-200. 
doi: 10.1016/j.neuroimage.2018.08.073. Epub 2018 Sep 8. PubMed PMID: 30205206; PubMed Central PMCID: PMC6230479.


* Mirzaalian H, Ning L, Savadjiev P, Pasternak O, Bouix S, Michailovich O, Karmacharya S, Grant G, Marx CE, Morey RA, Flashman LA, George MS, 
McAllister TW, Andaluz N, Shutter L, Coimbra R, Zafonte RD, Coleman MJ, Kubicki M, Westin CF, Stein MB, Shenton ME, Rathi Y. 
Multi-site harmonization of diffusion MRI data in a registration framework. Brain Imaging Behav. 2018 Feb;12(1):284-295. 
doi:10.1007/s11682-016-9670-y. PubMed PMID: 28176263.


# Requirements for data

1. Two groups of data from- *reference* and *target* sites are required. Control (healthy) subjects should be present 
in each site.

2. The groups between the sites should be very well matched for age, sex, socio-economic status, IQ and any other 
demographic variable.

3. A minimum of 16 subjects is required from each site for proper harmonization (so a minimum of 32 subjects in total).

4. The data should be curated with the following steps prior to harmonization: 
    
    (i) axis alignment and centering
    
    (ii) signal dropped gradient removal
    
    (iii) eddy current and head motion correction
    
5. b-values in each b-shell should have similar b-values (i.e, if one site has b-value 1000, 
the other one should have in the range [900,1100]).


If your data does not satisfy these requirements, please open an issue [here](https://github.com/pnlbwh/multi-shell-dMRIharmonization/issues) or contact -

*skarayumak[at]bwh[dot]harvard[dot]edu*

*tbillah[at]bwh[dot]harvard[dot]edu*



# Installation

Step-by-step installation instruction can be found [here](https://github.com/pnlbwh/dMRIharmonization/blob/9266b1c753ca0270562e57ee4450ac21c98ce8be/README.md).
But for ease of use, we provide a [Singularity](Singularity) container. Download it as:

    wget "https://www.dropbox.com/scl/fi/onkvy3gdvw99m05v0c52q/dMRIharmonization.sif?rlkey=qptch5779p0h9y3vkz55v0s9g&st=inlduybh&dl=0" -O dMRIharmonization.sif

You should bind your data and shell into the container to use it:

    singularity shell -B /path/to/data:/path/to/data dMRIharmonization.sif
    cd /home/pnlbwh/multi-shell-dMRIharmonization/lib
    ./multi-shell-harmonization.py --help
    ./harmonization.py --help


(Optional) For running tests and debugging, [download IIT templates](https://github.com/pnlbwh/dMRIharmonization/blob/9266b1c753ca0270562e57ee4450ac21c98ce8be/README.md#3-download-iit-templates)
and bind them into the container:

    singularity shell -B /path/to/data:/path/to/data \
    -B /path/to/IITAtlas:/home/pnlbwh/multi-shell-dMRIharmonization/IITAtlas/ dMRIharmonization.sif


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



`multi-shell-harmonization.py` is the one single executable for both multi-shell and single-shell data.
For details about the above arguments, see https://github.com/pnlbwh/dMRIharmonization#running.
Though the link uses `lib/harmonization.py`, the details are applicable to `multi-shell-harmonization.py` too.
However, you may use `lib/harmonization.py` for single-shell data. The former supports
`--bvalMap`, `--resample`, and `--denoise`.

<details>
<summary>lib/harmonization.py --help</summary>

    Usage:
    harmonization.py [SWITCHES] 

    Meta-switches:
        -h, --help                          Prints this help message and quits
        --help-all                          Prints help messages of all sub-commands and quits
        -v, --version                       Prints the program's version and quits

    Switches:
        --bshell_b VALUE:str                bvalue of the bshell, needed for multi-shell data only; the default is X
        --bvalMap VALUE:str                 specify a bmax to scale bvalues into
        --create                            turn on this flag to create template
        --debug                             turn on this flag to debug harmonized data (valid only with --process)
        --denoise                           turn on this flag to denoise voxel data
        --force                             turn on this flag to overwrite existing data
        --harm_list VALUE:ExistingFile      harmonized csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\n dwi2,mask2\n...
        --nproc VALUE:str                   number of processes/threads to use (-1 for all available, may slow down your system); the default is 4
        --nshm VALUE:str                    spherical harmonic order, by default maximum possible is used; the default is -1
        --nzero VALUE:str                   number of zero padding for denoising skull region during signal reconstruction; the default is 10
        --process                           turn on this flag to harmonize
        --ref_list VALUE:ExistingFile       reference csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\n dwi2,mask2\n...
        --ref_name VALUE:str                reference site name
        --resample VALUE:str                voxel size MxNxO to resample into
        --tar_list VALUE:ExistingFile       target csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\n dwi2,mask2\n...
        --tar_name VALUE:str                target site name; required
        --template VALUE:str                template directory; required
        --travelHeads                       travelling heads
        --verbose                           print everything to STDOUT

</details>


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
    --tar_name TAR --template template
    --process
    
    multi-shell-dMRIharmonization/lib/multi-shell-harmonization.py --tar_list tar_list.txt 
    --tar_name TAR --template template
    --process --debug


## Debug

### 1. Same target list

Run together with `--create` and `--process`:

    multi-shell-dMRIharmonization/lib/multi-shell-harmonization.py --ref_list ref_list.txt --tar_list tar_list.txt 
    --ref_name REF --tar_name TAR --template template
    --create --process --debug


### 2. Different target list

In theory, you want to create a template with small number of data from each sites and then use the template to 
harmonize all of your data in the target site. Since the data for template creation and harmonization are not same, 
we don't have luxury of using `--create --process --debug` altogether. Instead, you would use `--debug` with each of 
`--create` and `--process`. The `--debug` flag creates some files that are used to obtain statistics later.
The steps are described below:

(i) Create template with `--debug` enabled:
    
    multi-shell-dMRIharmonization/lib/multi-shell-harmonization.py --ref_list ref_list.txt --tar_list tar_small_list.txt 
    --ref_name REF --tar_name TAR --template template
    --create --debug

(ii) Harmonize data with `--debug` enabled:

    multi-shell-dMRIharmonization/lib/multi-shell-harmonization.py --tar_list tar_list.txt 
    --tar_name TAR --template template
    --process --debug

(iii) Obtain statistics
    
    ## reference site ##
    
    # start with highest bvalue shell
    
    multi-shell-dMRIharmonization/lib/tests/fa_skeleton_test.py 
    -i ref_list_b3000.csv.modified -s REF 
    -t template/ --bshell_b 3000    
    
    # repeat for other non-zero bvalues
    
    multi-shell-dMRIharmonization/lib/tests/fa_skeleton_test.py 
    -i ref_list_b2000.csv.modified -s REF 
    -t template/ --bshell_b 2000
    
    multi-shell-dMRIharmonization/lib/tests/fa_skeleton_test.py 
    -i ref_list_b1000.csv.modified -s REF 
    -t template/ --bshell_b 1000

    ...
    ...
    
    
    
    ## target site before harmonization ##
    
    # again, start with highest bvalue shell, notice the absence of ".modified" at the end of -i
    
    multi-shell-dMRIharmonization/lib/tests/fa_skeleton_test.py 
    -i tar_list_b3000.csv -s TAR 
    -t template/ --bshell_b 3000
    
    # repeat for other non-zero bvalues
    
    ...
    ...
    
    
    
    ## target site after harmonization ##
    
    # once again, start with highest bvalue shell, notice the presence of ".modified.harmonized" at the end of -i
    
    multi-shell-dMRIharmonization/lib/tests/fa_skeleton_test.py 
    -i tar_list_b3000.csv.modified.harmonized -s TAR 
    -t template/ --bshell_b 3000
    
    # repeat for other non-zero bvalues
    ...
    ...



# Tests

## 1. Multi shell

A small test data is provided via [Dropbox](https://www.dropbox.com/scl/fi/lx4d6vslyzs64rehbki45/multi-harm-test.zip?rlkey=0ox9pmg3gu04xs6hzl6jvctgt&st=o2qlfxn0).
Instruction for running tests can be found [here](lib/tests/README.md).

Success of this test will confirm that your environment is properly set up to run multi-shell-dMRIharmonization.

## 2. Single shell

For this test, you should<sup>~</sup> clone the single-shell [software](https://github.com/pnlbwh/dMRIharmonization).
But you can use the same bash environment that you have set up for multi-shell software.
A small test data is provided with each [release](https://github.com/pnlbwh/dMRIharmonization/releases).
Instruction for running tests can be found [here](https://github.com/pnlbwh/dMRIharmonization?tab=readme-ov-file#1-pipeline).

<sup>~</sup> This wiki explains why multi-shell software will not produce good results for single-shell test.

# Preprocessing

Since the beginning of multi-shell-dMRIharmonization development,
it is expected that multi-shell DWIs are matched by bvalues and resolution.
Hence, `--bvalMap`, `--resample`, `--denoise` flags are not supported for `multi-shell-harmonization.py`.
This is likely to change in a future release.

However, you can use these options with `harmonization.py`.
See [here](https://github.com/pnlbwh/dMRIharmonization/tree/master?tab=readme-ov-file#preprocessing) for details.


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
we provide you a way to debug manually. Firstly, make sure to harmonize data with `--debug` flag enabled. The flag will 
create diffusion measures that are used in debugging later. Then, `lib/test/fa_skeleton_test.py` script can register 
each subject FA (reference, target before harmonization, and after harmonization), to template space and then to MNI space.


    usage: fa_skeleton_test.py [-h] -i INPUT -s SITE -t TEMPLATE --bshell_b
                               BSHELL_B [--ncpu NCPU]
    
    Warps diffusion measures (FA, MD, GFA) to template space and then to MNI
    space. Finally, calculates mean FA over IITmean_FA_skeleton.nii.gz
    
    optional arguments:
      -h, --help            show this help message and exit
      -i INPUT, --input INPUT
                            a .txt/.csv file that you used in/obtained from
                            harmonization.py having two columns for (img,mask)
                            pair. See pnlbwh/dMRIharmonization documentation for
                            more details
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
are used to warp rest of the b-shells. See [Different target list](#2-different-target-list) for details.


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

