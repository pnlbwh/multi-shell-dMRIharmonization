#!/bin/bash

# ------------------------------------------------------------------------------
# This script runs the MRI data harmonization process.
#
# Version: 1.0
# Updated Date: June 14, 2023,
# Author: Ryan Zurrin
# Company: Brigham and Women's Hospital/Harvard Medical School
# ------------------------------------------------------------------------------

function usage() {
    echo "Usage: $0 -t TAR_LIST -n REF_NAME -T TAR_NAME -p TEMPLATE -d NPROC"
    echo "Options:"
    echo "  -t  Target list"
    echo "  -n  Reference name"
    echo "  -T  Target name"
    echo "  -p  Template"
    echo "  -d  Number of processors"
    exit 1
}

# Parse command line arguments
while getopts r:t:n:T:p:d:h option
do
    case "${option}"
    in
    t) TAR_LIST=${OPTARG};;
    n) REF_NAME=${OPTARG};;
    T) TAR_NAME=${OPTARG};;
    p) TEMPLATE=${OPTARG};;
    d) NPROC=${OPTARG};;
    h) usage;;
    *) echo "Invalid option: -${OPTARG}" >&2; usage;;
    esac
done

# Run the main program if all the parameters are set
if [[ -z "$REF_LIST" || -z "$TAR_LIST" || -z "$REF_NAME" || -z "$TAR_NAME" || -z "$TEMPLATE" || -z "$NPROC" ]]; then
    usage
fi

/home/ec2-user/multi-shell-dMRIharmonization/lib/multi_shell_harmonization.py \
--tar_list "${TAR_LIST}" \
--ref_name "${REF_NAME}" \
--tar_name "${TAR_NAME}" \
--template "${TEMPLATE}" \
--nproc "${NPROC}" \
--process --debug