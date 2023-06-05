# S3 Files Downloader

This repository contains a Python script to download files from an AWS S3 bucket. The script utilizes multithreading to download multiple files concurrently, speeding up the process considerably. It is meant to be used with MRI data, but can be adapted to download any type of file.


## Table of Contents

1. [Requirements](#requirements)
2. [Usage](#usage)
3. [Input File Format](#input-file-format)
4. [Contributing](#contributing)
5. [License](#license)

## Requirements

- Python 3.7 or newer
- Boto3 library
- s3fs library

You can install the required Python libraries using pip:
```sh
pip install boto3 s3fs
```

## Usage

To use this script, you'll need to provide a text file containing the S3 paths to the files you want to download, and specify the local directory where the files should be downloaded to.

Here's an example of how to run the script:

```sh
python download_from_s3.py --textfile <path-to-your-textfile> --directory <path-to-local-directory>
```

Replace `<path-to-your-textfile>` with the path to your text file, and `<path-to-local-directory>` with the path to the local directory where you want the files to be downloaded to.

## Input File Format

The input text file should contain two S3 paths per line, separated by a comma. The first path should point to a .nii.gz file, and the second path should point to a .nii.gz mask file.

Here's an example of what the input file format looks like:
```angular2html
s3://mybucket/path/to/file1.nii.gz,s3://mybucket/path/to/file1_mask.nii.gz
s3://mybucket/path/to/file2.nii.gz,s3://mybucket/path/to/file2_mask.nii.gz
...
```

For each line, the script will download the .nii.gz and .nii.gz mask file, as well as any .bval and .bvec files that are in the same directory.

## Contributing

If you have suggestions for how this script could be improved, please fork this repository and create a pull request, or simply open an issue with the tag "enhancement". Thank you!

## License

This project is licensed under the terms of the MIT license.
