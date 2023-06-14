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

import argparse
import configparser
import subprocess
import sys
import logging
import os


def setup_logging(logfile):
    directory = os.path.dirname(logfile)
    if directory:
        os.makedirs(directory, exist_ok=True)
    logging.basicConfig(
        filename=logfile,
        level=logging.INFO,
        format="%(asctime)s:%(levelname)s:%(message)s",
    )


def run_bash_script(config):
    try:
        command = f"""
        /home/ec2-user/multi-shell-dMRIharmonization/lib/multi_shell_harmonization.py \
        --ref_list "{config['ref_list']}" \
        --tar_list "{config['tar_list']}" \
        --ref_name "{config['ref_name']}" \
        --tar_name "{config['tar_name']}" \
        --template "{config['template']}" \
        --nproc "{config['nproc']}" \
        --create --process --debug
        """
        subprocess.run(command, shell=True, check=True)
        logging.info("Successfully ran the bash script.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while running the bash script: {e}")
        sys.exit(1)


def main(config_file):
    setup_logging("pipeline.log")

    # Load the configuration file
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
        logging.info("Successfully read the configuration file.")
    except configparser.ParsingError as e:
        logging.error(f"An error occurred while parsing the configuration file: {e}")
        sys.exit(1)

    # Check if the directories exist and create them if not
    template_dir = os.path.dirname(config["bash_script"]["template"])
    reference_dir = config["s3_download"]["reference_directory"]
    target_dir = config["s3_download"]["target_directory"]

    for directory in [template_dir, reference_dir, target_dir]:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Checked and/or created the directory: {directory}")

    # Run the download_from_s3 script
    try:
        subprocess.run(
            f"python download_from_s3.py -t {config['s3_download']['reference_textfile']} -d {reference_dir} -m {config['s3_download']['multithreading']}",
            shell=True,
            check=True,
        )
        subprocess.run(
            f"python download_from_s3.py -t {config['s3_download']['target_textfile']} -d {target_dir} -m {config['s3_download']['multithreading']}",
            shell=True,
            check=True,
        )
        logging.info("Successfully ran the download_from_s3 script.")
    except subprocess.CalledProcessError as e:
        logging.error(
            f"An error occurred while running the download_from_s3 script: {e}"
        )
        sys.exit(1)

    # Run the write_local_paths script
    try:
        subprocess.run(
            f"python write_local_paths.py -d {reference_dir} -o {config['local_paths']['reference_output']}",
            shell=True,
            check=True,
        )
        subprocess.run(
            f"python write_local_paths.py -d {target_dir} -o {config['local_paths']['target_output']}",
            shell=True,
            check=True,
        )
        logging.info("Successfully ran the write_local_paths script.")
    except subprocess.CalledProcessError as e:
        logging.error(
            f"An error occurred while running the write_local_paths script: {e}"
        )
        sys.exit(1)

    # Run the bash script
    run_bash_script(config["bash_script"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automated MRI data harmonization pipeline."
    )
    parser.add_argument(
        "--config", type=str, required=True, help="Path to the configuration file."
    )
    args = parser.parse_args()
    main(args.config)
