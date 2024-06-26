import sys
import os
import argparse
import time
import json
import csv
import warnings
import pandas

from ops.election_stats.election_stats import parse_election_stats
from ops.cvr_to_csv.cvr_to_csv import parse_cvr
from ops.precinct_stats.precinct_stats import parse_precinct_stats
from ops.block_to_precinct.block_to_precinct import parse_block_to_precinct
from ops.precincts_to_kml.precincts_to_kml import precincts_to_kml

from util import *

warnings.simplefilter(action='ignore', category=FutureWarning)

demographics = {}

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('op', choices=['election-stats', 'precinct-stats', 'precincts-to-kml', 'block-to-precinct','cvr-to-csv'])
    parser.add_argument('-o', '--output')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-y', '--census-year', default='2020')
    # block to precinct
    parser.add_argument('-m', '--mapper-file')
    parser.add_argument('-b', '--block-file')
    # kml specific args
    parser.add_argument('-p', '--precincts-file')
    parser.add_argument('-r', '--apply-race-colors', action='store_true')
    parser.add_argument('-z', '--z-axis')
    # cvr to csv
    parser.add_argument('-c', '--raw-cvr')
    return parser.parse_args()


def clean_precincts(cvrs, valid_precincts):
    log('cleaning cvrs...')

    for cvr in cvrs:
        df = pandas.read_csv(f'cvr/{cvr}')

        # Clean column
        if 'precincts' in df.columns:
            df = df.rename(columns={'precincts': 'precinct'})

        if 'precinct' not in df.columns and 'PrecinctPortion' in df.columns: # some things have both, but if they only have one then we can convert it
            df = df.rename(columns={'PrecinctPortion': 'precinct'})
        
        if 'precinct' not in df.columns:
            raise Exception(f'precinct not in {df.columns} for {cvr}')

        # Clean precinct numbers
        def clean_precinct(p):
            p = str(p)
            # PCT 7539 # remove the PCT
            # PCT 7539/1234 
            p = p.replace('PCT ', '')
            # 213456 (055) # remove the extension
            p = p.split(' ')[0]
            # 9514/22 # I want to remove the 22 in these cases
            # 9503/9504 # SF has some that list multiple precincts. I'm just 
            if '/' in p:
                ps = p.split('/')[0]
                p = ps[0] if ps[0] in valid_precincts else ps[1]
            # 9213456 # precincts are 6 digits, ignore the 9
            # NOTE: they're 6 digits in Alameda, but 4 digits in San Francisco, that's why we do this later
            p = p[-6:]
            return p

        df['precinct'] = df['precinct'].apply(clean_precinct)
        
        df.to_csv(f'cvr/{cvr}', index=False)


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
        # TODO: I can probably move demographics and clean_precincts into parse_precinct_stats
        demographics = {}
        with open(f'ops/precinct_stats/demographics/{args.census_year}.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                demographics[row['precinct']] = row

        clean_precincts(cvr_files, demographics.keys())
        data = parse_precinct_stats(cvr_files, args.verbose, args.census_year, demographics)

    if args.op == 'block-to-precinct':
        data = parse_block_to_precinct(args.block_file, args.mapper_file, args.output, args.census_year)

    if args.op == 'cvr-to-csv':
        data = parse_cvr(args.raw_cvr)

    if args.op == 'precincts-to-kml':
        data = precincts_to_kml(args.precincts_file, args.output, args.z_axis, args.apply_race_colors, args.census_year)

    log(f'Total Time: {round(time.time()-start)}s')

    if args.op in ('election-stats', 'precinct-stats', 'cvr-to-csv'):
        if args.output:
            generate_csv(args.output)
        else:
            log(json.dumps(data, indent=4))