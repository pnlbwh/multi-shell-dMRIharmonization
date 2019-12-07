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

from plumbum.cmd import antsApplyTransforms
from plumbum import FG
import multiprocessing
import numpy as np
from test_util import *
import argparse
from conversion import read_imgs, read_imgs_masks

ROOTDIR= abspath(pjoin(LIBDIR, '..'))
mniTmp = pjoin(ROOTDIR, 'IITAtlas', 'IITmean_FA.nii.gz')

diffusionMeasures = ['MD', 'FA', 'GFA']


def printStat(ref_mean, imgs):

    print('mean FA over IIT_mean_FA_skeleton.nii.gz for all cases: ')
    for i, imgPath in enumerate(imgs):
        print(basename(imgPath), ref_mean[i])

    print('')
    print('mean meanFA: ', np.mean(ref_mean))
    print('std meanFA: ', np.std(ref_mean))
    print('')


def read_caselist(file):

    with open(file) as f:

        imgs = []
        content= f.read()
        for line, row in enumerate(content.split()):
            temp= [element for element in row.split(',') if element] # handling w/space

            for img in temp:
                if not isfile(img):
                    raise FileNotFoundError(f'{img} does not exist: check line {line} in {file}')

            imgs.append(temp[0])

    return imgs

def antsReg(img, mask, mov, outPrefix, n_thread=1):

    if mask:
        p= Popen((' ').join(['antsRegistrationSyNQuick.sh',
                               '-d', '3',
                               '-f', img,
                               '-x', mask,
                               '-m', mov,
                               '-n', str(n_thread),
                               '-o', outPrefix]), shell= True)
        p.wait()
    else:
        p= Popen((' ').join(['antsRegistrationSyNQuick.sh',
                               '-d', '3',
                               '-f', img,
                               '-m', mov,
                               '-n', str(n_thread),
                               '-o', outPrefix]), shell= True)
        p.wait()


def register_subject(imgPath, warp2mni, trans2mni, templatePath, siteName, bshell_b):

    print(f'Warping {imgPath} diffusion measures to standard space')
    directory = dirname(imgPath)

    # should have _FA a the end already
    basePrefix= psplit(imgPath)[-1].split('.')[0]
    prefix = basePrefix.replace('_FA', '')

    # given data and harmonized data are in the same space, so need to register again
    basePrefix= basePrefix.replace('harmonized_','')
    outPrefix = pjoin(templatePath, basePrefix.replace(f'_b{bshell_b}', '_FA_ToTemplate'))  # should have _FA a the end

    dmTmp = pjoin(templatePath, f'Mean_{siteName}_FA_b{bshell_b}.nii.gz')
    maskTmp = pjoin(templatePath, f'{siteName}_Mask.nii.gz')
    warp2tmp = outPrefix + '1Warp.nii.gz'
    trans2tmp = outPrefix + '0GenericAffine.mat'

    # check existence of transforms created with _b{bmax}
    if not isfile(warp2tmp):
        antsReg(dmTmp, maskTmp, imgPath, outPrefix)

    for dm in diffusionMeasures:
        output = pjoin(templatePath, prefix + f'_InMNI_{dm}.nii.gz')
        moving = pjoin(directory, prefix + f'_{dm}.nii.gz')
        # warp diffusion measure to template space first, then to MNI space
        antsApplyTransforms[
            '-d', '3',
            '-i', moving,
            '-o', output,
            '-r', mniTmp,
            '-t', warp2mni, trans2mni, warp2tmp, trans2tmp
        ] & FG

    return pjoin(templatePath, prefix + f'_InMNI_FA.nii.gz')


def sub2tmp2mni(templatePath, siteName, faImgs, bshell_b, N_proc):

    # obtain the transform
    moving = pjoin(templatePath, f'Mean_{siteName}_FA_b{bshell_b}.nii.gz')

    outPrefix= pjoin(templatePath, f'TemplateToMNI_{siteName}')
    warp2mni= outPrefix+'1Warp.nii.gz'
    trans2mni= outPrefix+'0GenericAffine.mat'
    # template is created once, it is expected that the user wants to keep the template same during debugging
    # so in case multiple debug is needed, pass the registration
    if not isfile(warp2mni):
        antsReg(mniTmp, None, moving, outPrefix, N_proc)

    
    pool= multiprocessing.Pool(N_proc)
    res=[]
    for imgPath in faImgs:
        res.append(pool.apply_async(func= register_subject,
                   args= (imgPath, warp2mni, trans2mni, templatePath, siteName, bshell_b, )))

    mniFAimgs= [r.get() for r in res]

    pool.close()
    pool.join()
    
    
    ''' 
    # loop for debugging
    mniFAimgs= []
    for imgPath in faImgs:
        mniFAimgs.append(register_subject(imgPath, warp2mni, trans2mni, templatePath, siteName, bshell_b))
    '''

    return mniFAimgs



def analyzeStat(faImgs):
    '''
    :param file: list of (FA or MD or GFA) that are already in MNI space
    :return: mean of the images
    '''

    skel= load(pjoin(ROOTDIR, 'IITAtlas', 'IITmean_FA_skeleton.nii.gz'))
    skel_mask= (skel.get_data()>0)*1.

    meanAttr=[]
    for faImg in faImgs:
        data= load(faImg).get_data()
        temp= data*skel_mask
        meanAttr.append(temp[temp>0].mean())

    return meanAttr


def main():

    parser = argparse.ArgumentParser(description='''Warps diffusion measures (FA, MD, GFA) to template space 
    and then to MNI space. Finally, calculates mean FA over IITmean_FA_skeleton.nii.gz''')
    parser.add_argument('-i', '--input', type=str, required=True, 
        help='a .txt/.csv file having one column for FA imgs, '
             'or two columns for (img,mask) pair, the latter list is what you used in/obtained from harmonization.py. '
             'See pnlbwh/dMRIharmonization documentation for more details')
    parser.add_argument('-s', '--site', type= str, required=True,
                        help='site name for locating template FA and mask in tempalte directory')
    parser.add_argument('-t', '--template', type=str, required=True,
                        help='template directory where Mean_{site}_FA.nii.gz and {site}_Mask.nii.gz is located')
    parser.add_argument('--bshell_b', required=True, help='bvalue of the bshell')
    parser.add_argument('--ncpu', help='number of cpus to use', default= '4')

    args = parser.parse_args()
    imgList=abspath(args.input)
    siteName=args.site
    templatePath=abspath(args.template)
    bshell_b= int(args.bshell_b)
    N_proc= int(args.ncpu)

    # read FA image list
    try:
        imgs, _ = read_imgs_masks(imgList)
        print('imgs,masks list is provided. FA images are assumed to be directoryOfImg/dti/ImgPrefix_FA.nii.gz, make sure they are there')
        faImgs= []

        for imgPath in imgs:
            directory = dirname(imgPath)
            prefix = basename(imgPath).split('.')[0]
            faImg= pjoin(directory, 'dti', prefix+ '_FA.nii.gz')
            if not isfile(faImg):
                raise FileNotFoundError(f'{faImg} not found. Did you run \"--create --debug\" and \"--process --debug\" before?')

            faImgs.append(faImg)


    except:
        faImgs= read_imgs(imgList)
        print('FA image list is provided.')
    

    # register and obtain *_InMNI_FA.nii.gz
    mniFAimgs= sub2tmp2mni(templatePath, siteName, faImgs, bshell_b, N_proc)
    
    # save statistics for future
    statFile= os.path.join(self.templatePath, 'meanFAstat.txt')
    f= open(statFile,'a')
    stdout= sys.stdout
    sys.stdout= f

    print(datetime.now().strftime('%c'),'\n')

    print('b-shell', bshell_b, '\n')

    # pass *_InMNI_FA.nii.gz list to analyzeStat
    site_means= analyzeStat(mniFAimgs)
    print(f'{siteName} site: ')
    printStat(site_means, mniFAimgs)

    f.close()
    sys.stdout= stdout

    # print statistics on console
    print('')
    with open(statFile) as f:
        print(f.read())

    print('\nThe statistics are also saved in ', statFile)



if __name__ == '__main__':
    main()

