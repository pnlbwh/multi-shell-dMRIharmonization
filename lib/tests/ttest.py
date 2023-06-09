#!/usr/bin/env python

import pandas as pd
from scipy.stats import ttest_ind
import sys


def main():
    df_ref = pd.read_csv(sys.argv[1])  # pd.read_csv('Reference_Site21_stat.csv')
    df_harm = pd.read_csv(sys.argv[2])  # pd.read_csv('Target_Site21_after_stat.csv')
    df_tar = pd.read_csv(sys.argv[3])  # pd.read_csv('Target_Site21_before_stat.csv')

    keys = df_ref.columns.values[1:]

    print("ttest among statistics")
    for key in keys:
        print(key)
        print("before", ttest_ind(df_ref[key], df_tar[key])[1])
        print("after", ttest_ind(df_tar[key], df_harm[key])[1])
        print("")


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print("Usage: " "ttest.py ref_stat.csv tar_stat.csv harm_stat.csv")
        exit()

    main()
