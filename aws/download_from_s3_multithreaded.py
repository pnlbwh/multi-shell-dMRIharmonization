import os
import argparse
import s3fs
import concurrent.futures
from tqdm import tqdm  # Make sure to import tqdm


def download_from_s3(s3_path, local_path):
    """
    Download a file from S3 to a local directory.

    :param s3_path: Path to the file in S3.
    :param local_path: Path to the local directory.
    """
    fs = s3fs.S3FileSystem()

    # Check if the file exists in S3
    if fs.exists(s3_path):
        # Download the file
        fs.get(s3_path, os.path.join(local_path, os.path.basename(s3_path)))
        # Return the file path instead of printing it
        return s3_path
    else:
        print(f"File {s3_path} does not exist in S3")


def main():
    parser = argparse.ArgumentParser(description='Download files from S3 based on a text file.')
    parser.add_argument('-t', '--textfile', help='Path to the text file.', required=True)
    parser.add_argument('-d', '--directory', help='Path to the target directory.', required=True)
    args = parser.parse_args()

    # Get all nii, mask, bval, and bvec files
    files_to_download = []
    with open(args.textfile, 'r') as f:
        for line in f:
            nii_file, mask_file = line.strip().split(',')
            # Also download associated .bval and .bvec files
            bval_file = nii_file.replace('.nii.gz', '.bval')
            bvec_file = nii_file.replace('.nii.gz', '.bvec')
            files_to_download.extend([nii_file, mask_file, bval_file, bvec_file])

    print(f"Total files to download: {len(files_to_download)}")

    # List to store the downloaded files
    downloaded_files = []

    # Download the files using multi-threading
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_from_s3, file, args.directory) for file in files_to_download}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            result = future.result()  # Get the return value from download_from_s3
            if result is not None:
                downloaded_files.append(result)  # Append to the list

    # Print the downloaded files at the end
    print("Downloaded files:")
    for file in downloaded_files:
        print(file)


if __name__ == '__main__':
    main()
