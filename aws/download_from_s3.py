# ===============================================================================
# AWS-based automated pipeline for dMRI harmonization (2023) is written by-
#
# RYAN ZURRIN
# Brigham and Women's Hospital/Harvard Medical School
# rzurrin@bwh.harvard.edu, ryanzurrin@gmail.com
#
# ===============================================================================
# See details at https://github.com/RyanZurrin/multi-shell-dMRIharmonization/tree/hcp_aws
# Submit issues at https://github.com/RyanZurrin/multi-shell-dMRIharmonization/issues
# View LICENSE at https://github.com/RyanZurrin/multi-shell-dMRIharmonization//LICENSE
# ===============================================================================

import os
import csv
import argparse
import s3fs
import concurrent.futures
from tqdm import tqdm


def download_from_s3(s3_path, local_path):
    """
    Download a file from S3 to a local directory.

    :param s3_path: Path to the file in S3.
    :param local_path: Path to the local directory.
    """
    fs = s3fs.S3FileSystem()
    try:
        # Check if the file exists in S3
        if fs.exists(s3_path):
            # Download the file
            fs.get(s3_path, os.path.join(local_path, os.path.basename(s3_path)))
            return s3_path
        else:
            print(f"File {s3_path} does not exist in S3")
    except Exception as e:
        print(f"An error occurred while trying to download {s3_path}: {e}")


def download_directory_from_s3(s3_directory, local_directory, multithreading):
    fs = s3fs.S3FileSystem()
    try:
        # Get list of all files in the s3 directory
        files_to_download = fs.glob(s3_directory + "/*")

        # Create the local directory if it doesn't exist
        os.makedirs(local_directory, exist_ok=True)

        # List to store the downloaded files
        downloaded_files = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=multithreading
        ) as executor:
            futures = {
                executor.submit(download_from_s3, file, local_directory)
                for file in files_to_download
            }
            for future in tqdm(
                concurrent.futures.as_completed(futures), total=len(futures)
            ):
                result = future.result()
                if result is not None:
                    downloaded_files.append(result)

        # Print the downloaded files at the end
        print("Downloaded files:")
        for file in downloaded_files:
            print(file)
    except Exception as e:
        print(
            f"An error occurred while trying to download directory {s3_directory}: {e}"
        )


def handle_files(nii_file, mask_file):
    files_to_download = [nii_file, mask_file]
    bval_file = nii_file.replace(".nii.gz", ".bval")
    bvec_file = nii_file.replace(".nii.gz", ".bvec")
    files_to_download.extend([bval_file, bvec_file])
    return files_to_download


def get_files_to_download(textfile):
    files_to_download = []
    _, ext = os.path.splitext(textfile)
    with open(textfile, "r") as f:
        if ext == ".csv":
            reader = csv.reader(f)
            for line in reader:
                if line[0].startswith("#") or line[0].startswith(";"):
                    continue
                nii_file, mask_file = line
                files_to_download.extend(handle_files(nii_file, mask_file))
        else:
            for line in f:
                if line.strip().startswith("#") or line.strip().startswith(";"):
                    continue
                nii_file, mask_file = line.strip().split(",")
                files_to_download.extend(handle_files(nii_file, mask_file))
    return files_to_download


def main():
    parser = argparse.ArgumentParser(
        description="Download files from S3 based on a text file."
    )
    parser.add_argument(
        "-t", "--textfile", help="Path to the text file.", required=False
    )
    parser.add_argument(
        "-d", "--directory", help="Path to the target directory.", required=True
    )
    parser.add_argument(
        "-m",
        "--multithreading",
        type=int,
        help="Number of threads to use for multithreading download.",
        required=False,
    )
    parser.add_argument(
        "-p", "--template", help="Path to the template on S3.", required=False
    )
    args = parser.parse_args()

    # Ensure that the local directory exists
    if not os.path.exists(args.directory):
        os.makedirs(args.directory)

    files_to_download = []
    if args.textfile is not None:
        files_to_download = get_files_to_download(args.textfile)

    print(f"Total files to download: {len(files_to_download)}")

    # List to store the downloaded files
    downloaded_files = []

    # Check if multithreading is requested
    if len(files_to_download) > 0:
        if args.multithreading is not None:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=args.multithreading
            ) as executor:
                futures = {
                    executor.submit(download_from_s3, file, args.directory)
                    for file in files_to_download
                }
                for future in tqdm(
                    concurrent.futures.as_completed(futures), total=len(futures)
                ):
                    result = future.result()
                    if result is not None:
                        downloaded_files.append(result)
        else:
            for file in tqdm(files_to_download):
                result = download_from_s3(file, args.directory)
                if result is not None:
                    downloaded_files.append(result)

    # Download the template if requested
    if args.template is not None:
        download_directory_from_s3(args.template, args.directory, args.multithreading)

    # Print the downloaded files at the end
    print("Downloaded files:")
    for file in downloaded_files:
        print(file)


if __name__ == "__main__":
    main()
