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

from normalize import find_b0
from plumbum import cli, local
from conversion import read_bvals, read_bvecs, write_bvals, write_bvecs, read_imgs, read_imgs_masks
from nibabel import load
from util import abspath, pjoin, save_nifti, RAISE
import numpy as np
from multiprocessing import Pool
from findBshells import BSHELL_MIN_DIST

def separateBshells(imgPath, ref_bvals_file=None, ref_bvals=None):

    if ref_bvals_file:
        print('Reading reference b-shell file ...')
        ref_bvals= read_bvals(ref_bvals_file)


    print('Separating b-shells for', imgPath)
        
    imgPath= local.path(imgPath)

    img= load(imgPath._path)
    dwi= img.get_data()
    inPrefix= abspath(imgPath).split('.')[0]
    bvals= np.array(read_bvals(inPrefix+'.bval'))
    bvecs= np.array(read_bvecs(inPrefix+'.bvec'))


    for bval in ref_bvals:

        # ind= np.where(bval==bvals)[0]
        ind= np.where(abs(bval-bvals)<=BSHELL_MIN_DIST)[0]
        N_b= len(ind)

        bPrefix = inPrefix + f'_b{int(bval)}'

        if bval==0.:
            b0 = find_b0(dwi, ind)
            save_nifti(bPrefix + '.nii.gz', b0, img.affine, img.header)

        else:
            b0_bshell = np.zeros((dwi.shape[0],dwi.shape[1],dwi.shape[2],N_b+1), dtype='float32')
            b0_bshell[:,:,:,0]= b0
            b0_bshell[:,:,:,1:]= dwi[:,:,:,ind]

            b0_bvals= [0.]+[bval]*N_b

            b0_bvecs= np.zeros((N_b+1,3), dtype='float32')
            b0_bvecs[1:,]= bvecs[ind,: ]

            # save_nifti(bPrefix+'.nii.gz', b0_bshell, img.affine, img.header)
            write_bvals(bPrefix+'.bval', b0_bvals)
            write_bvecs(bPrefix+'.bvec', b0_bvecs)



def separateAllBshells(ref_csv, ref_bvals_file, ncpu=4, outPrefix= None):

    outPrefix = abspath(outPrefix)
    ref_bvals = read_bvals(ref_bvals_file)

    try:
        imgs, masks = read_imgs_masks(ref_csv)
    except:
        imgs = read_imgs(ref_csv)
        masks = None

    pool = Pool(int(ncpu))
    for imgPath in imgs:
        pool.apply_async(separateBshells,
                         kwds={'imgPath': imgPath, 'ref_bvals': ref_bvals}, error_callback=RAISE)

    pool.close()
    pool.join()

    for bval in ref_bvals:

        if outPrefix:
            f = open(f'{outPrefix}_b{int(bval)}.csv', 'w')

        if masks:
            for imgPath, maskPath in zip(imgs, masks):
                inPrefix = abspath(imgPath).split('.')[0]
                bPrefix = inPrefix + f'_b{int(bval)}'
                f.write(f'{bPrefix}.nii.gz,{maskPath}\n')

        else:
            for imgPath in imgs:
                inPrefix = abspath(imgPath).split('.')[0]
                bPrefix = inPrefix + f'_b{int(bval)}'
                f.write(f'{bPrefix}.nii.gz\n')

        f.close()


class separateShells(cli.Application):

    ref_csv = cli.SwitchAttr(
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

    outPrefix= cli.SwitchAttr(
        ['-outPrefix'],
        help='outPrefix for list of generated single shell images(,masks)')

    ncpu = cli.SwitchAttr(
        '--ncpu',
        help='number of processes/threads to use (-1 for all available, may slow down your system)',
        default=4)


    def main(self):

        separateAllBshells(self.ref_csv, self.ref_bvals_file, self.ncpu, self.outPrefix)


if __name__== '__main__':
    separateShells.run()
