#!/usr/bin/env python

from plumbum import cli, local
from conversion import read_bvals, read_bvecs, write_bvals, write_bvecs, read_imgs
from nibabel import load
from util import abspath, pjoin, save_nifti, copyfile, RAISE, basename, dirname, isfile
import numpy as np
from multiprocessing import Pool


def joinShells(imgPath, ref_bvals, sep_prefix):

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

        ind= np.where(bval==bvals)[0]

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

class joinDividedShells(cli.Application):


    tar_csv = cli.SwitchAttr(
        ['--tar_list'],
        cli.ExistingFile,
        help='target csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\ndwi2,mask2\n...')

    ref_bvals_file = cli.SwitchAttr(
        ['--ref_bshell_file'],
        cli.ExistingFile,
        help='reference bshell file')
    
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

        ref_bvals= read_bvals(self.ref_bvals_file)
        if self.tar_csv:
            imgs = read_imgs(self.tar_csv)

            pool = Pool(int(self.ncpu))
            for imgPath in imgs:
                pool.apply_async(joinShells, (imgPath, ref_bvals, self.separatedPrefix), error_callback=RAISE)

            pool.close()
            pool.join()

            # loop for debugging
            # for imgPath in imgs:
            #     joinShells(imgPath, ref_bvals, self.separatedPrefix)


if __name__== '__main__':
    joinDividedShells.run()





