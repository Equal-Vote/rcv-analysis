import json
from collections import defaultdict

CANDIDATES = {
    '215': 'BEGICH',
    '151': 'BEGICH',
    '217': 'PALIN',
    '169': 'PALIN',
    '218': 'PELTOLA',
    '171': 'PELTOLA',
}

CHOOSE_ONE = 6
RCV = 69

data = defaultdict( lambda: {
    'BallotId': '',
    'ChooseOne': [],
    'Rank1': [],
    'Rank2': [],
    'Rank3': [],
    'Rank4': [],
    'ChooseOneRank': '',
    'MaxRank': '',
    'ChooseOneWasFirst': '',
    'ChooseOneWasLast': '',
    'ChooseOneOvervote': '',
    'SkippedRank': '',
    'DuplicateRank': '',
    'Overvote': '',
})

# Note, at the moment this is hard coded for Alaska
def parse_session(s):
    id = f'{s['TabulatorId']}_{s['BatchId']}_{s['RecordId']}'
    if id in data:
        print(s)
    d = data[id]
    if len(s['Original']['Cards']) > 1:
        raise Exception('more than 1 card')
    for c in s['Original']['Cards'][0]['Contests']:
        if c['Id'] == CHOOSE_ONE:
            for m in c['Marks']:
                d['ChooseOne'].append(CANDIDATES.get(str(m['CandidateId']), 'OTHER'))

        if c['Id'] == RCV:
            for m in c['Marks']:
                d[f'Rank{m['Rank']}'].append(CANDIDATES.get(str(m['CandidateId']), 'OTHER'))


    def maxRank(d):
        if len(d['Rank4']) > 0:
            return 4
        if len(d['Rank3']) > 0:
            return 3
        if len(d['Rank2']) > 0:
            return 2
        if len(d['Rank1']) > 0:
            return 1
        return 0
    
    def chooseOneRank(d):
        if len(d['ChooseOne']) != 1:
            return 0
        if d['ChooseOne'][0] in d['Rank1']: 
            return 1
        if d['ChooseOne'][0] in d['Rank2']: 
            return 2
        if d['ChooseOne'][0] in d['Rank3']: 
            return 3
        if d['ChooseOne'][0] in d['Rank4']: 
            return 4
        return 0

    r = chooseOneRank(d)
    d.update({
        'BallotId': id,
        'ChooseOneOvervote': len(d['ChooseOne']) > 1,
        'Overvote': any(len(d[f'Rank{i}']) > 1 for i in range(1, 5)),
        'SkippedRank': any(len(d[f'Rank{i}']) > 0 and len(d[f'Rank{i-1}']) == 0 for i in range(2, 5)),
        'DuplicateRank': len(set(d['Rank1']) | set(d['Rank2']) | set(d['Rank3']) | set(d['Rank4'])) != len(d['Rank1'] + d['Rank2'] + d['Rank3'] + d['Rank4']),
        'MaxRank': maxRank(d),
        'ChooseOneRank': r,
        'ChooseOneWasFirst': True if r > 0 and (r == 1 or all(len(d[f'Rank{i}']) == 0 for i in range(r-1, 0, -1))) else False,
    }) 

    d['ChooseOne'] = 'skip' if len(d['ChooseOne']) == 0 else ' | '.join(d['ChooseOne'])
    d['Rank1'] = 'skip' if len(d['Rank1']) == 0 else ' | '.join(d['Rank1'])
    d['Rank2'] = 'skip' if len(d['Rank2']) == 0 else ' | '.join(d['Rank2'])
    d['Rank3'] = 'skip' if len(d['Rank3']) == 0 else ' | '.join(d['Rank3'])
    d['Rank4'] = 'skip' if len(d['Rank4']) == 0 else ' | '.join(d['Rank4'])

    return d


def parse_cvr(cvr_file):
    with open(cvr_file) as f:
        c = json.load(f)
        for s in c['Sessions']:
            parse_session(s)
    return data

