import json
import time
from collections import defaultdict
from pathlib import Path
import traceback
from copy import copy

from rcv_cruncher import rank_column_csv, SingleWinner, CastVoteRecord 

from util import *

data = defaultdict( lambda: {
    # These are derived from top stats
    'election': '',
    'competitive_ratio': -1,
    'min_elimination_margin': 0,
    # These are empty unless there's an override
    'upward_monotonicity_failure': '',
    'downward_monotonicity_failure': '',
    'compromise_failure': '',
    'repeal': '',
    'note1': '',
    'note2': '',
    'note3': '',
    'note4': '',
    'note5': '',
    # These are derived from iterating over ballot
    'total_rankings_used': 0,
    'total_rankings_skipped_by_tally': 0,
    'total_rankings_stalled_after_winner': 0,
    'total_rankings_stalled_after_runner_up': 0,
    'total_rankings_tallied': 0,
    'total_ballots_with_rankings_skipped_by_tally': 0,
    'total_ballots_with_rankings_stalled_after_winner': 0,
    'total_ballots_with_rankings_stalled_after_runner_up': 0,
    'total_ballots_with_fav_eliminated_and_second_not_tallied': 0,
    'total_ballots_with_elimination_and_next_not_tallied': 0,

    'total_rankings_tallied_1': 0,
    'total_rankings_tallied_2': 0,
    'total_rankings_tallied_3': 0,
    'total_rankings_tallied_4': 0,
    'total_rankings_tallied_5': 0,
    'total_rankings_tallied_6': 0,

    'total_rankings_used_1': 0,
    'total_rankings_used_2': 0,
    'total_rankings_used_3': 0,
    'total_rankings_used_4': 0,
    'total_rankings_used_5': 0,
    'total_rankings_used_6': 0,

    # These are set based on rcv cruncher
    'n_candidates': '',
    'rank_limit': '',
    'come_from_behind': '',
    'restrictive_rank_limit': '',
    'first_round_overvote': '',
    'ranked_single': '',
    'ranked_3_or_more': '',
    'ranked_multiple': '',
    'includes_duplicate_ranking': '',
    'includes_overvote_ranking': '',
    'includes_skipped_ranking': '',
    'total_irregular': '',
    'total_undervote': '',
    'total_ballots': '',
    'condorcet': '',
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

def add_overrides():
    # add overrides
    with open('ops/election_stats/overrides.json', 'r') as f:
        overrides = json.load(f)
        for election, row in overrides.items():
            if not set(row.keys()).issubset(set(data[election].keys())):
                raise Exception(f'{row.keys()} contains invalid entries')

            row['election'] = election
            data[election].update(row)


def parse_election_stats(file_names, verbose):
    add_overrides() # adding overrides first since the fields are mutually exclusive, and I want to catch errors quick
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
                 exhaust_on_duplicate_candidate_marks=True,
                 exhaust_on_overvote_marks=True,
                 # exhaust_on_N_repeated_skipped_marks=2,
            )

            stats = election.get_stats()[0].to_dict()
            stats = {k:v[0] for k,v in stats.items()}

            # Compute competitive ratio & min_elimination_margin
            rounds = election.get_round_by_round_dict()

            mm = 999999 # I can't use min_elimination_margin for some reason?
            # I can't use round since that conflicts with the python function
            for _round in rounds['results']:
                elect_sum = sum(int(_round['tally'][r['elected']]) for r in _round['tallyResults'] if 'elected' in r)
                # added .get(,0) since TakomaPark_11082022_CityCouncilWard5 has writein being eliminated with 0 votes
                elim_sum = sum(int(_round['tally'].get(r['eliminated'], 0)) for r in _round['tallyResults'] if 'eliminated' in r)
                eliminated_candidates = [r['eliminated'] for r in _round['tallyResults'] if 'eliminated' in r]
                if _round['round'] == len(rounds['results']):
                    mm = min(mm, elect_sum-elim_sum)
                else:
                    lowest_remaining_tally = 999999999999
                    for (candidate, tally) in _round['tally'].items():
                        if candidate in eliminated_candidates:
                            continue
                        if int(tally) < lowest_remaining_tally:
                            lowest_remaining_tally = int(tally)
                    mm = min(mm, lowest_remaining_tally-elim_sum)

            if len(rounds['results']) < 2:
                competitive_ratio = 0
            else:
                # TODO: I probably shouldn't assume that the elected will be first
                winner = rounds['results'][-1]['tallyResults'][0]['elected'] 
                # using -1 because some elections have rounds where multiple candidates are eliminated and we want to use the strongest candidate among those
                bronze = rounds['results'][-2]['tallyResults'][-1]['eliminated']
                top3_tally = rounds['results'][-2]['tally']
                competitive_ratio = int(top3_tally[bronze])/int(top3_tally[winner])

            # Generate row
            data[election_name].update({
                'election': election_name,
                'competitive_ratio': competitive_ratio,
                'min_elimination_margin': mm,

                'n_candidates': stats['n_candidates'],
                'come_from_behind': stats['come_from_behind'],
                'rank_limit': stats['rank_limit'],
                'restrictive_rank_limit': stats['restrictive_rank_limit'],
                'first_round_overvote': stats['first_round_overvote'],
                'ranked_single': stats['ranked_single'],
                'ranked_3_or_more': stats['ranked_3_or_more'],
                'ranked_multiple': stats['ranked_multiple'],
                'total_undervote': stats['total_undervote'],
                'total_ballots': stats['total_ballots'],
                'total_fully_ranked': stats['total_fully_ranked'],
                'mean_rankings_used': stats['mean_rankings_used'],
                'winner': stats['winner'],
                'condorcet': stats['condorcet'],
                'n_rounds': stats['n_rounds'],
                'includes_duplicate_ranking': stats['includes_duplicate_ranking'],
                'includes_overvote_ranking': stats['includes_overvote_ranking'],
                'includes_skipped_ranking': stats['includes_skipped_ranking'],
                'total_irregular': stats['total_irregular'],
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

            # Loop over ballots
            data[election_name]['total_rankings_used'] = data[election_name]['mean_rankings_used'] * data[election_name]['total_ballots']
            cvr = CastVoteRecord(
                parser_func=rank_column_csv,
                parser_args={'cvr_path': cvr_file},
            )
            df = cvr.get_cvr_table();

            elim_order = []
            for results in reversed(rounds['results']):
                for op in results['tallyResults']:
                    elim_order.append(op['eliminated'] if 'eliminated' in op else op['elected'])

            num_finalists = len(rounds['results'][-1]['tallyResults'])


            def parse_ballot(b):
                e_stack = copy(elim_order)
                l = b.to_list()[b.index.get_loc('rank1'):]
                rankings_used = len([x for x in l if x != 'skipped'])
                for i in range(len(l)):
                    # anything after overvote should be skipped
                    if l[i] == 'overvote':
                        for j in range(i, len(l)):
                            l[j] = 'skipped'
                    # duplicate rankings should be skipped
                    if i != l.index(l[i]):
                        l[i] = 'skipped'

                b_stack = [c for c in list(reversed(l)) if c != 'skipped']

                rankings_skipped_by_tally = 0
                rankings_tallied = 1 if len(b_stack) > 0 else 0 
                rankings_tallied_list = [0]*12 # using a large number to avoid index issues, but we don't actually use all of them

                if(len(b_stack) > 0):
                    rankings_tallied_list[int(b[b == b_stack[-1]].index.tolist()[0].replace('rank',''))] = 1

                first_ballot_elimination_completed = False
                fav_eliminated_and_second_not_tallied = False
                # repeat tally until all eliminated candidates have been processed, or the ballot is exhasuted
                while len(e_stack) > num_finalists and len(b_stack) > 0:
                    e_stack.pop()
                    # if top candidate is still in the running, continue
                    if b_stack[-1] in e_stack:
                        continue
                    # ballot's top candidate is no longer in the stack
                    b_stack.pop()

                    # skip rankings
                    while len(b_stack) > 0 and b_stack[-1] not in e_stack:
                        if not first_ballot_elimination_completed:  
                            fav_eliminated_and_second_not_tallied = True
                        b_stack.pop()
                        rankings_skipped_by_tally = rankings_skipped_by_tally + 1
                    if len(b_stack) > 0 and b_stack[-1] in e_stack:
                        rankings_tallied = rankings_tallied + 1
                        rankings_tallied_list[int(b[b == b_stack[-1]].index.tolist()[0].replace('rank',''))] = 1

                    first_ballot_elimination_completed = True
                
                stall_after_winner = len(b_stack)-1 if len(b_stack) > 0 and b_stack[-1] == stats['winner'] else 0
                stall_after_runner_up =len(b_stack)-1 if len(b_stack) > 0 and b_stack[-1] != stats['winner'] else 0

                if not first_ballot_elimination_completed and stall_after_runner_up > 0 and len(b_stack) == rankings_used:
                    fav_eliminated_and_second_not_tallied = True

                return {
                    'rankings_used': rankings_used,
                    'rankings_skipped_by_tally': rankings_skipped_by_tally,
                    'rankings_stalled_after_winner': stall_after_winner,
                    'rankings_stalled_after_runner_up': stall_after_runner_up,
                    'rankings_tallied': rankings_tallied,

                    'rankings_used_1': b['rank1'] != 'skipped' if 'rank1' in b else 0,
                    'rankings_used_2': b['rank2'] != 'skipped' if 'rank2' in b else 0,
                    'rankings_used_3': b['rank3'] != 'skipped' if 'rank3' in b else 0,
                    'rankings_used_4': b['rank4'] != 'skipped' if 'rank4' in b else 0,
                    'rankings_used_5': b['rank5'] != 'skipped' if 'rank5' in b else 0,
                    'rankings_used_6': b['rank6'] != 'skipped' if 'rank6' in b else 0,

                    'rankings_tallied_1': rankings_tallied_list[1],
                    'rankings_tallied_2': rankings_tallied_list[2],
                    'rankings_tallied_3': rankings_tallied_list[3],
                    'rankings_tallied_4': rankings_tallied_list[4],
                    'rankings_tallied_5': rankings_tallied_list[5],
                    'rankings_tallied_6': rankings_tallied_list[6],

                    'has_rankings_skipped_by_tally': rankings_skipped_by_tally > 0,
                    'has_rankings_stalled_after_winner': stall_after_winner > 0,
                    'has_rankings_stalled_after_runner_up': stall_after_runner_up > 0,

                    'has_fav_eliminated_and_second_not_tallied': fav_eliminated_and_second_not_tallied,
                    'has_elimination_and_next_not_tallied': rankings_skipped_by_tally > 0 or stall_after_runner_up > 0,
                }

            sum_o = df.apply(parse_ballot, axis='columns', result_type='expand').sum(axis='index') # run operation on all rows and then sum each column
            data[election_name].update({
                # This overrides the previous total_rankings_used which is mean_rankings_used * total_ballots. 
                # We use sum_o since that one includes overvotes
                'total_rankings_used': sum_o['rankings_used'],
                'total_rankings_skipped_by_tally': sum_o['rankings_skipped_by_tally'],
                'total_rankings_stalled_after_winner': sum_o['rankings_stalled_after_winner'],
                'total_rankings_stalled_after_runner_up': sum_o['rankings_stalled_after_runner_up'],
                'total_rankings_tallied': sum_o['rankings_tallied'],

                'total_rankings_used_1': sum_o['rankings_used_1'],
                'total_rankings_used_2': sum_o['rankings_used_2'],
                'total_rankings_used_3': sum_o['rankings_used_3'],
                'total_rankings_used_4': sum_o['rankings_used_4'],
                'total_rankings_used_5': sum_o['rankings_used_5'],
                'total_rankings_used_6': sum_o['rankings_used_6'],

                'total_rankings_tallied_1': sum_o['rankings_tallied_1'],
                'total_rankings_tallied_2': sum_o['rankings_tallied_2'],
                'total_rankings_tallied_3': sum_o['rankings_tallied_3'],
                'total_rankings_tallied_4': sum_o['rankings_tallied_4'],
                'total_rankings_tallied_5': sum_o['rankings_tallied_5'],
                'total_rankings_tallied_6': sum_o['rankings_tallied_6'],

                'total_ballots_with_rankings_skipped_by_tally': sum_o['has_rankings_skipped_by_tally'],
                'total_ballots_with_rankings_stalled_after_winner': sum_o['has_rankings_stalled_after_winner'],
                'total_ballots_with_rankings_stalled_after_runner_up': sum_o['has_rankings_stalled_after_runner_up'],
                'total_ballots_with_fav_eliminated_and_second_not_tallied': sum_o['has_fav_eliminated_and_second_not_tallied'],
                'total_ballots_with_elimination_and_next_not_tallied': sum_o['has_elimination_and_next_not_tallied'],
            })

            # print(sum_o['rankings_tallied'], '/', sum_o['rankings_used'], ' = ', sum_o['rankings_tallied']/sum_o['rankings_used'])
            # for j in range(1,7):
            #     i = str(j)
            #     print(i, ': ', sum_o['rankings_tallied_'+i], '/', sum_o['rankings_used_'+i], ' = ', sum_o['rankings_tallied_'+i]/sum_o['rankings_used_'+i])

            log(f'{round(time.time()-start)}s')

        except Exception as e:
            log('ERROR')
            if verbose:
                log(traceback.format_exc())

    return data;


