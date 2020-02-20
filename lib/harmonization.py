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
from distutils.spawn import find_executable
import multiprocessing, psutil

from determineNshm import verifyNshmForAll, determineNshm
from util import *
from fileUtil import read_caselist, check_dir, check_csv

N_CPU= psutil.cpu_count()
SCRIPTDIR= dirname(__file__)


class pipeline(cli.Application):

    """
    ===============================================================================
    dMRIharmonization (2018) pipeline is written by-

    TASHRIF BILLAH
    Brigham and Women's Hospital/Harvard Medical School
    tbillah@bwh.harvard.edu, tashrifbillah@gmail.com

    ===============================================================================
    See details at https://github.com/pnlbwh/dMRIharmonization
    Submit issues at https://github.com/pnlbwh/dMRIharmonization/issues
    View LICENSE at https://github.com/pnlbwh/dMRIharmonization/blob/master/LICENSE
    ===============================================================================

    Template creation, harmonization, and debugging
    """

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

    harm_csv = cli.SwitchAttr(
        ['--harm_list'],
        cli.ExistingFile,
        help='harmonized csv/txt file with first column for dwi and 2nd column for mask: dwi1,mask1\ndwi2,mask2\n...',
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

    denoise = cli.Flag(
        '--denoise',
        help='turn on this flag to denoise voxel data',
        default= False)

    bshell_b = cli.SwitchAttr(
        '--bshell_b',
        help='bvalue of the bshell',
        mandatory= True)

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


    diffusionMeasures = ['MD', 'FA', 'GFA']


    def createTemplate(self):

        from buildTemplate import difference_calc, antsMult, warp_bands, \
            dti_stat, rish_stat, template_masking, createAntsCaselist
        from preprocess import common_processing

        # check directory existence
        check_dir(self.templatePath, self.force)

        # go through each file listed in csv, check their existence, create dti and harm directories
        check_csv(self.ref_csv, self.force)
        check_csv(self.target_csv, self.force)

        # createTemplate steps -----------------------------------------------------------------------------------------

        # read image lists
        refImgs, refMasks= common_processing(self.ref_csv)
        if not self.ref_csv.endswith('.modified'):
            self.ref_csv += '.modified'
        # debug: use the following line to omit processing again
        # refImgs, refMasks = read_caselist(self.ref_csv)

        targetImgs, targetMasks= common_processing(self.target_csv)
        if not self.target_csv.endswith('.modified'):
            self.target_csv += '.modified'
        # debug: use the following line to omit processing again
        # targetImgs, targetMasks = read_caselist(self.target_csv)

        imgs= refImgs+targetImgs
        masks= refMasks+targetMasks

        # create caselist for antsMult
        antsMultCaselist= pjoin(self.templatePath, 'antsMultCaselist.txt')
        createAntsCaselist(imgs, antsMultCaselist)

        # run ANTS multivariate template construction

        # ATTN: antsMultivariateTemplateConstruction2.sh requires '/' at the end of templatePath
        if not self.templatePath.endswith('/'):
            self.templatePath += '/'

        # check if bmax template was created earlier
        bmaxTemplateFile= pjoin(self.templatePath, 'bmaxTemplateCompletion')
        template0= pjoin(self.templatePath, 'template0.nii.gz')
        if not isfile(bmaxTemplateFile):
            # ATTN: antsMultivariateTemplateConstruction2.sh requires absolute path for caselist
            antsMult(abspath(antsMultCaselist), self.templatePath)
        else:
            warnings.warn(f'Using {template0} which was created before with bmax shell')

        # load templateHdr
        templateHdr= load(template0).header


        # warp mask, dti, and rish bands
        pool = multiprocessing.Pool(self.N_proc)
        for imgPath, maskPath in zip(imgs, masks):
            pool.apply_async(func= warp_bands, args= (imgPath, maskPath, self.templatePath, ))
        
        pool.close()
        pool.join()

        
        # loop for debugging
        # for imgPath, maskPath in zip(imgs, masks):
        #     warp_bands(imgPath, maskPath, self.templatePath)

        print('calculating dti statistics i.e. mean, std calculation for reference site')
        refMaskPath= dti_stat(self.reference, refImgs, refMasks, self.templatePath, templateHdr)
        print('calculating dti statistics i.e. mean, std calculation for target site')
        targetMaskPath= dti_stat(self.target, targetImgs, targetMasks, self.templatePath, templateHdr)

        print('masking dti statistics of reference site')
        _= template_masking(refMaskPath, targetMaskPath, self.templatePath, self.reference)
        print('masking dti statistics of target site')
        templateMask= template_masking(refMaskPath, targetMaskPath, self.templatePath, self.target)

        print('calculating rish_statistics i.e. mean, std calculation of reference site')
        rish_stat(self.reference, refImgs, self.templatePath, templateHdr)
        print('calculating rish_statistics i.e. mean, std calculation of target site')
        rish_stat(self.target, targetImgs, self.templatePath, templateHdr)

        print('calculating templates map for diffusionMeasures')
        difference_calc(self.reference, self.target, refImgs, targetImgs, self.templatePath, templateHdr,
                        templateMask, self.diffusionMeasures)

        print('calculating templates for rishFeatures')
        difference_calc(self.reference, self.target, refImgs, targetImgs, self.templatePath, templateHdr,
                        templateMask, [f'L{i}' for i in range(0, self.N_shm+1, 2)])


        print('\n\nTemplate creation completed \n\n')


        # write a flag in templatePath that can be used to see if bmax template was created earlier
        if not isfile(bmaxTemplateFile):
            with open(pjoin(bmaxTemplateFile), 'w'):
                pass

    def harmonizeData(self):

        from reconstSignal import reconst
        from preprocess import dti_harm

        # check the templatePath
        if not exists(self.templatePath):
            raise NotADirectoryError(f'{self.templatePath} does not exist')
        else:
            if not os.listdir(self.templatePath):
                raise ValueError(f'{self.templatePath} is empty')

        # go through each file listed in csv, check their existence, create dti and harm directories
        check_csv(self.target_csv, self.force)


        # target data is not manipulated in multi-shell-dMRIharmonization i.e. bvalMapped, resampled, nor denoised
        # this block may be uncommented in a future design
        # from preprocess import dti_harm
        # if self.debug:
        #     # calcuate diffusion measures of target site before any processing so we are able to compare
        #     # with the ones after harmonization
        #     imgs, masks= read_caselist(self.tar_unproc_csv)
        #     pool = multiprocessing.Pool(self.N_proc)
        #     for imgPath, maskPath in zip(imgs, masks):
        #         imgPath= convertedPath(imgPath)
        #         maskPath= convertedPath(maskPath)
        #         pool.apply_async(func= dti_harm, args= ((imgPath, maskPath, )))
        #
        #     pool.close()
        #     pool.join()

        # reconstSignal steps ------------------------------------------------------------------------------------------

        # read target image list
        moving= pjoin(self.templatePath, f'Mean_{self.target}_FA_b{self.bshell_b}.nii.gz')
        imgs, masks= read_caselist(self.target_csv)

        preFlag= 1 # omit preprocessing of target data again
        if self.target_csv.endswith('.modified'):
            preFlag= 0
        else:
            # this file will be used later for debugging
            self.target_csv += '.modified'
            fm = open(self.target_csv, 'w')


        self.harm_csv= self.target_csv+'.harmonized'
        fh= open(self.harm_csv, 'w')
        pool = multiprocessing.Pool(self.N_proc)
        res= []
        for imgPath, maskPath in zip(imgs, masks):
            res.append(pool.apply_async(func= reconst, args= (imgPath, maskPath, moving, self.templatePath, preFlag, )))

        for r in res:
            imgPath, maskPath, harmImg, harmMask= r.get()

            if preFlag:
                fm.write(imgPath + ',' + maskPath + '\n')
            fh.write(harmImg + ',' + harmMask + '\n')


        pool.close()
        pool.join()

       
        # loop for debugging
        # res= []
        # for imgPath, maskPath in zip(imgs, masks):
        #     res.append(reconst(imgPath, maskPath, moving, self.templatePath, preFlag))
        #
        # for r in res:
        #     imgPath, maskPath, harmImg, harmMask= r
        #
        #     if preFlag:
        #         fm.write(imgPath + ',' + maskPath + '\n')
        #     fh.write(harmImg + ',' + harmMask + '\n')


        if preFlag:
            fm.close()
        fh.close()

        
        if self.debug:
            harmImgs, harmMasks= read_caselist(self.harm_csv)
            pool = multiprocessing.Pool(self.N_proc)
            for imgPath,maskPath in zip(harmImgs,harmMasks):
                pool.apply_async(func= dti_harm, args= (imgPath,maskPath))
            pool.close()
            pool.join()


        print('\n\nHarmonization completed\n\n')


    def post_debug(self):

        from debug_fa import sub2tmp2mni

        print('\n\n Reference site')
        sub2tmp2mni(self.templatePath, self.reference, self.ref_csv, ref= True)

        print('\n\n Target site before harmonization')
        sub2tmp2mni(self.templatePath, self.target, self.tar_unproc_csv, tar_unproc= True)

        print('\n\n Target site after harmonization')
        sub2tmp2mni(self.templatePath, self.target, self.harm_csv, tar_harm= True)


        self.showStat()

    
    def showStat(self):

        from debug_fa import analyzeStat
        from datetime import datetime
        from harm_plot import generate_csv, harm_plot
        import pandas as pd

        print('\n\nComputing statistics\n\n')
        
        print(f'{self.reference} site: ')
        ref_mean = analyzeStat(self.ref_csv, self.templatePath)
        generate_csv(self.ref_csv, ref_mean, pjoin(self.templatePath, self.reference), self.bshell_b)

        print(f'{self.target} site before harmonization: ')
        target_mean_before = analyzeStat(self.tar_unproc_csv, self.templatePath)
        generate_csv(self.tar_unproc_csv, target_mean_before, pjoin(self.templatePath, self.target)+'_before', self.bshell_b)

        print(f'{self.target} site after harmonization: ')
        target_mean_after = analyzeStat(self.harm_csv, self.templatePath)
        generate_csv(self.harm_csv, target_mean_after, pjoin(self.templatePath, self.target)+'_after', self.bshell_b)
        
        
        print('\n\nPrinting statistics\n\n')
        # save statistics for future
        statFile= pjoin(self.templatePath, 'meanFAstat.csv')
        if isfile(statFile):
            df= pd.read_csv(statFile)
        else:
            timestamp= datetime.now().strftime('%m/%d/%y %H:%M')
            sites= [f'{self.reference}',f'{self.target}_before',f'{self.target}_after']
            df= pd.DataFrame({timestamp:sites})
        
        header= f'mean meanFA b{self.bshell_b}'
        value= [np.mean(x) for x in [ref_mean, target_mean_before, target_mean_after]]
        df= df.assign(**{header:value})
        
        # print an empty line so future results, if appended, are visually separate
        # df=df.append(pd.Series(),ignore_index=True)
        
        df.to_csv(statFile, index=False)
        
        # print statistics on console        
        with open(statFile) as f:
            print(f.read())            
        
        # generate graph
        ebar= harm_plot([ref_mean, target_mean_before, target_mean_after],
                         labels=[self.reference, self.target+'_before', self.target+'_after'],
                         outPrefix=pjoin(self.templatePath,'meanFAstat'), bshell_b=self.bshell_b)

        print(f'\nDetailed statistics, summary results, and demonstrative plots are saved in:\n\n{self.templatePath}/*_stat.csv'
              f'\n{statFile}\n{ebar}\n')
              
   


    def sanityCheck(self):

        if not (self.create or self.process or self.debug):
            raise AttributeError('No option selected, ' 
                                'specify one (or many of) creation, harmonization, and debug flags')

        # check ants commands
        external_commands= [
            'antsMultivariateTemplateConstruction2.sh',
            'antsApplyTransforms',
            'antsRegistrationSyNQuick.sh',
            'unring.a64']

        for cmd in external_commands:
            exe= find_executable(cmd)
            if not exe:
                raise EnvironmentError(f'{cmd} not found')




    def main(self):

        self.templatePath= abspath(self.templatePath)
        self.N_shm= int(self.N_shm)
        self.N_proc= int(self.N_proc)
        if self.N_proc==-1:
            self.N_proc= N_CPU

        if self.target_csv.endswith('.modified'):
            self.tar_unproc_csv= str(self.target_csv).split('.modified')[0]
        else:
            self.tar_unproc_csv= str(self.target_csv)


        # check appropriateness of N_shm
        if self.N_shm!=-1 and (self.N_shm<2 or self.N_shm>8):
            raise ValueError('2<= --nshm <=8')



        # determine N_shm in default mode during template creation
        if self.N_shm==-1 and self.create:
            if self.ref_csv:
                ref_nshm_img = read_caselist(self.ref_csv)[0][0]
            elif self.target_csv:
                ref_nshm_img = read_caselist(self.target_csv)[0][0]

            directory= dirname(ref_nshm_img)
            prefix= basename(ref_nshm_img).split('.nii')[0]
            bvalFile= pjoin(directory, prefix+'.bval')
            self.N_shm, _= determineNshm(bvalFile)


        # automatic determination of N_shm during data harmonization is limited by N_shm used during template creation
        # Scale_L{i}.nii.gz of <= {N_shm during template creation} are present only
        elif self.N_shm==-1 and self.process:
            for i in range(0,8,2):
                if isfile(pjoin(self.templatePath, f'Scale_L{i}_b{self.bshell_b}.nii.gz')):
                    self.N_shm= i
                else:
                    break


        # verify validity of provided/determined N_shm for all subjects
        if self.ref_csv:
            verifyNshmForAll(self.ref_csv, self.N_shm)
        if self.target_csv:
            verifyNshmForAll(self.target_csv, self.N_shm)


        # write config file to temporary directory
        configFile= f'/tmp/harm_config_{os.getpid()}.ini'
        with open(configFile,'w') as f:
            f.write('[DEFAULT]\n')
            f.write(f'N_shm = {self.N_shm}\n')
            f.write(f'N_proc = {self.N_proc}\n')
            f.write(f'N_zero = {self.N_zero}\n')
            f.write(f'resample = {self.resample if self.resample else 0}\n')
            f.write(f'bvalMap = {self.bvalMap if self.bvalMap else 0}\n')
            f.write(f'bshell_b = {self.bshell_b}\n')
            f.write(f'denoise = {1 if self.denoise else 0}\n')
            f.write(f'travelHeads = {1 if self.travelHeads else 0}\n')
            f.write(f'debug = {1 if self.debug else 0}\n')
            f.write(f'verbose = {1 if self.verbose else 0}\n')
            f.write('diffusionMeasures = {}\n'.format((',').join(self.diffusionMeasures)))


        self.sanityCheck()

      if self.create:
          self.createTemplate()

      if self.process:
          self.harmonizeData()

        if self.create and self.process and self.debug:
            self.post_debug()


        os.remove(configFile)


if __name__ == '__main__':
    pipeline.run()

