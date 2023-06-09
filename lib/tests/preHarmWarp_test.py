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
from glob import glob

from scipy.ndimage import binary_opening, generate_binary_structure
from scipy.ndimage.filters import gaussian_filter
from util import *
import sys
from fileUtil import read_caselist

eps = 2.2204e-16
SCRIPTDIR = abspath(dirname(__file__))
config = ConfigParser()
config.read(SCRIPTDIR + "/harm_config.ini")
N_shm = int(config["DEFAULT"]["N_shm"])
N_proc = int(config["DEFAULT"]["N_proc"])
bshell_b = int(config["DEFAULT"]["bshell_b"])
diffusionMeasures = [x for x in config["DEFAULT"]["diffusionMeasures"].split(",")]
travelHeads = int(config["DEFAULT"]["travelHeads"])
verbose = int(config["DEFAULT"]["verbose"])


def applyXform(inImg, refImg, warp, trans, outImg):

    (
        antsApplyTransforms[
            "-d",
            "3",
            "-i",
            inImg,
            "-o",
            "/tmp/test.nii.gz",
            "--verbose",  # outImg,
            "-r",
            refImg,
            "-t",
            warp,
            "-t",
            trans,
        ]
        & FG
    )


def warp_bands(imgPath, maskPath, templatePath):

    prefix = basename(imgPath).split(".nii")[0]
    transPrefix = prefix.replace(f"_b{bshell_b}", "")
    directory = dirname(imgPath)
    warp = glob(pjoin(templatePath, transPrefix + f"*_FA*[!ToMNI]1Warp.nii.gz"))
    trans = glob(pjoin(templatePath, transPrefix + f"*_FA*[!ToMNI]0GenericAffine.mat"))

    # print(prefix)
    # print('transforms', warp, trans,'\n\n')

    # warping the mask
    applyXform(
        maskPath,
        pjoin(templatePath, "template0.nii.gz"),
        warp,
        trans,
        pjoin(templatePath, basename(maskPath).split(".nii")[0] + "Warped.nii.gz"),
    )

    """
    # warping the rish features
    for i in range(0, N_shm+1, 2):
        applyXform(pjoin(directory, 'harm', f'{prefix}_L{i}.nii.gz'),
           pjoin(templatePath, 'template0.nii.gz'),
           warp, trans,
           pjoin(templatePath, f'{prefix}_WarpedL{i}.nii.gz'))


    # warping the diffusion measures
    for dm in diffusionMeasures:
        applyXform(pjoin(directory, 'dti', f'{prefix}_{dm}.nii.gz'),
                   pjoin(templatePath, 'template0.nii.gz'),
                   warp, trans,
                   pjoin(templatePath, f'{prefix}_Warped{dm}.nii.gz'))
    
    """


if __name__ == "__main__":

    templatePath = "/data/pnl/HarmonizationProject/abcd/site21/site21_cluster/retest_multi/template_April4"

    img_list = "/data/pnl/HarmonizationProject/abcd/site21/site21_cluster/retest_multi/target_b1000.csv.modified"
    imgs, masks = read_caselist(img_list)

    for imgPath, maskPath in zip(imgs, masks):
        warp_bands(imgPath, maskPath, templatePath)
