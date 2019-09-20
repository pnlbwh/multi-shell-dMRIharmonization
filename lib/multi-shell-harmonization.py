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
N_CPU= str(psutil.cpu_count())
from conversion import read_bvals
from util import dirname, basename, pjoin, SCRIPTDIR, remove, isfile
from subprocess import check_call

from consistencyCheck import consistencyCheck

from separateBshells import separateAllBshells

from joinBshells import joinAllBshells

from fileUtil import check_dir


def separateShellsWrapper(csvFile, ref_bshell_file, N_proc):

    csvDirectory= dirname(csvFile)
    csvPrefix= basename(csvFile).split('.')[0]
    outPrefix= pjoin(csvDirectory, csvPrefix)

    separateAllBshells(csvFile, ref_bshell_file, N_proc, outPrefix)

    return outPrefix


class multi_shell_pipeline(cli.Application):

    VERSION = 1.0

    ref_csv = cli.SwitchAttr(
        ['--ref_list'],
        cli.ExistingFile,
        help='reference csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\\ndwi2,mask2\\n...',
        mandatory=False)

    target_csv = cli.SwitchAttr(
        ['--tar_list'],
        cli.ExistingFile,
        help='target csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\\ndwi2,mask2\\n...',
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
        default= '4')

    N_zero = cli.SwitchAttr(
        '--nzero',
        help= 'number of zero padding for denoising skull region during signal reconstruction',
        default= '10')

    force = cli.Flag(
        ['--force'],
        help='turn on this flag to overwrite existing data',
        default= False)

    travelHeads = cli.Flag(
        ['--travelHeads'],
        help='travelling heads',
        default= False)

    denoise= None
    bvalMap= None
    resample= None

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

        if self.N_proc=='-1':
            self.N_proc= N_CPU

        # check directory existence
        check_dir(self.templatePath, self.force)

        ## check consistency of b-shells and spatial resolution
        ref_bvals_file= pjoin(self.templatePath, 'ref_bshell_bvalues.txt')
        ref_res_file= pjoin(self.templatePath, 'ref_res_file.npy')
        if self.ref_csv:
            if isfile(ref_bvals_file) and isfile(ref_res_file):
                remove(ref_bvals_file)
                remove(ref_res_file)

            consistencyCheck(self.ref_csv, ref_bvals_file, ref_res_file)

        if self.target_csv:
            consistencyCheck(self.target_csv, ref_bvals_file, ref_res_file)


        ## separate b-shells
        if self.ref_csv:
            refListOutPrefix= separateShellsWrapper(self.ref_csv, ref_bvals_file, self.N_proc)
        if self.target_csv:
            tarListOutPrefix= separateShellsWrapper(self.target_csv, ref_bvals_file, self.N_proc)


        ## define variables for template creation and data harmonization

        # variables common to all ref_bvals
        pipeline_vars=[
            '--ref_name', self.reference,
            '--tar_name', self.target,
            '--nshm', self.N_shm,
            '--nproc', self.N_proc,
            '--template', self.templatePath,
            ]

        if self.N_zero:
            pipeline_vars.append(f'--nzero {self.N_zero}')
        if self.bvalMap:
            pipeline_vars.append(f'--bvalMap {self.bvalMap}')
        if self.resample:
            pipeline_vars.append(f'--resample {self.resample}')
        if self.denoise:
            pipeline_vars.append('--denoise')
        if self.travelHeads:
            pipeline_vars.append('--travelHeads')
        if self.force:
            pipeline_vars.append('--force')
        if self.debug:
            pipeline_vars.append('--debug')
        if self.verbose:
            pipeline_vars.append('--verbose')


        # the b-shell bvalues are sorted in descending order because we want to perform registration with highest bval
        ref_bvals= read_bvals(ref_bvals_file)[::-1]
        for bval in ref_bvals[ :-1]: # pass the last bval which is 0.

            if self.create and not self.process:
                print('## template creation ##')

                check_call((' ').join([pjoin(SCRIPTDIR, 'harmonization.py'),
                '--tar_list', tarListOutPrefix+f'_b{int(bval)}.csv',
                '--bshell_b', str(int(bval)),
                '--ref_list', refListOutPrefix+f'_b{int(bval)}.csv',
                '--create'] + pipeline_vars), shell= True)



            elif not self.create and self.process:
                print('## data harmonization ##')

                check_call((' ').join([pjoin(SCRIPTDIR, 'harmonization.py'),
                '--tar_list', tarListOutPrefix + f'_b{int(bval)}.csv',
                '--bshell_b', str(int(bval)),
                '--process'] + pipeline_vars), shell=True)



            elif self.create and self.process:
                check_call((' ').join([pjoin(SCRIPTDIR, 'harmonization.py'),
                '--tar_list', tarListOutPrefix + f'_b{int(bval)}.csv',
                '--bshell_b', str(int(bval)),
                '--ref_list', refListOutPrefix+f'_b{int(bval)}.csv',
                '--create', '--process'] + pipeline_vars), shell=True)


        ## join harmonized data
        joinAllBshells(self.target_csv, ref_bvals_file, 'harmonized_', self.N_proc)


if __name__== '__main__':
    multi_shell_pipeline.run()

