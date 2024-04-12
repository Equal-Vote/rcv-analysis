import sys
import os
import argparse
import time
import json
import csv
import warnings

from ops.election_stats.election_stats import parse_election_stats
from ops.precinct_stats.precinct_stats import parse_precinct_stats
from ops.block_to_precinct.block_to_precinct import parse_block_to_precinct
from ops.precincts_to_kml.precincts_to_kml import precincts_to_kml

from util import *

warnings.simplefilter(action='ignore', category=FutureWarning)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('op', choices=['election-stats', 'precinct-stats', 'precincts-to-kml', 'block-to-precinct'])
    parser.add_argument('-o', '--output')
    parser.add_argument('-v', '--verbose', action='store_true')
    # block to precinct
    parser.add_argument('-m', '--mapper-file')
    parser.add_argument('-b', '--block-file')
    # kml specific args
    parser.add_argument('-p', '--precincts-file')
    parser.add_argument('-r', '--apply-race-colors', action='store_true')
    parser.add_argument('-z', '--z-axis')
    return parser.parse_args()


def generate_csv(file_name):
    with open(file_name, 'w') as f:
        writer = csv.DictWriter(f,
            fieldnames=data[list(data.keys())[0]].keys(),
            lineterminator='\n',
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
        data = parse_precinct_stats(cvr_files, args.verbose)

    if args.op == 'block-to-precinct':
        data = parse_block_to_precinct(args.block_file, args.mapper_file, args.output)

    if args.op == 'precincts-to-kml':
        data = precincts_to_kml(args.precincts_file, args.output, args.z_axis, args.apply_race_colors)

    log(f'Total Time: {round(time.time()-start)}s')

    if args.op in ('election-stats', 'precinct-stats',):
        if args.output:
            generate_csv(args.output)
        else:
            log(json.dumps(data, indent=4))