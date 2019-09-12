#!/usr/bin/env python

from dMRIharmonization.lib.normalize import find_b0
from plumbum import cli, local
from conversion import read_bvals, read_bvecs, write_bvals, write_bvecs, read_imgs
from nibabel import load
from util import abspath, pjoin, save_nifti, RAISE
import numpy as np
from multiprocessing import Pool

def divideShells(imgPath, ref_bvals):

    print('Separating b-shells for', imgPath)
        
    imgPath= local.path(imgPath)

    img= load(imgPath._path)
    dwi= img.get_data()
    inPrefix= abspath(imgPath).split('.')[0]
    bvals= np.array(read_bvals(inPrefix+'.bval'))
    bvecs= np.array(read_bvecs(inPrefix+'.bvec'))


    for bval in ref_bvals:

        ind= np.where(bval==bvals)[0]
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

            save_nifti(bPrefix+'.nii.gz', b0_bshell, img.affine, img.header)
            write_bvals(bPrefix+'.bval', b0_bvals)
            write_bvecs(bPrefix+'.bvec', b0_bvecs)



class separateShells(cli.Application):

    ref_csv = cli.SwitchAttr(
        ['--ref_list'],
        cli.ExistingFile,
        help='reference csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\ndwi2,mask2\n...')

    tar_csv = cli.SwitchAttr(
        ['--tar_list'],
        cli.ExistingFile,
        help='target csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\ndwi2,mask2\n...')

    ref_bvals_file = cli.SwitchAttr(
        ['--ref_bshell_file'],
        cli.ExistingFile,
        help='reference bshell file')

    ncpu = cli.SwitchAttr(
        '--ncpu',
        help='number of processes/threads to use (-1 for all available, may slow down your system)',
        default=4)

    def main(self):

        ref_bvals= read_bvals(self.ref_bvals_file)
        if self.ref_csv:
            imgs= read_imgs(self.ref_csv)

            pool= Pool(int(self.ncpu))
            for imgPath in imgs:
                pool.apply_async(divideShells, (imgPath, ref_bvals), error_callback=RAISE)

            pool.close()
            pool.join()

            # loop for debugging
            # for imgPath in imgs:
            #     divideShells(imgPath, ref_bvals)

if __name__== '__main__':
    separateShells.run()





