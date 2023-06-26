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


def setup_logging(logfile, verbose):
    directory = os.path.dirname(logfile)
    if directory:
        os.makedirs(directory, exist_ok=True)
    logging.basicConfig(
        filename=logfile,
        level=logging.INFO,
        format="%(asctime)s:%(levelname)s:%(message)s",
    )
    if verbose:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
        console.setFormatter(formatter)
        logging.getLogger("").addHandler(console)


def run_bash_script(config, create, process, debug):
    """
    Run the bash script that calls the multi-shell harmonization script.

    Parameters:
    :param config: ConfigParser object containing the configuration file.
    :param create: Boolean indicating whether to create the harmonized images.
    :param process: Boolean indicating whether to process the harmonized images.
    :param debug: Boolean indicating whether to print debug messages in the terminal.
    """
    command = f"""    
    /home/ec2-user/multi-shell-dMRIharmonization/lib/multi_shell_harmonization.py \
    --ref_list "{config['ref_list']}" \
    --tar_list "{config['tar_list']}" \
    --ref_name "{config['ref_name']}" \
    --tar_name "{config['tar_name']}" \
    --template "{config['template']}" \
    --nproc "{config['nproc']}" """

    if create:
        command += " --create"
    if process:
        command += " --process"
    if debug:
        command += " --debug"

    # log the command
    logging.info(f"Running the following command: {command}")

    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            log_message = output.strip().decode("utf-8")
            logging.info(log_message)
            if verbose:
                print(log_message)
    rc = process.poll()
    if rc != 0:
        logging.error("An error occurred while running the bash script")
        sys.exit(1)


def main(args_):
    setup_logging("pipeline.log", args_.verbose)

    # Load the configuration file
    config = configparser.ConfigParser()
    config.read(args_.config)
    logging.info("Successfully read the configuration file.")

    # Check if the directories exist and create them if not
    template_dir = os.path.dirname(config["bash_script"]["template"])
    reference_dir = config["s3_download"]["reference_directory"]
    target_dir = config["s3_download"]["target_directory"]

    # if the flags create, process and debug are not in args, then look for them in the config file, if they not there
    # then set them to True by default
    if not args_.create:
        if "create" in config["bash_script"]:
            create = config.getboolean("bash_script", "create")
        else:
            create = False
    else:
        create = args_.create

    if not args_.process:
        if "process" in config["bash_script"]:
            process = config.getboolean("bash_script", "process")
        else:
            process = False
    else:
        process = args_.process

    if not args_.debug:
        if "debug" in config["bash_script"]:
            debug = config.getboolean("bash_script", "debug")
        else:
            debug = False
    else:
        debug = args_.debug

    # log all the args and config settings that will be used
    logging.info(f"create: {create}")
    logging.info(f"process: {process}")
    logging.info(f"debug: {debug}")
    logging.info(f"template_dir: {template_dir}")
    logging.info(f"reference_dir: {reference_dir}")
    logging.info(f"target_dir: {target_dir}")
    logging.info(f"ref_list: {config['bash_script']['ref_list']}")
    logging.info(f"tar_list: {config['bash_script']['tar_list']}")
    logging.info(f"ref_name: {config['bash_script']['ref_name']}")
    logging.info(f"tar_name: {config['bash_script']['tar_name']}")
    logging.info(f"template: {config['bash_script']['template']}")
    logging.info(f"nproc: {config['bash_script']['nproc']}")
    logging.info(f"multithreading: {config['s3_download']['multithreading']}")
    logging.info(f"reference_output: {config['local_paths']['reference_output']}")
    logging.info(f"target_output: {config['local_paths']['target_output']}")

    for directory in [template_dir, reference_dir, target_dir]:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Checked and/or created the directory: {directory}")

    # Run the download_from_s3 script
    try:
        # check that reference and target are not empty strings and if not run the download_from_s3 script
        if reference_dir != "":
            subprocess.run(
                f"python download_from_s3.py -t {config['s3_download']['reference_textfile']} -d {reference_dir} -m {config['s3_download']['multithreading']}",
                shell=True,
                check=True,
            )
            logging.info(
                "Successfully ran the download_from_s3 script for the reference data."
            )
        if target_dir != "":
            subprocess.run(
                f"python download_from_s3.py -t {config['s3_download']['target_textfile']} -d {target_dir} -m {config['s3_download']['multithreading']}",
                shell=True,
                check=True,
            )
            logging.info(
                "Successfully ran the download_from_s3 script for the target data."
            )
    except subprocess.CalledProcessError as e:
        logging.error(
            f"An error occurred while running the download_from_s3 script: {e}"
        )
        sys.exit(1)

    # download the template if it is specified in the config file
    if (
        "s3_download" in config
        and "template_path" in config["s3_download"]
        and config["s3_download"]["template_path"]
    ):
        try:
            subprocess.run(
                f"python download_from_s3.py -p {config['s3_download']['template_path']} -d {template_dir} -m {config['s3_download']['multithreading']}",
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
    run_bash_script(config["bash_script"], create, process, debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automated MRI data harmonization pipeline."
    )
    parser.add_argument(
        "--config", type=str, required=True, help="Path to the configuration file."
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print log messages in the terminal."
    )
    parser.add_argument(
        "--debug", action="store_true", help="Print debug messages in the terminal."
    )
    parser.add_argument(
        "--create", action="store_true", help="Create the harmonized images."
    )
    parser.add_argument(
        "--process", action="store_true", help="Process the harmonized images."
    )
    args = parser.parse_args()
    main(args)
