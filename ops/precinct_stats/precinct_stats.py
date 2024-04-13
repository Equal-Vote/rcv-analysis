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
    'elections': 0,
    'precinct': '',
    # These are empty unless there's an override
    'note1': '',
    'note2': '',
    'note3': '',
    'note4': '',
    'note5': '',
    # These are set based on rcv cruncher
    'first_round_overvote': 0,
    'ranked_single': 0,
    'ranked_multiple': 0,
    'ranked_3_or_more': 0,
    'mean_rankings_used': 0,
    'total_fully_ranked': 0,
    'includes_duplicate_ranking': 0,
    'includes_overvote_ranking': 0,
    'includes_skipped_ranking': 0,
    'total_irregular': 0,
    'total_ballots': 0,
    'total_pretally_exhausted': 0,
    'total_posttally_exhausted': 0,
    'total_posttally_exhausted_by_overvote': 0,
    'total_posttally_exhausted_by_skipped_rankings': 0,
    'total_posttally_exhausted_by_abstention': 0,
    'total_posttally_exhausted_by_rank_limit': 0,
    'total_posttally_exhausted_by_rank_limit_fully_ranked': 0,
    'total_posttally_exhausted_by_rank_limit_partially_ranked': 0,
    'total_posttally_exhausted_by_duplicate_rankings': 0,
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


def parse_precinct_stats(file_names, verbose, census_year):
    demographics = {}
    with open(f'ops/precinct_stats/demographics/{census_year}.csv') as f:
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
                data[precinct].update({
                    'precinct': precinct,
                })
                data[precinct]['elections'] = data[precinct]['elections']+1

                data[precinct]['mean_rankings_used'] = \
                    (
                        data[precinct]['mean_rankings_used'] * data[precinct]['total_ballots'] +
                        stats['mean_rankings_used'][i] * stats['total_ballots'][i]
                    ) / (
                        data[precinct]['total_ballots'] + stats['total_ballots'][i]
                    )

                for key in [
                    'first_round_overvote',
                    'ranked_single',
                    'ranked_multiple',
                    'ranked_3_or_more',
                    'total_fully_ranked',
                    'includes_duplicate_ranking',
                    'includes_overvote_ranking',
                    'includes_skipped_ranking',
                    'total_irregular',
                    'total_ballots',
                    'total_pretally_exhausted',
                    'total_posttally_exhausted',
                    'total_posttally_exhausted_by_overvote',
                    'total_posttally_exhausted_by_skipped_rankings',
                    'total_posttally_exhausted_by_abstention',
                    'total_posttally_exhausted_by_rank_limit',
                    'total_posttally_exhausted_by_rank_limit_fully_ranked',
                    'total_posttally_exhausted_by_rank_limit_partially_ranked',
                    'total_posttally_exhausted_by_duplicate_rankings',
                ]:
                    data[precinct][key] = data[precinct][key] + stats[key][i]

                data[precinct].update(demographics[precinct])

            log(f'{round(time.time()-start)}s')

        except Exception as e:
            log('ERROR')
            if verbose:
                log(traceback.format_exc())
                log(repr(e))

    return data;


