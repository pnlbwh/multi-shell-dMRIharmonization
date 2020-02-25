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

import multiprocessing
from conversion import write_bvals
from util import *
from fileUtil import read_caselist
from denoising import denoising
from bvalMap import remapBval
from resampling import resampling
from dti import dti
from rish import rish


SCRIPTDIR= dirname(__file__)
config = ConfigParser()
config.read(f'/tmp/harm_config_{getpid()}.ini')

N_shm = int(config['DEFAULT']['N_shm'])
N_proc = int(config['DEFAULT']['N_proc'])
denoise= int(config['DEFAULT']['denoise'])
bvalMap= float(config['DEFAULT']['bvalMap'])
resample= config['DEFAULT']['resample']
bshell_b= float(config['DEFAULT']['bshell_b'])
if resample=='0':
    resample = 0
debug = int(config['DEFAULT']['debug'])
force = int(config['DEFAULT']['force'])



def dti_harm(imgPath, maskPath):

    directory = dirname(imgPath)
    inPrefix = imgPath.split('.nii')[0]
    prefix = basename(inPrefix)

    outPrefix = pjoin(directory, 'dti', prefix)
    if not isfile(outPrefix+'_FA.nii.gz'):
       dti(imgPath, maskPath, inPrefix, outPrefix)

    outPrefix = pjoin(directory, 'harm', prefix)
    if not isfile(outPrefix+'_L0.nii.gz'):
       rish(imgPath, maskPath, inPrefix, outPrefix, N_shm)


def preprocessing(imgPath, maskPath):

    # load signal attributes for pre-processing
    # imgPath= nrrd2nifti(imgPath)
    lowRes = load(imgPath)
    lowResImg = lowRes.get_data().astype('float')
    lowResImgHdr = lowRes.header

    # maskPath= nrrd2nifti(maskPath)
    lowRes = load(maskPath)
    lowResMask = lowRes.get_data()
    lowResMaskHdr = lowRes.header

    lowResImg = applymask(lowResImg, lowResMask)

    # pre-processing

    # modifies data only
    if denoise:
        inPrefix = imgPath.split('.nii')[0]
        outPrefix = inPrefix + '_denoised'

        if force or not isfile(outPrefix+'.nii.gz'):
            print('Denoising ', imgPath)
            lowResImg, _ = denoising(lowResImg, lowResMask)
            save_nifti(outPrefix+'.nii.gz', lowResImg, lowRes.affine, lowResImgHdr)
            copyfile(inPrefix + '.bvec', outPrefix + '.bvec')
            copyfile(inPrefix + '.bval', outPrefix + '.bval')

        maskPath= maskPath

        if debug:
            dti_harm(outPrefix+'.nii.gz', maskPath)

        imgPath= outPrefix+'.nii.gz'


    # modifies data, and bvals
    if bvalMap:
        inPrefix = imgPath.split('.nii')[0]
        outPrefix = inPrefix + '_bmapped'

        if force or not isfile(outPrefix+'.nii.gz'):
            print('B value mapping ', imgPath)
            bvals, _ = read_bvals_bvecs(inPrefix + '.bval', None)
            lowResImg, bvals = remapBval(lowResImg, lowResMask, bvals, bvalMap)
            save_nifti(outPrefix+'.nii.gz', lowResImg, lowRes.affine, lowResImgHdr)
            copyfile(inPrefix + '.bvec', outPrefix + '.bvec')
            write_bvals(outPrefix + '.bval', bvals)

        maskPath= maskPath

        if debug:
            dti_harm(outPrefix+'.nii.gz', maskPath)

        imgPath= outPrefix+'.nii.gz'


    # modifies data, mask, and headers
    sp_high = np.array([float(i) for i in resample.split('x')])
    if resample and (abs(sp_high-lowResImgHdr['pixdim'][1:4])>10e-3).any():
        inPrefix = imgPath.split('.nii')[0]
        outPrefix = inPrefix + '_resampled'

        if force or not isfile(outPrefix+'.nii.gz'):
            print('Resampling ', imgPath)
            bvals, _ = read_bvals_bvecs(inPrefix + '.bval', None)
            imgPath, maskPath = resampling(imgPath, maskPath, lowResImg, lowResImgHdr, lowResMask, lowResMaskHdr, sp_high, bvals)
            copyfile(inPrefix + '.bvec', outPrefix + '.bvec')
            copyfile(inPrefix + '.bval', outPrefix + '.bval')
        else:
            maskPath= maskPath.split('.nii')[0]+ '_resampled.nii.gz'

        if debug:
            dti_harm(outPrefix+'.nii.gz', maskPath)

        imgPath= outPrefix+'.nii.gz'


    return (imgPath, maskPath)



def common_processing(caselist):
    imgs, masks = read_caselist(caselist)
    
    res=[]
    pool = multiprocessing.Pool(N_proc)
    for imgPath,maskPath in zip(imgs,masks):
        res.append(pool.apply_async(func= preprocessing, args= (imgPath,maskPath)))

    attributes= [r.get() for r in res]


    pool.close()
    pool.join()
    

    f = open(caselist + '.modified', 'w')
    for i in range(len(imgs)):
        imgs[i] = attributes[i][0]
        masks[i] = attributes[i][1]
        f.write(f'{imgs[i]},{masks[i]}\n')
    f.close()


    # the following imgs, masks is for diagnosing MemoryError i.e. computing rish w/o preprocessing
    # to diagnose, comment all the above and uncomment the following
    # imgs, masks = read_caselist(caselist+'.modified')

    # experimentally found ncpu=4 to be memroy optimal
    pool = multiprocessing.Pool(4)
    for imgPath,maskPath in zip(imgs,masks):
        pool.apply_async(func= dti_harm, args= (imgPath,maskPath))

    pool.close()
    pool.join()

    return (imgs, masks)

