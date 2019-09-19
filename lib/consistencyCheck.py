#!/usr/bin/env python

# ===============================================================================
# dMRIharmonization (2018) pipeline is written by-
#
# TASHRIF BILLAH
# Brigham and Women's Hospital/Harvard Medical School
# tbillah@bwh.harvard.edu, tashrifbillah@gmail.com
#
# ===============================================================================
# See details at https://github.com/pnlbwh/dMRIharmonization
# Submit issues at https://github.com/pnlbwh/dMRIharmonization/issues
# View LICENSE at https://github.com/pnlbwh/dMRIharmonization/blob/master/LICENSE
# ===============================================================================

from conversion import read_bvals, read_imgs, read_imgs_masks
import numpy as np
from warnings import warn
from plumbum import local
from util import abspath, load, isfile, getpid
from findBshells import findBShells
import sys


def check_bshells(ref_imgs, ref_bvals):

    unmatched=[]
    for imgPath in ref_imgs:

        imgPath= local.path(imgPath)
        if not imgPath.exists():
            FileNotFoundError(imgPath)

        inPrefix= abspath(imgPath).split('.')[0]
        bvals= findBShells(inPrefix+'.bval')

        if (bvals==ref_bvals).all():
            print('b-shells matched for', imgPath.name)

        else:
            np.testing.assert_array_equal(bvals, ref_bvals, err_msg=f'Unmatched b-shells for {imgPath.name}')
            unmatched.append(imgPath._path)

    print('')
    if len(unmatched):
        warn('Leave out the unmatched cases or change the reference case for determining b-shell to run multi-shell-dMRIharmonization')
        print('Unmatched cases:')
        print(unmatched)
    else:
        print('All cases have same b-shells. Data is good for running multi-shell-dMRIharmonization')
    print('')



def check_resolution(ref_imgs, ref_res):

    unmatched = []
    for imgPath in ref_imgs:

        imgPath= local.path(imgPath)
        if not imgPath.exists():
            FileNotFoundError(imgPath)

        res= load(imgPath._path).header['pixdim'][1:4]

        if (res == ref_res).all():
            print('spatial resolution matched for', imgPath.name)

        else:
            np.testing.assert_array_equal(res, ref_res, err_msg=f'Unmatched spatial resolution for {imgPath.name}')
            unmatched.append(imgPath._path)

    print('')
    if len(unmatched):
        warn('Leave out the unmatched cases or change the reference case for determining spatial resolution to run multi-shell-dMRIharmonization')
        print('Unmatched cases:')
        print(unmatched)
    else:
        print('All cases have same spatial resolution. Data is good for running multi-shell-dMRIharmonization')
    print('')


def consistencyCheck(ref_csv, outputBshellFile= None, outPutResolutionFile= None):

    try:
        ref_imgs, _ = read_imgs_masks(ref_csv)
    except:
        ref_imgs = read_imgs(ref_csv)


    if isfile(outputBshellFile) and isfile(outPutResolutionFile):
        ref_bvals= read_bvals(outputBshellFile)
        ref_res = np.load(outPutResolutionFile)
    else:
        ref_bshell_img = ref_imgs[0]
        print(f'Using {ref_bshell_img} to determine b-shells')

        inPrefix = abspath(ref_bshell_img).split('.')[0]
        ref_bvals = findBShells(inPrefix + '.bval', outputBshellFile)

        ref_res = load(ref_bshell_img).header['pixdim'][1:4]
        np.save(outPutResolutionFile, ref_res)


    print('b-shells are', ref_bvals)

    print('\nSite', ref_csv, '\n')

    print('Checking consistency of b-shells among subjects')
    check_bshells(ref_imgs, ref_bvals)


    print('spatial resolution is', ref_res)
    print('Checking consistency of spatial resolution among subjects')
    check_resolution(ref_imgs, ref_res)



if __name__ == '__main__':
    if len(sys.argv)==1 or sys.argv[1]=='-h' or sys.argv[1]=='--help':
        print('''Check consistency of b-shells and spatial resolution among subjects
Usage:
consistencyCheck list.csv/txt

Provide a csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\\ndwi2,mask2\\n...
or just one column for dwi1\\ndwi2\\n...''')
        exit()

    ref_csv= abspath(sys.argv[1])
    if ref_csv:
        consistencyCheck(ref_csv)
    else:
        raise FileNotFoundError(f'{ref_csv} does not exists.')

