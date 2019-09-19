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

from plumbum import cli, local
from conversion import read_bvals, read_imgs, read_imgs_masks
from nibabel import load
from util import abspath, pjoin, save_nifti, copyfile, RAISE, basename, dirname, isfile
import numpy as np
from multiprocessing import Pool
from findBshells import BSHELL_MIN_DIST


def joinBshells(imgPath, ref_bvals_file=None, ref_bvals=None, sep_prefix=None):

    if ref_bvals_file:
        print('Reading reference b-shell file ...')
        ref_bvals= read_bvals(ref_bvals_file)

    print('Joining b-shells for', imgPath)

    imgPath= local.path(imgPath)
    img= load(imgPath._path)
    dim= img.header['dim'][1:5]

    inPrefix= abspath(imgPath).split('.')[0]
    directory= dirname(inPrefix)
    prefix = basename(inPrefix)

    bvalFile= inPrefix+'.bval'
    bvecFile= inPrefix+'.bvec'

    if sep_prefix:
        harmPrefix= pjoin(directory, sep_prefix+ prefix)
    else:
        harmPrefix= inPrefix

    if not isfile(harmPrefix+'.bval'):
        copyfile(bvalFile, harmPrefix+'.bval')
    if not isfile(harmPrefix+'.bvec'):
        copyfile(bvecFile, harmPrefix+'.bvec')

    bvals= np.array(read_bvals(inPrefix+'.bval'))


    joinedDwi = np.zeros((dim[0], dim[1], dim[2], dim[3]), dtype='float32')

    for bval in ref_bvals:

        # ind= np.where(bval==bvals)[0]
        ind= np.where(abs(bval-bvals)<=BSHELL_MIN_DIST)[0]

        if bval==0.:
            b0Img = load(inPrefix+'_b0.nii.gz')
            b0 = b0Img.get_data()
            for i in ind:
                joinedDwi[:,:,:,i]= b0

        else:
            b0_bshell= load(harmPrefix+f'_b{int(bval)}.nii.gz').get_data()

            joinedDwi[:,:,:,ind] = b0_bshell[:,:,:,1:]

    if not isfile(harmPrefix + '.nii.gz'):
        save_nifti(harmPrefix + '.nii.gz', joinedDwi, b0Img.affine, b0Img.header)
    else:
        print(harmPrefix + '.nii.gz', 'already exists, not overwritten.')



def joinAllBshells(tar_csv, ref_bvals_file, separatedPrefix=None, ncpu=4):

    ref_bvals = read_bvals(ref_bvals_file)
    if tar_csv:

        try:
            imgs, _ = read_imgs_masks(tar_csv)
        except:
            imgs = read_imgs(tar_csv)

        pool = Pool(int(ncpu))
        for imgPath in imgs:
            pool.apply_async(joinBshells, kwds=({'imgPath': imgPath, 'ref_bvals': ref_bvals, 'sep_prefix': separatedPrefix}),
                             error_callback=RAISE)

        pool.close()
        pool.join()



class joinDividedShells(cli.Application):

    tar_csv = cli.SwitchAttr(
        ['--img_list'],
        cli.ExistingFile,
        help='csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\\ndwi2,mask2\\n...'
             'or just one column for dwi1\\ndwi2\\n...',
        mandatory= True)

    ref_bvals_file = cli.SwitchAttr(
        ['--ref_bshell_file'],
        cli.ExistingFile,
        help='reference bshell file',
        mandatory= True)
    
    separatedPrefix= cli.SwitchAttr(
        ['--sep_prefix'],
        help='prefix of the separated bshell files (.nii.gz, .bval, .bvec) if different from original files. '
             'Example: if separated bshell files are named as harmonized_originalName.nii.gz, then --sep_prefix=harmonized_',
        default=None)

    ncpu = cli.SwitchAttr(
        '--ncpu',
        help='number of processes/threads to use (-1 for all available, may slow down your system)',
        default=4)

    def main(self):
        joinAllBshells(self.tar_csv, self.ref_bvals_file, self.separatedPrefix, self.ncpu)



if __name__== '__main__':
    joinDividedShells.run()

