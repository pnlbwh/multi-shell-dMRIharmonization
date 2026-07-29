#!/usr/bin/env python

# ===============================================================================
# Script for cleaning up prior run's outputs
# ===============================================================================

from conversion import read_imgs, read_imgs_masks
from glob import glob
from plumbum import local
from util import abspath, isfile, dirname
import sys
from os import remove
from shutil import rmtree


def delete(pattern):
    files= glob(pattern)

    print('Deleting', len(files), 'files:', pattern)
    for f in files:
        remove(f)

    dir= dirname(pattern)
    try:
        rmtree(dir+ '/dti')
        rmtree(dir+ '/harm')
    except FileNotFoundError:
        pass
    

def cleanup(ref_imgs):

    for imgPath in ref_imgs:

        imgPath= local.path(imgPath)
        inPrefix= abspath(imgPath).split('.nii')[0]
        
        delete(inPrefix+'*bmapped*')
        # next step may be redundant
        delete(inPrefix+'*resampled*')
        

def _cleanup(ref_csv):

    try:
        ref_imgs, _ = read_imgs_masks(ref_csv)
    except:
        ref_imgs = read_imgs(ref_csv)

    cleanup(ref_imgs)


if __name__ == '__main__':
    if len(sys.argv)==1 or sys.argv[1]=='-h' or sys.argv[1]=='--help':
        print('''Check consistency of b-shells and spatial resolution among subjects
Usage:
{__file__} list.csv/txt

Provide a csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\\ndwi2,mask2\\n...
or just one column for dwi1\\ndwi2\\n...''')
        exit()

    ref_csv= abspath(sys.argv[1])
    if isfile(ref_csv):
        _cleanup(ref_csv)
    else:
        raise FileNotFoundError(f'{ref_csv} does not exists.')

