import pandas as pd
from copy import copy
from collections import defaultdict
import time

from util import *

columns = {
    ' !!Total:' : 'Precinct Pop.',
    ' !!Total:!!Hispanic or Latino': 'Hispanic',
    ' !!Total:!!Not Hispanic or Latino:!!Population of one race:!!White alone': 'White',
    ' !!Total:!!Not Hispanic or Latino:!!Population of one race:!!Black or African American alone': 'Black or African American',
    ' !!Total:!!Not Hispanic or Latino:!!Population of one race:!!American Indian and Alaska Native alone': 'American Indian and Alaska Native',
    ' !!Total:!!Not Hispanic or Latino:!!Population of one race:!!Asian alone': 'Asian',
    ' !!Total:!!Not Hispanic or Latino:!!Population of one race:!!Native Hawaiian and Other Pacific Islander alone': 'Native Hawaiian and Other Pacific Islander',
    ' !!Total:!!Not Hispanic or Latino:!!Population of one race:!!Some Other Race alone': 'Some Other Race',
    ' !!Total:!!Not Hispanic or Latino:!!Population of two or more races:': 'Two or more races',
}


def parse_block_to_precinct(block_file, mapper_file, output_file):
    # load census block data
    types = defaultdict(lambda: 'float')
    types['Geography'] = 'string'
    types['Geographic Area Name'] = 'string'
    blocks = pd.read_csv(block_file, index_col='Geography', dtype=types, header=1)[columns.keys()].rename(columns=columns)

    # load block to precinct mapper
    types = defaultdict(lambda: 'float')
    mapper = pd.read_csv(mapper_file, dtype={'block': 'string', 'mprec': 'string'})
    mapper = mapper.dropna(subset=['mprec'])

    # init precincts
    precincts = pd.DataFrame(columns=columns.values(), index=mapper.mprec.unique())

    for p in precincts:
        precincts[p].values[:]  = 0

    start = time.time()
    i = 0
    for b, _ in blocks.iterrows():
        i = i + 1
        if i%1000 == 0:
            log(i, time.time()-start)

        # an attempt to remove the loop, but it actually ran slower 😭
        #m = mapper.loc[mapper['block'] == b.split('US')[1]]
        #pct_block = pd.DataFrame(m['pct_block'])
        #pct_block.columns=['block']
        #pct_block.index=m['mprec']
        #block_demo = pd.DataFrame(blocks.loc[b]).T
        #block_demo.index=['block']
        #precincts.loc[m['mprec']] += pct_block.dot(block_demo)

        # same as above, but the above version is 40% faster
        for _, row in mapper.loc[mapper['block'] == b.split('US')[1]].iterrows():
            precincts.loc[row['mprec']] += blocks.loc[b].mul(row['pct_block'])
    
    precincts.to_csv(output_file, index_label='precinct')

