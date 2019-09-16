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

from plumbum import cli
import psutil
N_CPU= psutil.cpu_count()
from conversion import read_imgs_masks, read_bvals
from util import dirname, basename, pjoin

from .consistencyCheck import consistencyCheck

from .separateBshells import separateShells

from .harmonization import pipeline

from .joinBshells import joinDividedShells


def separateShellsWrapper(csvFile, N_proc):

    separateShells.ref_csv = csvFile
    separateShells.ncpu = N_proc
    ref_bshell_img= read_imgs_masks(csvFile)[0][0]
    directory= dirname(ref_bshell_img)
    prefix= basename(ref_bshell_img).split('.')[0]
    separateShells.ref_bvals_file =  pjoin(directory, prefix+'.bval')

    csvDirectory= dirname(csvFile)
    csvPrefix= basename(csvFile)
    separateShells.outPrefix= pjoin(csvDirectory, csvPrefix)
    separateShells.run()

    return (separateShells.ref_bvals_file, separateShells.outPrefix)


class multi_shell_pipeline(cli.Application):

    ref_csv = cli.SwitchAttr(
        ['--ref_list'],
        cli.ExistingFile,
        help='reference csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\ndwi2,mask2\n...',
        mandatory=False)

    target_csv = cli.SwitchAttr(
        ['--tar_list'],
        cli.ExistingFile,
        help='target csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\ndwi2,mask2\n...',
        mandatory=False)


    templatePath = cli.SwitchAttr(
        ['--template'],
        help='template directory',
        mandatory=True)

    N_shm = cli.SwitchAttr(
        ['--nshm'],
        help='spherical harmonic order, by default maximum possible is used',
        default= '-1')

    N_proc = cli.SwitchAttr(
        '--nproc',
        help= 'number of processes/threads to use (-1 for all available, may slow down your system)',
        default= 4)

    N_zero = cli.SwitchAttr(
        '--nzero',
        help= 'number of zero padding for denoising skull region during signal reconstruction',
        default= 10)

    force = cli.Flag(
        ['--force'],
        help='turn on this flag to overwrite existing data',
        default= False)

    travelHeads = cli.Flag(
        ['--travelHeads'],
        help='travelling heads',
        default= False)

    resample = cli.SwitchAttr(
        '--resample',
        help='voxel size MxNxO to resample into',
        default= False)

    bvalMap = cli.SwitchAttr(
        '--bvalMap',
        help='specify a bmax to scale bvalues into',
        default= False)

    bshell_b = cli.SwitchAttr(
        '--bshell_b',
        help='bvalue of the bshell',
        mandatory= True)

    denoise = cli.Flag(
        '--denoise',
        help='turn on this flag to denoise voxel data',
        default= False)

    create = cli.Flag(
        '--create',
        help= 'turn on this flag to create template',
        default= False)

    process = cli.Flag(
        '--process',
        help= 'turn on this flag to harmonize',
        default= False)

    debug = cli.Flag(
        '--debug',
        help= 'turn on this flag to debug harmonized data (valid only with --process)',
        default= False)

    reference = cli.SwitchAttr(
        '--ref_name',
        help= 'reference site name',
        mandatory= True)

    target = cli.SwitchAttr(
        '--tar_name',
        help= 'target site name',
        mandatory= True)

    verbose= cli.Flag(
        '--verbose',
        help='print everything to STDOUT',
        default= False)


    def main(self):

        self.N_shm= int(self.N_shm)
        self.N_proc= int(self.N_proc)
        if self.N_proc==-1:
            self.N_proc= N_CPU


        ## check consistency of b-shells and spatial resolution
        if self.ref_csv:
            consistencyCheck.ref_csv = self.ref_csv
            consistencyCheck.run()
        if self.target_csv:
            consistencyCheck.ref_csv = self.target_csv
            consistencyCheck.run()


        ## separate b-shells
        if self.ref_csv:
            ref_bvals_file, refListOutPrefix= separateShellsWrapper(self.ref_csv, self.N_proc)
        if self.target_csv:
            ref_bvals_file, tarListOutPrefix= separateShellsWrapper(self.target_csv, self.N_proc)


        ## define variables for template creation and data harmonization

        # variables common to all ref_bvals
        pipeline.templatePath = self.templatePath
        pipeline.N_proc = self.N_proc
        pipeline.N_zero = self.N_zero

        pipeline.reference = self.reference
        pipeline.target = self.target

        pipeline.travelHeads = self.travelHeads
        pipeline.debug = self.debug

        pipeline.bvalMap = self.bvalMap
        pipeline.resample = self.resample
        pipeline.denoise = self.denoise

        pipeline.force = self.force

        # variables specific to bval
        ref_bvals = read_bvals(ref_bvals_file)
        for bval in ref_bvals:

            pipeline.bshell_b= self.bshell_b

            ## template creation
            if self.create:
                pipeline.create = True
                pipeline.ref_csv= refListOutPrefix+f'_b{bval}.csv'
                pipeline.target_csv= tarListOutPrefix+f'_b{bval}.csv'

                pipeline.run()

            ## data harmonization
            if self.process:
                pipeline.process = True
                pipeline.target_csv= tarListOutPrefix+f'_b{bval}.csv'

                pipeline.run()



        ## join harmonized data
        joinDividedShells.ref_bvals_file = ref_bvals_file
        joinDividedShells.ncpu = self.N_proc
        joinDividedShells.tar_csv = tarListOutPrefix+'.csv' # original target file
        joinDividedShells.separatedPrefix = 'harmonized_'
        joinDividedShells.run()


if __name__== '__main__':
    multi_shell_pipeline.run()