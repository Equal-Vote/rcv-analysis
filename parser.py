import json
import csv
import argparse
import warnings

from collections import defaultdict
from rcv_cruncher import rank_column_csv, SingleWinner, CastVoteRecord
from pathlib import Path

warnings.simplefilter(action='ignore', category=FutureWarning)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output')
    return parser.parse_args()


def parse_cvrs(file_names):
    data = defaultdict( lambda: {
        # These are derived values
        'election': '',
        'competitive_ratio': -1,
        # These are empty unless there's an override
        'condorcet_failure': '',
        'condorcet_cycle': '',
        'upward_monotonicity_failure': '',
        'downward_monotonicity_failure': '',
        'compromise_failure': '',
        'repeal': '',
        'note1': '',
        'note2': '',
        'note3': '',
        # These are set based on rcv cruncher
        'n_candidates': '',
        'rank_limit': '',
        'restrictive_rank_limit': '',
        'first_round_overvote': '',
        'ranked_single': '',
        'ranked_3_or_more': '',
        'ranked_multiple': '',
        'total_ballots': '',
        'total_fully_ranked': '',
        'mean_rankings_used': '',
        'winner': '',
        'n_rounds': '',
        'total_pretally_exhausted': '',
        'total_posttally_exhausted': '',
        'total_posttally_exhausted_by_overvote': '',
        'total_posttally_exhausted_by_skipped_rankings': '',
        'total_posttally_exhausted_by_abstention': '',
        'total_posttally_exhausted_by_duplicate_rankings': '',
        'total_posttally_exhausted_by_rank_limit': '',
        'total_posttally_exhausted_by_rank_limit_fully_ranked': '',
        'total_posttally_exhausted_by_rank_limit_partially_ranked': '',
        'first_round_winner_vote': '',
        'final_round_winner_vote': '',
        'first_round_winner_percent': '',
        'final_round_winner_percent': '',
        'first_round_winner_place': '',
    })

    for file in file_names:
        election_name = file.split('.')[0]

        # Load election into rcv_cruncher
        base_path = Path.cwd() / 'cvr';
        cvr_file = base_path / file;

        election = SingleWinner(
             parser_func=rank_column_csv,
             parser_args={'cvr_path': cvr_file},
             exhaust_on_duplicate_candidate_marks=False,
             exhaust_on_overvote_marks=True,
             exhaust_on_N_repeated_skipped_marks=0
        )

        stats = election.get_stats()[0].to_dict()
        stats = {k:v[0] for k,v in stats.items()}

        # Compute competitive ratio
        rounds = election.get_round_by_round_dict()
            # TODO: I probably shouldn't assume that the elected will be first
        winner = rounds['results'][-1]['tallyResults'][0]['elected'] 
        bronze = rounds['results'][-2]['tallyResults'][0]['eliminated']
        top3_tally = rounds['results'][-2]['tally']
        competitive_ratio = int(top3_tally[bronze])/int(top3_tally[winner])

        # Generate row
        data[election_name].update({
            'election': election_name,
            'competitive_ratio': competitive_ratio,

            'n_candidates': stats['n_candidates'],
            'rank_limit': stats['rank_limit'],
            'restrictive_rank_limit': stats['restrictive_rank_limit'],
            'first_round_overvote': stats['first_round_overvote'],
            'ranked_single': stats['ranked_single'],
            'ranked_3_or_more': stats['ranked_3_or_more'],
            'ranked_multiple': stats['ranked_multiple'],
            'total_ballots': stats['total_ballots'],
            'total_fully_ranked': stats['total_fully_ranked'],
            'mean_rankings_used': stats['mean_rankings_used'],
            'winner': stats['winner'],
            'n_rounds': stats['n_rounds'],
            'total_pretally_exhausted': stats['total_pretally_exhausted'],
            'total_posttally_exhausted': stats['total_posttally_exhausted'],
            'total_posttally_exhausted_by_overvote': stats['total_posttally_exhausted_by_overvote'],
            'total_posttally_exhausted_by_skipped_rankings': stats['total_posttally_exhausted_by_skipped_rankings'],
            'total_posttally_exhausted_by_abstention': stats['total_posttally_exhausted_by_abstention'],
            'total_posttally_exhausted_by_duplicate_rankings': stats['total_posttally_exhausted_by_duplicate_rankings'],
            'total_posttally_exhausted_by_rank_limit': stats['total_posttally_exhausted_by_rank_limit'],
            'total_posttally_exhausted_by_rank_limit_fully_ranked': stats['total_posttally_exhausted_by_rank_limit_fully_ranked'],
            'total_posttally_exhausted_by_rank_limit_partially_ranked': stats['total_posttally_exhausted_by_rank_limit_partially_ranked'],
            'first_round_winner_vote': stats['first_round_winner_vote'],
            'final_round_winner_vote': stats['final_round_winner_vote'],
            'first_round_winner_percent': stats['first_round_winner_percent'],
            'final_round_winner_percent': stats['final_round_winner_percent'],
            'first_round_winner_place': stats['first_round_winner_place'],
        })

    return data


def add_overrides(data):
    # add overrides
    with open('overrides.json', 'r') as f:
        overrides = json.load(f)
        for election, row in overrides.items():
            row['election'] = election
            data[election].update(row)


def generate_csv(file_name, data):
    with open(file_name, 'w') as f:
        writer = csv.DictWriter(f,
            fieldnames=data[list(data.keys())[0]].keys()
        )
    
        writer.writeheader()
        for key, value in data.items():
            writer.writerow(value)


if __name__ == '__main__':
    args = get_args()

    file_names = [
        'Moab_11022021_CityCouncil.csv',
        # 'Vineyard_11022021_CityCouncil.csv',
        # 'WoodlandHills_11022021_CityCouncil.csv',
    ]

    data = parse_cvrs(file_names)

    add_overrides(data)

    if args.output:
        generate_csv(args.output, data)
    else:
        print(json.dumps(data, indent=4))


