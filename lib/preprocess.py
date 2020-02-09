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
from glob import glob

SCRIPTDIR= os.path.dirname(__file__)
config = ConfigParser()
config.read(f'/tmp/harm_config_{os.getpid()}.ini')

N_shm = int(config['DEFAULT']['N_shm'])
N_proc = int(config['DEFAULT']['N_proc'])
denoise= int(config['DEFAULT']['denoise'])
bvalMap= float(config['DEFAULT']['bvalMap'])
resample= config['DEFAULT']['resample']
bshell_b= float(config['DEFAULT']['bshell_b'])
if resample=='0':
    resample = 0
debug = int(config['DEFAULT']['debug'])



def dti_harm(imgPath, maskPath):

    directory = os.path.dirname(imgPath)
    inPrefix = imgPath.split('.nii')[0]
    prefix = basename(inPrefix)

    outPrefix = os.path.join(directory, 'dti', prefix)
    if not glob(outPrefix+'_FA.nii.gz'):
       dti(imgPath, maskPath, inPrefix, outPrefix)

    outPrefix = os.path.join(directory, 'harm', prefix)
    if not glob(outPrefix+'_L0.nii.gz'):
       rish(imgPath, maskPath, inPrefix, outPrefix, N_shm)



def preprocessing(imgPath, maskPath):

    # load signal attributes for pre-processing ----------------------------------------------------------------
    # imgPath= nrrd2nifti(imgPath)
    lowRes = load(imgPath)
    lowResImg = lowRes.get_data().astype('float')
    lowResImgHdr = lowRes.header

    # maskPath= nrrd2nifti(maskPath)
    lowRes = load(maskPath)
    lowResMask = lowRes.get_data()
    lowResMaskHdr = lowRes.header

    lowResImg = applymask(lowResImg, lowResMask)

    inPrefix = imgPath.split('.nii')[0]

    bvals, _ = read_bvals_bvecs(inPrefix + '.bval', None)

    # pre-processing -------------------------------------------------------------------------------------------
    suffix= None
    # modifies data only
    if denoise:
        print('Denoising ', imgPath)
        lowResImg, _ = denoising(lowResImg, lowResMask)
        suffix = '_denoised'
        if debug:
            outPrefix= imgPath.split('.nii')[0]+suffix
            save_nifti(outPrefix+'.nii.gz', lowResImg, lowRes.affine, lowResImgHdr)
            shutil.copyfile(inPrefix + '.bvec', outPrefix + '.bvec')
            shutil.copyfile(inPrefix + '.bval', inPrefix + '.bval')
            dti_harm(outPrefix+'.nii.gz', maskPath)

    # modifies data, and bvals
    if bvalMap:
        print('B value mapping ', imgPath)
        lowResImg, bvals = remapBval(lowResImg, lowResMask, bvals, bvalMap)
        suffix = '_bmapped'
        if debug:
            outPrefix= imgPath.split('.nii')[0]+suffix
            save_nifti(outPrefix+'.nii.gz', lowResImg, lowRes.affine, lowResImgHdr)
            shutil.copyfile(inPrefix + '.bvec', outPrefix + '.bvec')
            write_bvals(outPrefix + '.bval', bvals)
            dti_harm(outPrefix+'.nii.gz', maskPath)

    # modifies data, mask, and headers
    if resample:
        print('Resampling ', imgPath)
        sp_high = np.array([float(i) for i in resample.split('x')])
        if (abs(sp_high-lowResImgHdr['pixdim'][1:4])>10e-3).any():
            imgPath, maskPath = \
                resampling(imgPath, maskPath, lowResImg, lowResImgHdr, lowResMask, lowResMaskHdr, sp_high, bvals)
            suffix = '_resampled'


    # save pre-processed data; resampled data is saved inside resampling() -------------------------------------
    if (denoise or bvalMap) and suffix!= '_resampled':
        imgPath = inPrefix + suffix + '.nii.gz'
        save_nifti(imgPath, lowResImg, lowRes.affine, lowResImgHdr)

    if suffix:
        shutil.copyfile(inPrefix + '.bvec', inPrefix + suffix + '.bvec')
    if bvalMap:
        write_bvals(inPrefix + suffix + '.bval', bvals)
    elif denoise or suffix== '_resampled':
        shutil.copyfile(inPrefix + '.bval', inPrefix + suffix + '.bval')


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

