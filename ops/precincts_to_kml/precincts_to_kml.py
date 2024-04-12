import csv
import random
import json
import re

import xmltodict


def pre(mark):
    if 'Data' in mark['ExtendedData']:
        return [d['value'] for d in mark['ExtendedData']['Data'] if d['@name'] == 'Precinct_ID'][0]
    else:
        return [d['#text'] for d in mark['ExtendedData']['SchemaData']['SimpleData'] if d['@name'] == 'Precinct_ID'][0]


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
            'a': toNum(h[:2]),
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
    'White': [ 'ffe2ecfe', 'ffb8b2ff'],
    'Black or African American': [ 'ffd9e5fd', 'ff91aff9'],
    'American Indian and Alaska Native': [ 'fff7f7f7', 'ffcccccc'],
    'Asian': [ 'ffe8f8ed', 'ffafe7b6'],
    'Hispanic': [ 'fffff3ef', 'ffe4d7be'],
    # these colors were defined in my reference graphic, I'll add them as needed
    'Native Hawaiian and Other Pacific Islander': [ 'ff000000', 'ffffffff'],
    'Some Other Race': [ 'ff000000', 'ffffffff'],
    'Two or more races':[ 'ff000000', 'ffffffff']
}


def apply_data_to_kml(precincts, key, max_value, apply_race_colors, kml):
    max_height = 5000;

    # Removing any precincts that don't line up with the data (I should probably clean this up)
    if 'Folder' in kml['kml']['Document']:
        root = kml['kml']['Document']['Folder']
    else:
        root = kml['kml']['Document']

    root['Placemark'] = [mark for mark in root['Placemark'] if pre(mark) in precincts]

    for mark in root['Placemark']:
        if 'Polygon' not in mark:
            continue
        error = (float(precincts[pre(mark)][key]) / float(precincts[pre(mark)]['total_ballots'])) / max_value
        # Add label
        appendData(mark, f'{key.replace('total_', '')}_percent', f'{round(error*100, 2)}%')
        # Style
        if apply_race_colors:
            race = sorted(list(RACE_COLORS.keys()), key=lambda race: float(precincts[pre(mark)][race]))[-1]

            t = float(precincts[pre(mark)][race]) / float(precincts[pre(mark)]['Precinct Pop.'])
            t = (t - .3) / (.5 - .3)# inv lerp 30% - 50%

            color = lerpColor(RACE_COLORS[race][0], RACE_COLORS[race][1], t)
        else:
            f = min(max_value,error)/max_value
            color = lerpColor('ffffffff', 'ff0000ff', f)
        mark['Style'] = {
            'LineStyle': {
                'color': color
            },
            'PolyStyle': {
                'color': color
            },
        }
        # Enable extrusion
        mark['Polygon']['extrude'] = '1'
        mark['Polygon']['altitudeMode'] = 'relativeToGround'
        # Update coordindates
        ring = mark['Polygon']['outerBoundaryIs']['LinearRing']
        ring['coordinates'] = ' '.join([f'{c},{max_height * error}' for c in re.split(r'\\n|\s', ring['coordinates'])])


def precincts_to_kml(precincts_file, output_file, z_axis, apply_race_colors):
    # load base kml
    with open('ops/precincts_to_kml/kml/alameda_2022.kml') as f:
        text = f.read()
    kml = xmltodict.parse(text)

    # load precincts file
    precincts = {}
    with open(precincts_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            precincts[row['precinct']] = row
    
    # modify
    m = apply_data_to_kml(precincts, z_axis or 'total_irregular', .5, apply_race_colors, kml)

    # write kml
    with open(output_file, 'w') as f:
        f.write(xmltodict.unparse(kml))
