import sys
import os
import argparse
import time
import json
import csv
import warnings

from election_stats import parse_election_stats

from util import *

warnings.simplefilter(action='ignore', category=FutureWarning)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('op', choices=['election-stats', 'precinct-stats', 'append-kml', 'parse-census'])
    parser.add_argument('-o', '--output')
    parser.add_argument('-v', '--verbose', action='store_true')
    # kml specific args
    parser.add_argument('-k', '--base-kml')
    parser.add_argument('-e', '--election-file')
    parser.add_argument('-d', '--demographics-file')
    parser.add_argument('-c', '--color', choices=['race'])
    parser.add_argument('-z', '--z-axis')
    return parser.parse_args()


def generate_csv(file_name):
    with open(file_name, 'w') as f:
        writer = csv.DictWriter(f,
            fieldnames=data[list(data.keys())[0]].keys()
        )
    
        writer.writeheader()
        for key, value in data.items():
            writer.writerow(value)


if __name__ == '__main__':
    args = get_args()

    cvr_files = os.listdir('cvr/')
    # cvr_files = ['Moab_11022021_CityCouncil.csv']


    start = time.time()

    if args.op == 'election-stats':
        data = parse_election_stats(cvr_files, args.verbose)

    if args.op == 'precinct-stats':
        pass
    if args.op == 'append-kml':
        pass
    if args.op == 'parse-census':
        pass

    log(f'Total Time: {round(time.time()-start)}s')


    if args.op in ('election-stats', 'precinct-stats', 'parse-census',):
        if args.output:
            generate_csv(args.output)
        else:
            log(json.dumps(data, indent=4))


