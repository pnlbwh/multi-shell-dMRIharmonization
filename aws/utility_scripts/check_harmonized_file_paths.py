import csv
import argparse
import s3fs
from tqdm import tqdm

def check_s3_object(fs, path):
    try:
        return fs.exists(path)
    except:
        return False

def verify_s3_paths(input_path, output_path):
    fs = s3fs.S3FileSystem()

    with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
        # Determine if input is CSV or TXT based on file extension
        if input_path.endswith('.csv'):
            reader = csv.reader(f_in)
            rows = list(reader)
            for line_num, row in tqdm(enumerate(rows, start=1), total=len(rows)):
                for s3_path in row:
                    if not check_s3_object(fs, s3_path.replace("s3://", "")):
                        f_out.write(f"{line_num},{s3_path}\n")
        else:  # Treat as text file with one path per line
            paths = f_in.read().splitlines()
            for line_num, s3_path in tqdm(enumerate(paths, start=1), total=len(paths)):
                if not check_s3_object(fs, s3_path.replace("s3://", "")):
                    f_out.write(f"{line_num},{s3_path}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Path to the input file (CSV or TXT).")
    parser.add_argument("-o", "--output_file", default="output.csv",
                        help="Optional path to output CSV file. Default is 'output.csv' in the current directory.")

    args = parser.parse_args()

    verify_s3_paths(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
