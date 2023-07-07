#!/usr/bin/env python3
import csv
import argparse
import os
import sys  # for exit with status code


# function to check if a line is valid
def is_valid_line(dwi, mask):
    dwi_base = dwi.rsplit('.nii.gz', 1)[0]  # get the base name without .nii.gz
    # check for different naming convention if 'HCPEP' is in the dwi string
    if 'HCPEP' in dwi:
        return mask == dwi_base + "_mask.nii.gz"
    else:
        return mask == dwi_base + "_bse-multi_BrainMask.nii.gz"


# parse command line arguments
parser = argparse.ArgumentParser(description='Verify paths in CSV file.')
parser.add_argument('--csv', type=str, required=True, help='Path to CSV file.')
parser.add_argument('--out', type=str, default='incorrect_paths.txt',
                    help='Path to output file. (Default: incorrect_paths.txt in the current directory)')

args = parser.parse_args()

# make sure the output file is in the correct directory
output_path = os.path.join(os.getcwd(), args.out)

error_found = False  # flag to check if there was any error

# open the csv file
with open(args.csv, 'r') as f, open(output_path, 'w') as out:
    reader = csv.reader(f)
    out.write("line #, dwi_path, mask_path\n")
    for i, line in enumerate(reader):
        dwi, mask = line[0].strip(), line[1].strip()
        if not is_valid_line(dwi, mask):
            out.write(f'{i + 1}, {dwi}, {mask}\n')
            error_found = True  # set the flag to True as error found

# If error found, print an error message and exit with a non-zero status code
if error_found:
    print(f'Error found. Please check the file {output_path} for details.')
    sys.exit(1)

# If no error found, print a success message
print('All paths are correct.')
