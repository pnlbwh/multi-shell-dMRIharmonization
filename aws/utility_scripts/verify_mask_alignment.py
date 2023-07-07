import argparse
import os

import nibabel as nib
import numpy as np
from skimage.metrics import structural_similarity as ssim
from tqdm import tqdm
from multiprocessing import Pool
from pathlib import Path
import logging


def calculate_dice(im1, im2):
    im1 = np.greater(im1, 0)
    im2 = np.greater(im2, 0)

    intersection = np.logical_and(im1, im2)

    return 2. * intersection.sum() / (im1.sum() + im2.sum())


def calculate_ssim_single_slice(im1_slice, im2_slice):
    return ssim(im1_slice, im2_slice)


def calculate_ssim(im1, im2):
    im1_slices = np.asarray(im1.dataobj)
    im2_slices = np.asarray(im2.dataobj)

    with Pool() as pool:
        ssims = pool.starmap(calculate_ssim_single_slice, zip(im1_slices, im2_slices))

    return np.mean(ssims)


def calculate_metrics(subject_files, root_path, dice_flag, ssim_flag):
    subject_id, files = subject_files
    image_path = root_path / files['image']
    mask_path = root_path / files['mask']

    image = nib.load(str(image_path))
    mask = nib.load(str(mask_path))

    # Remove the fourth dimension (if present) from the DWI image
    image_data = np.asarray(image.dataobj)
    if image_data.ndim == 4:
        image_data = np.squeeze(image_data[..., 0])

    metrics = {"subject": subject_id}
    if dice_flag:
        metrics["dice"] = calculate_dice(image_data, np.asarray(mask.dataobj))
    if ssim_flag:
        metrics["ssim"] = calculate_ssim(image_data, np.asarray(mask.dataobj))
    return metrics


def main(root_path, output_file, dice_flag, ssim_flag, nproc):
    root_path = Path(root_path)
    if not root_path.exists() or not root_path.is_dir():
        logging.error(f"The provided root path {root_path} does not exist or is not a directory")
        return

    files = os.listdir(root_path)

    # Group images and masks by subject
    subject_files = {}
    for file in files:
        subject_id = file.split('_')[0]
        if subject_id not in subject_files:
            subject_files[subject_id] = {'image': '', 'mask': ''}
        if 'BrainMask' in file:
            subject_files[subject_id]['mask'] = file
        else:
            subject_files[subject_id]['image'] = file

    # Check alignment for each subject and write results to output file
    with open(output_file, 'w') as f:
        if dice_flag and ssim_flag:
            f.write('subject\tdicecoeff\tssim\n')
        elif dice_flag:
            f.write('subject\tdicecoeff\n')
        elif ssim_flag:
            f.write('subject\tssim\n')

        args_for_calculate_metrics = [(subject_files, root_path, dice_flag, ssim_flag) for subject_files in subject_files.items()]

        if nproc > 1:
            with Pool(nproc) as p:
                for metrics in tqdm(p.imap_unordered(calculate_metrics, args_for_calculate_metrics, chunksize=1),
                                    total=len(subject_files), desc="Processing images", unit="subject"):
                    if dice_flag and ssim_flag:
                        f.write(f"{metrics['subject']}\t{metrics['dice']}\t{metrics['ssim']}\n")
                    elif dice_flag:
                        f.write(f"{metrics['subject']}\t{metrics['dice']}\n")
                    elif ssim_flag:
                        f.write(f"{metrics['subject']}\t{metrics['ssim']}\n")
        else:
            for args in tqdm(args_for_calculate_metrics, total=len(subject_files), desc="Processing images", unit="subject"):
                metrics = calculate_metrics(*args)
                if dice_flag and ssim_flag:
                    f.write(f"{metrics['subject']}\t{metrics['dice']}\t{metrics['ssim']}\n")
                elif dice_flag:
                    f.write(f"{metrics['subject']}\t{metrics['dice']}\n")
                elif ssim_flag:
                    f.write(f"{metrics['subject']}\t{metrics['ssim']}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculate Dice coefficients or SSIM for NIFTI images and masks')
    parser.add_argument('root_path', help='Path to the directory containing the images and masks')
    parser.add_argument('--output', default='results.txt', help='Path to the output file (default: results.txt in the current directory)')
    parser.add_argument('--dice', action='store_true', help='If set, calculates the Dice coefficient')
    parser.add_argument('--ssim', action='store_true', help='If set, calculates the SSIM')
    parser.add_argument('--nproc', default=1, type=int, help='Number of processes to use. If more than 1, enables multiprocessing')
    args = parser.parse_args()

    # If neither dice nor ssim is selected, do both
    if not args.dice and not args.ssim:
        args.dice = args.ssim = True

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    main(args.root_path, args.output, args.dice, args.ssim, args.nproc)
