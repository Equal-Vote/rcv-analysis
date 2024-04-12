import json
import time
import traceback
from collections import defaultdict
from pathlib import Path
import csv

from rcv_cruncher import rank_column_csv, SingleWinner, CastVoteRecord

from util import log

data = defaultdict( lambda: {
    # These are derived values
    'election': '',
    'precinct': '',
    # These are empty unless there's an override
    'note1': '',
    'note2': '',
    'note3': '',
    'note4': '',
    'note5': '',
    # These are set based on rcv cruncher
    'first_round_overvote': '',
    'ranked_single': '',
    'ranked_multiple': '',
    'ranked_3_or_more': '',
    'mean_rankings_used': '',
    'total_fully_ranked': '',
    'includes_duplicate_ranking': '',
    'includes_overvote_ranking': '',
    'includes_skipped_ranking': '',
    'total_irregular': '',
    'total_ballots': '',
    'total_pretally_exhausted': '',
    'total_posttally_exhausted': '',
    'total_posttally_exhausted_by_overvote': '',
    'total_posttally_exhausted_by_skipped_rankings': '',
    'total_posttally_exhausted_by_abstention': '',
    'total_posttally_exhausted_by_rank_limit': '',
    'total_posttally_exhausted_by_rank_limit_fully_ranked': '',
    'total_posttally_exhausted_by_rank_limit_partially_ranked': '',
    'total_posttally_exhausted_by_duplicate_rankings': '',
    # These are from the census demographics
    'Precinct Pop.': '',
    'White': '',
    'Black or African American': '',
    'American Indian and Alaska Native': '',
    'Asian': '',
    'Native Hawaiian and Other Pacific Islander': '',
    'Some Other Race': '',
    'Two or more races': '',
})


def parse_precinct_stats(file_names, verbose):
    demographics = {}
    with open('ops/precinct_stats/demographics/alameda_2020.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            demographics[row['precinct']] = row

    for (i, file) in enumerate(file_names):
        election_name = file.split('.')[0]
        log(f'{i+1}/{len(file_names)} {election_name}....', end='')
        start = time.time()

        try:
            # Load election into rcv_cruncher
            base_path = Path.cwd() / 'cvr';
            cvr_file = base_path / file;

            election = SingleWinner(
                 parser_func=rank_column_csv,
                 parser_args={'cvr_path': cvr_file},
                 exhaust_on_duplicate_candidate_marks=False,
                 exhaust_on_overvote_marks=True,
                 exhaust_on_N_repeated_skipped_marks=0,
                 split_fields=['precinct']
            )

            stats = election.get_stats(add_split_stats=True)[0].to_dict()
            stats = {k.replace('split_', ''):v for k,v in stats.items()}

            # Generate rows
            for i in range(len(stats['field'])):
                precinct = str(stats['value'][i])
                data[f'{election_name}_{precinct}'].update({
                    'election': election_name,
                    'precinct': precinct,

                    'first_round_overvote': stats['first_round_overvote'][i],
                    'ranked_single': stats['ranked_single'][i],
                    'ranked_multiple': stats['ranked_multiple'][i],
                    'ranked_3_or_more': stats['ranked_3_or_more'][i],
                    'mean_rankings_used': stats['mean_rankings_used'][i],
                    'total_fully_ranked': stats['total_fully_ranked'][i],
                    'includes_duplicate_ranking': stats['includes_duplicate_ranking'][i],
                    'includes_overvote_ranking': stats['includes_overvote_ranking'][i],
                    'includes_skipped_ranking': stats['includes_skipped_ranking'][i],
                    'total_irregular': stats['total_irregular'][i],
                    'total_ballots': stats['total_ballots'][i],
                    'total_pretally_exhausted': stats['total_pretally_exhausted'][i],
                    'total_posttally_exhausted': stats['total_posttally_exhausted'][i],
                    'total_posttally_exhausted_by_overvote': stats['total_posttally_exhausted_by_overvote'][i],
                    'total_posttally_exhausted_by_skipped_rankings': stats['total_posttally_exhausted_by_skipped_rankings'][i],
                    'total_posttally_exhausted_by_abstention': stats['total_posttally_exhausted_by_abstention'][i],
                    'total_posttally_exhausted_by_rank_limit': stats['total_posttally_exhausted_by_rank_limit'][i],
                    'total_posttally_exhausted_by_rank_limit_fully_ranked': stats['total_posttally_exhausted_by_rank_limit_fully_ranked'][i],
                    'total_posttally_exhausted_by_rank_limit_partially_ranked': stats['total_posttally_exhausted_by_rank_limit_partially_ranked'][i],
                    'total_posttally_exhausted_by_duplicate_rankings': stats['total_posttally_exhausted_by_duplicate_rankings'][i],
                })
                data[f'{election_name}_{precinct}'].update(demographics[precinct])

            log(f'{round(time.time()-start)}s')

        except Exception as e:
            log('ERROR')
            if verbose:
                log(traceback.format_exc())
                log(repr(e))

    return data;


