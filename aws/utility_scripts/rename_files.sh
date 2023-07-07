#!/bin/bash

# Check if correct number of arguments are provided
if [ $# -ne 3 ]; then
  echo "Incorrect number of arguments supplied!"
  echo "Usage: ./rename_files.sh [path] [target_string] [replacement_string]"
  exit 1
fi

# Assigning arguments to variables
root_dir=$1
target_string=$2
replacement_string=$3

# change to the directory containing the files
cd $root_dir

# Check if directory change was successful
if [ $? -ne 0 ]; then
  echo "Error accessing directory $root_dir"
  exit 1
fi

# loop over all files with target string in the name
for file in *${target_string}*; do
  # replace target string with replacement string in the file name
  new_name=${file//$target_string/$replacement_string}

  # rename the file
  mv -n "$file" "$new_name"
done

