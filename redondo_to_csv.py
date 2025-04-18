import xml.etree.ElementTree as ET
import os
import xmltodict
import json

MAYOR_CONTEST = 'For MAYOR:'

def contenstsOnBallot(ballot):
    return [o['ns0:Name'] for o in ballot['ns0:Cvr']['ns0:Contests']['ns0:Contest']]

def getContestFromBallot(ballot, contest):
    return [o for o in ballot['ns0:Cvr']['ns0:Contests']['ns0:Contest'] if o['ns0:Name'] == contest][0]

# Note, ballots is just the unzipped folder in the citywide directory
folder = 'RedondoRaw/citywide/Ballots'

files = os.listdir(folder)

files = [f'{folder}/{f}' for f in files if '.xml.sig' not in f and 'WriteIn' not in f]


print(','.join(['index'] + [f'rank{i+1}' for i in range(6)]))

for j,file in enumerate(files):
# for j in [1105, 2358, 2442, 3749, 5756, 5872, 10984]:
#     file = files[j]
    # XML -> Dict
    tree = ET.parse(file)
    xml_data = tree.getroot()
    xml_str = ET.tostring(xml_data, encoding='utf-8', method='xml')
    obj = dict(xmltodict.parse(xml_str))


    # init row
    row = [str(j)] + ['skipped'] * 6

    ballot = getContestFromBallot(obj, MAYOR_CONTEST)

    print(json.dumps(ballot, indent=4))

    if ballot['ns0:Options'] is not None:
        options = ballot['ns0:Options']['ns0:Option']
        if not isinstance(options, list):
            options = [options]
        for option in options:
            name = option['ns0:Name'] if 'ns0:Name' in option else 'writein'
            for i,v in enumerate(option['ns0:Value']):
                if v != '1':
                   continue
                if row[i+1] == 'skipped':
                    row[i+1] = name
                else:
                    row[i+1] = 'overvote'

    print(','.join(row))

# with open(files[0], 'r') as f:
#     data = f.read()
#     print(data)
#     obj = xmltodict.parse(data)
#     print(json.dumps(obj, indent=4))
