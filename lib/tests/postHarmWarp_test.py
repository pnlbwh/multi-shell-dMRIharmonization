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
from fileUtil import read_caselist
from util import *

SCRIPTDIR = abspath(dirname(__file__))

config = ConfigParser()
config.read(SCRIPTDIR + "/harm_config.ini")
N_proc = int(config["DEFAULT"]["N_proc"])
diffusionMeasures = [
    "FA"
]  # [x for x in config['DEFAULT']['diffusionMeasures'].split(',')]
bshell_b = int(config["DEFAULT"]["bshell_b"])


def antsReg(img, mask, mov, outPrefix):

    if verbose:
        f = sys.stdout
    else:
        logFile = pjoin(outPrefix + "_ANTs.log")
        f = open(logFile, "w")
        print(f"See {logFile} for details of registration")

    if mask:
        p = Popen(
            (" ").join(
                [
                    "antsRegistrationSyNQuick.sh",
                    "-d",
                    "3",
                    "-f",
                    img,
                    "-x",
                    mask,
                    "-m",
                    mov,
                    "-o",
                    outPrefix,
                    "-e",
                    "123456",
                ]
            ),
            shell=True,
            stdout=f,
            stderr=sys.stdout,
        )
        p.wait()
    else:
        p = Popen(
            (" ").join(
                [
                    "antsRegistrationSyNQuick.sh",
                    "-d",
                    "3",
                    "-f",
                    img,
                    "-m",
                    mov,
                    "-o",
                    outPrefix,
                    "-e",
                    "123456",
                ]
            ),
            shell=True,
            stdout=f,
            stderr=sys.stdout,
        )
        p.wait()

    if f.name != "<sys.stdout>":
        f.close()


def register_reference(imgPath, warp2mni, trans2mni, templatePath):

    print(f"Warping {basename(imgPath)} diffusion measures to standard space")
    directory = dirname(imgPath)
    inPrefix = imgPath.split(".nii")[0]
    prefix = basename(inPrefix)

    for dm in diffusionMeasures:

        output = pjoin(templatePath, prefix + f"_InMNI_{dm}.nii.gz")

        # reference site have been already warped to reference template space in buildTemplate.py: warp_bands()
        # warped data are pjoin(templatePath, prefix, prefix + f'_WarpedFA.nii.gz')
        moving = pjoin(templatePath, prefix + f"_Warped{dm}.nii.gz")

        if isfile(moving):
            print("moving image:", basename(moving))
        if isfile(output):
            print("output image:", basename(output), "\n")

        # so warp diffusion measure to MNI space directly
        """
        antsApplyTransforms[
            '-d', '3',
            '-i', moving,
            '-o', output,
            '-r', mniTmp,
            '-t', warp2mni, trans2mni
        ] & FG
        """


def register_target(imgPath, templatePath):

    print(f"Warping {imgPath} diffusion measures to standard space")
    directory = dirname(imgPath)
    inPrefix = imgPath.split(".nii")[0]
    prefix = basename(inPrefix)

    dmImg = pjoin(directory, "dti", prefix + f"_FA.nii.gz")
    outPrefix = pjoin(templatePath, prefix.replace(f"_b{bshell_b}", "") + "_FA_ToMNI")
    warp2mni = outPrefix + "1Warp.nii.gz"
    trans2mni = outPrefix + "0GenericAffine.mat"
    # unprocessed target data is given, so in case multiple debug is needed, pass the registration
    if not exists(warp2mni):
        antsReg(mniTmp, None, dmImg, outPrefix)

    for dm in diffusionMeasures:
        output = pjoin(templatePath, prefix + f"_InMNI_{dm}.nii.gz")

        moving = pjoin(directory, "dti", prefix + f"_{dm}.nii.gz")
        if isfile(moving):
            print("moving image:", basename(moving))
        if isfile(output):
            print("output image:", basename(output), "\n")

        # warp diffusion measure to template space first, then to MNI space
        """
        antsApplyTransforms[
            '-d', '3',
            '-i', moving,
            '-o', output,
            '-r', mniTmp,
            '-t', warp2mni, trans2mni,
        ] & FG
        """


def register_harmonized(imgPath, warp2mni, trans2mni, templatePath, siteName):

    print(f"Warping {imgPath} diffusion measures to standard space")
    directory = dirname(imgPath)
    inPrefix = imgPath.split(".nii")[0]
    prefix = basename(inPrefix)

    dmImg = pjoin(directory, "dti", prefix + f"_FA.nii.gz")
    dmTmp = pjoin(templatePath, f"Mean_{siteName}_FA_b{bshell_b}.nii.gz")
    maskTmp = pjoin(templatePath, f"{siteName}_Mask.nii.gz")
    outPrefix = pjoin(templatePath, prefix.replace(f"_b{bshell_b}", "") + "_FA")
    warp2tmp = outPrefix + "1Warp.nii.gz"
    trans2tmp = outPrefix + "0GenericAffine.mat"

    # check existence of transforms created with _b{bmax}
    if not exists(warp2tmp):
        antsReg(dmTmp, maskTmp, dmImg, outPrefix)

    for dm in diffusionMeasures:
        output = pjoin(templatePath, prefix + f"_InMNI_{dm}.nii.gz")

        moving = pjoin(directory, "dti", prefix + f"_{dm}.nii.gz")
        if isfile(moving):
            print("moving image:", basename(moving))
        if isfile(warp2tmp) and isfile(trans2tmp):
            print("transforms:", basename(warp2tmp), basename(trans2tmp))
        if isfile(output):
            print("output image:", basename(output), "\n")

        # warp diffusion measure to template space first, then to MNI space
        """
        antsApplyTransforms[
            '-d', '3',
            '-i', moving,
            '-o', output,
            '-r', mniTmp,
            '-t', warp2mni, trans2mni, warp2tmp, trans2tmp
        ] & FG
        """


def sub2tmp2mni(
    templatePath, siteName, caselist, ref=False, tar_unproc=False, tar_harm=False
):

    # obtain the transform
    moving = pjoin(templatePath, f"Mean_{siteName}_FA_b{bshell_b}.nii.gz")

    outPrefix = pjoin(templatePath, f"TemplateToMNI_{siteName}")
    warp2mni = outPrefix + "1Warp.nii.gz"
    trans2mni = outPrefix + "0GenericAffine.mat"

    # check existence of transforms created with _b{bmax}
    if not exists(warp2mni):
        antsReg(mniTmp, None, moving, outPrefix)

    imgs, _ = read_caselist(caselist)

    pool = multiprocessing.Pool(N_proc)
    for imgPath in imgs:

        if ref:
            pool.apply_async(
                func=register_reference,
                args=(
                    imgPath,
                    warp2mni,
                    trans2mni,
                    templatePath,
                ),
            )
        elif tar_unproc:
            pool.apply_async(
                func=register_target,
                args=(
                    imgPath,
                    templatePath,
                ),
            )
        elif tar_harm:
            pool.apply_async(
                func=register_harmonized,
                args=(
                    imgPath,
                    warp2mni,
                    trans2mni,
                    templatePath,
                    siteName,
                ),
            )

    pool.close()
    pool.join()

    # loop for debugging
    # for imgPath in imgs:
    #
    #     if ref:
    #         register_reference(imgPath, warp2mni, trans2mni, templatePath)
    #     elif tar_unproc:
    #         register_target(imgPath, templatePath)
    #     elif tar_harm:
    #         register_harmonized(imgPath, warp2mni, trans2mni, templatePath, siteName)


if __name__ == "__main__":
    """
    templatePath='/data/pnl/HarmonizationProject/abcd/site21/site21_cluster/retest_multi/template_April4'
    caselist=f'/data/pnl/HarmonizationProject/abcd/site21/site21_cluster/retest_multi/reference_b{bshell_b}.csv.modified'
    siteName='Reference_Site21'
    sub2tmp2mni(templatePath, siteName, caselist, ref= True)
    """

    templatePath = "/data/pnl/HarmonizationProject/abcd/site21/site21_cluster/retest_multi/template_April4"
    caselist = f"/data/pnl/HarmonizationProject/abcd/site21/site21_cluster/retest_multi/target_b{bshell_b}.csv"
    siteName = "Target_Site21"
    sub2tmp2mni(templatePath, siteName, caselist, tar_unproc=True)

    """
    templatePath='/data/pnl/HarmonizationProject/abcd/site21/site21_cluster/retest_multi/template_April4'
    caselist=f'/data/pnl/HarmonizationProject/abcd/site21/site21_cluster/retest_multi/target_b{bshell_b}.csv.modified.harmonized'
    siteName='Target_Site21'
    sub2tmp2mni(templatePath, siteName, caselist, tar_harm= True)
    """
