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
from plumbum import cli, local
from warnings import warn
from util import abspath, load
from os import getpid
from findBshells import findBShells

def check_bshells(csvFile, ref_bvals):
    
    print('\nSite',csvFile,'\n')

    ref_imgs= read_imgs(csvFile)
    unmatched=[]
    for imgPath in ref_imgs:

        imgPath= local.path(imgPath)

        if not imgPath.exists:
            FileNotFoundError(imgPath)

        inPrefix= abspath(imgPath).split('.')[0]
        bvals= np.unique(read_bvals(inPrefix+'.bval'))

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


def check_resolution(csvFile, ref_res):
    print('\nSite', csvFile, '\n')

    ref_imgs = read_imgs(csvFile)
    unmatched = []
    for imgPath in ref_imgs:

        imgPath = local.path(imgPath)

        if not imgPath.exists:
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

class consistencyCheck(cli.Application):

    ref_csv = cli.SwitchAttr(
        ['--ref_list'],
        cli.ExistingFile,
        help='csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\ndwi2,mask2\n...'
             'or just one column for dwi1\n/dwi2\n...')


    def main(self):

        try:
            ref_imgs,_=read_imgs_masks(self.ref_csv)
        except:
            ref_imgs= read_imgs(self.ref_csv)


        ref_bshell_img= ref_imgs[0]
        print(f'Using {ref_bshell_img} to determine b-shells ...')

        inPrefix= abspath(ref_bshell_img).split('.')[0]
        ref_bvals= findBShells(inPrefix+'.bval', f'/tmp/b_shells_{getpid()}.txt')
        print('b-shells are', ref_bvals)

        print('Checking consistency of b-shells among reference and target cases')
        if self.ref_csv:
            check_bshells(self.ref_csv, ref_bvals)


        ref_res= load(ref_bshell_img).header['pixdim'][1:4]
        print('spatial resolution is', ref_res)
        print('Checking consistency of spatial resolution among reference and target cases')
        if self.ref_csv:
            check_resolution(self.ref_csv, ref_res)


if __name__ == '__main__':
    consistencyCheck.run()
