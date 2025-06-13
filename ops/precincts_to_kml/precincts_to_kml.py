import csv
import random
import json
import re

import xmltodict


def pre(mark):
    p = ''
    if 'Data' in mark['ExtendedData']:
        p = [d['value'] for d in mark['ExtendedData']['Data'] if d['@name'] == 'Precinct_ID'][0]
    else:
        p = [d['#text'] for d in mark['ExtendedData']['SchemaData']['SimpleData'] if d['@name'] == 'Precinct_ID'][0]
    
    if len(p) == 7 and p[0] == '9':
        p = p[1:]

    return p


def appendData(mark, key, value):
    if 'Data' in mark['ExtendedData']:
        mark['ExtendedData']['Data'].append({
            '@name': key,
            'value': value
        })
    else:
        mark['ExtendedData']['SchemaData']['SimpleData'].append({
            '@name': key,
            '#text': value
        })

def lerpColor(a, b='ffffffff', t=0):
    HEX = '0123456789abcdef'

    t = max(0, min(1, t))

    def toNum(h):
        return HEX.rfind(h[0])*16 + HEX.rfind(h[1])

    def toHex(i):
        i = round(i)
        return f'{HEX[i // 16]}{HEX[i % 16]}'

    def parseColor(h):
        return {
            'a': 255, # toNum(h[:2]),
            'b': toNum(h[2:4]),
            'g': toNum(h[4:6]),
            'r': toNum(h[6:]),
        }

    def colorToHex(c):
        return f'{toHex(c['a'])}{toHex(c['b'])}{toHex(c['g'])}{toHex(c['r'])}'
    
    aa = parseColor(a)
    bb = parseColor(b)
    cc = {
        'r': aa['r'] * (1-t) + bb['r'] * t,
        'g': aa['g'] * (1-t) + bb['g'] * t,
        'b': aa['b'] * (1-t) + bb['b'] * t,
        'a': aa['a'] * (1-t) + bb['a'] * t,
    }
    return colorToHex(cc)


RACE_COLORS = {
    'White': ['ff800080', 'ffffffff'], # ['ffffffff', 'ffb3a22a'],
    'Black or African American': [ 'ffffffff', 'ff0099ff'], # [ 'ffa1c8ff', 'ff167dff'],
    'American Indian and Alaska Native': [ 'cceaeaea', 'cccccccc'], 
    'Asian': ['ffffffff', 'ff3cb360'], # [ 'ffe8f8ed', 'ffc6ffcf'],
    'Hispanic': ['ffffffff', 'ff56e1ff'], # [ 'fffff4ce', 'ffffe392'], 
    # these colors weren't defined in my reference graphic, I'll add them as needed
    'Native Hawaiian and Other Pacific Islander': [ 'ff000000', 'ffffffff'],
    'Some Other Race': [ 'ff000000', 'ffffffff'],
    'Two or more races':[ 'ff000000', 'ffffffff']
}

def lerp(a, b, t):
    return a*(1-t) + b*t


def apply_data_to_kml(precincts, key, max_value, apply_race_colors, kml):
    min_height = 200;
    max_height = 5000;

    # Removing any precincts that don't line up with the data (I should probably clean this up)
    if 'Folder' in kml['kml']['Document']:
        root = kml['kml']['Document']['Folder']
    else:
        root = kml['kml']['Document']

    # print('KML original', sorted([pre(mark) for mark in root['Placemark']]))
    root['Placemark'] = [mark for mark in root['Placemark'] if pre(mark) in precincts]

    if len(root['Placemark']) != len(precincts):
        # print()
        # print('KML ', sorted([pre(mark) for mark in root['Placemark']]))
        # print()
        # print('Data', sorted(list(precincts.keys())))
        print('MISSING PRECINCTS:\n', '\n'.join(set(precincts.keys()).difference(set(pre(m) for m in root['Placemark']))) )
        print(f"Warning! KML only has {len(root['Placemark'])} / {len(precincts)} precincts")
        #raise Exception(f"Mismatch! KML only has {len(root['Placemark'])} / {len(precincts)} precincts")

    for mark in root['Placemark']:
        if 'Polygon' not in mark:
            continue

        key_sum = 0
        total_votes = 0
        for item in precincts[pre(mark)]:
            key_sum = key_sum + float(item[key])
            total_votes = total_votes + (float(item['total_ballots']) - float(item['total_undervote']))

        error = key_sum / total_votes

        # Add label
        appendData(mark, f'{key.replace('total_', '')}_percent', f'{round(error*100)}')
        # error = error / max_value
        # Style
        if apply_race_colors:
            # race = sorted(list(RACE_COLORS.keys()), key=lambda race: float(precincts[pre(mark)][0][race]))[-1]
            # race = 'Black or African American'
            # race = 'Hispanic'
            # race = 'Asian'
            race = 'White'

            t = float(precincts[pre(mark)][0][race]) / float(precincts[pre(mark)][0]['Precinct Pop.'])

            mark['name'] = f'{round((1-t)*100)}%'

            # t = (t - .3) / (.5 - .3)# inv lerp 30% - 50%
            t = (t - .0) / (.3 - .0)# inv lerp 00% - 30%
            # t = (t - .2) / (.9 - .2)# inv lerp 20% - 90%
            # t = (t - .2) / (1 - .2)# inv lerp 20% - 100%
            #t = (t - .0) / (.01 - .0)# inv lerp 00% - 1%

            color = lerpColor(RACE_COLORS[race][0], RACE_COLORS[race][1], t)
        else:
            f = min(.22,error)/.22
            color = lerpColor('ccffffff', 'cc0000ff', min(1, f))
            mark['name'] = f'{round(error*100)}%'
        mark['Style'] = {
            'PolyStyle': {
                'color': color,
                'outline': '1'
            },
            'LineStyle': {
                'color': 'ff000000', #lerpColor(color, 'ff000000', .7),
                'width': 3,
                # 'colorMode': 'normal',
                # 'gx:labelVisibility': 1,
            },
            # 'IconStyle': {
            #     'Icon': {
            #         # 'href': 'https://cdn-icons-png.flaticon.com/512/25/25613.png'
            #         'href': 'https://upload.wikimedia.org/wikipedia/commons/c/ca/1x1.png'
            #     }
            # },
            # 'LabelStyle': {
            #     'scale': 2.2
            # }
        }
        # Enable extrusion
        # mark['Polygon']['extrude'] = '0'
        # mark['Polygon']['altitudeMode'] = 'absolute'
        # # Update coordindates
        # ring = mark['Polygon']['outerBoundaryIs']['LinearRing']
        # ring['coordinates'] = ' '.join([f'{c},{lerp(min_height, max_height, error/max_value)}' for c in re.split(r'\\n|\s', ring['coordinates'])])
        # # Add a point
        # # https://stackoverflow.com/questions/43112699/line-label-not-displayed-when-using-region-on-kml-file-for-ge#:~:text=This%20is%20a%20bug%20in,the%20location%20of%20the%20point.
        # a = 0
        # b = 0
        # arr = ring['coordinates'].split(' ')
        # for pair in arr:
        #     p = pair.split(',')
        #     a = a + float(p[0])
        #     b = b + float(p[1])
        # a = a / len(arr)
        # b = b / len(arr)
        # mark['MultiGeometry'] = {
        #     'Polygon': mark['Polygon'],
        #     'Point': {
        #         'extrude': '1',
        #         'altitudeMode': 'absolute',
        #         'coordinates': f'{a},{b},{(lerp(min_height, max_height, error/max_value))-200}'
        #     }
        # }
        # del mark['Polygon']


def precincts_to_kml(precincts_file, output_file, z_axis, apply_race_colors, census_year):
    # load base kml
    with open(f'ops/precincts_to_kml/kml/alameda_{'2022' if census_year == '2020' else '2018'}.kml') as f:
        text = f.read()
    kml = xmltodict.parse(text)

    # load precincts file
    precincts = {}
    with open(precincts_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['precinct'] not in precincts:
                precincts[row['precinct']] = []
            precincts[row['precinct']].append(row)
    
    # modify
    m = apply_data_to_kml(precincts, z_axis or 'total_irregular', .1, apply_race_colors, kml)

    # write kml
    with open(output_file, 'w') as f:
        f.write(xmltodict.unparse(kml))
