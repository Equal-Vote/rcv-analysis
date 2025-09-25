# Overview
This is a script that'll run rcv cruncher on all the elections you have in the `cvr` folder, and summarize the results in a csv file (assuming you specify an output file, otherwise it'll output a json blob to the console).

You can find descriptions of most of the stats [here](https://rcv-cruncher.readthedocs.io/en/latest/statistics.html).

Here's additional fields that this computes:
Here's some fields that were derived from the rcv-cruncher output:
 * **competitive_ratio**: This is defined as the ratio in first place votes between the 3rd place candidate and the 1st place candidate. It's useful for comparing to results from [this paper](https://www.researchgate.net/publication/258164743_Frequency_of_monotonicity_failure_under_Instant_Runoff_Voting_Estimates_based_on_a_spatial_model_of_elections)
 * **min_elimination_margin**: Smallest margin between the eliminated candidate and the next lowest candidate across all the elimination rounds. This helps guage how close the election is for auditing purposes. So if min_elimination margin is 10, then the elimination order (and potentially the winner) could change if just 5 votes flipped. 

 And some more fields that didn't rely on rcv-cruncher:
 * **total_rankings_skipped_by_tally**: Total rankings that were skipped during tally due to candidates already being eliminated. 
 * **total_rankings_stalled_after_winner**: Total rankings that were left over at the end of the tally where the ballot was allocated to the winner. These untallied rankings are respecting the voters intent per later-no-harm. 
 * **total_rankings_stalled_after_runner_up**: Total rankings that were left over at the end of the tally where the ballot was not allocated to the winner. These untallied rankings are NOT respecting the voters intent.
 * **total_rankings_used**: Total rankings used by the voters. NOTE: Previously this was a derived field from ``mean_rankings_used * total_ballots`` using outputs from rcv-cruncher, but this was updated since mean_rankings_used tends to be lower due to duplicate ranks counting as 1 ranking.
 * **total_rankings_tallied**: Total rankings tallied during the elimination rounds.
 * **total_ballots_with_rankings_skipped_by_tally**: Total ballots which had at least one of the rankings skipped during the tally.
 * **total_ballots_with_rankings_stalled_after_winner**: Total ballots which had at least one of the rankings skipped during the tally.
 * **total_ballots_with_rankings_stalled_after_runner_up**: (self exaplanatory)
 * **total_ballots_with_fav_eliminated_and_second_not_tallied**: (self exaplanatory)
 * **total_ballots_with_elimination_and_next_not_tallied**: (self exaplanatory)

# Setup

This project assumes you download CVRs from [here](https://dataverse.harvard.edu/dataverse/rcv_cvrs) and put them in a folder called `cvr` (I have Moab 2021 committed to the repo as an example)

# Loading Demographic Data

https://data.census.gov/table?g=050XX00US06001$1000000&y=2020
https://statewidedatabase.org/d20/g22_geo_conv.html
https://mapshaper.org/
https://data.acgov.org/datasets/5c2a208663ec40d8aa18bfe65ed3a32f_0/explore?location=37.679110%2C-121.907993%2C10.75
https://data.acgov.org/datasets/3d3205bb21904c3db4f8597e1c55cc5e_0/explore?location=37.805475%2C-121.657363%2C9.87


# Outputs

Here's information for each of the output files (the date corresponds to the date the CVRs were imported from Dataverse, not the date the simulation was ran).

The outputs have also been posted as a [Google spreadsheet](https://docs.google.com/spreadsheets/d/1iMa8Gw6-7Nu06JMKAstaMd7U3GwrCSUn3hfHoepCUAw/edit?usp=sharing)

## 2023-10-25

I collected all the [single](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/AMK8PJ) and [sequential](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/04LOQX) IRV datafiles and ran single-winner IRV on all of them.

There were 455 elections in the dataset, however several files were bugged, and I added Aspen manually. My final spreadsheet had 448 entries (so it seems like there's 2 other elections that I'm missing, not sure where those went)

Bugged Files
* Vineyard_11052019_CityCouncil_tab1.csv
* Vineyard_11052019_CityCouncil_tab2.csv
* Easthampton_11022021_Mayor.csv
* Payson_11052019_CityCouncil_tab1.csv
* Payson_11052019_CityCouncil_tab2.csv
* Payson_11052019_CityCouncil_tab3.csv

It assumed the following settings. Individual elections require different settings, but these will hopefully be close enough for a starting point:

```
     exhaust_on_duplicate_candidate_marks=False,
     exhaust_on_overvote_marks=True,
     exhaust_on_N_repeated_skipped_marks=0
```

This dataset also specifes a number of overrides for fields that aren't computed by rcv_cruncher. The overrides also include the Aspen election. This election was said to use STV, but the specific algorithm they used was closer to block-IRV, so I felt it was fair to include it here.

## 2025-06-12

Added outputs for 2022 Oakland Mayor Election, and District School Board

These CSVs show precinct level stats, along with the precinct level census data

```
python cruncher.py precinct-stats -o output.csv
```

Afterward kmls were generated in order to visualize the precincts on google maps

```
python cruncher.py precincts-to-kml -r -o output2.kml -p outputs/2025-04-18-oakland-mayor-2022-precincts.csv
```

## 2025-09-20

Generated some statistics for the purposes of the LA Charter Presentation:

 * NYC 2025 Mayor Primary: 33% of rankings were used
 * Alaska 2022 US House Special Election: 57% of rankings were used
 * Redondo Beach 2025 Mayor Election: 38% of rankings were used

I ran the following, and then did ``total_rankings_tallied / total_rankings_used`` to determine how many rankings were processed during the tally (see variable definitions above).

```
python cruncher.py election-stats -o output.csv
```

The output is available at outputs/2025-09-20-all-elections.csv

# Future work

The FairVote RCV Cruncher tool was very helpful and gave us 99% of the data we needed.

The only other bit I'd like to include is an investigation of skipped and stalled ranks. These are situations where ranks are either skipped because the candidate was already eliminated, or stalled because the ballot had already been allocated toward one of the finalists. It would be super interesting to know what percent of ranks are counted, skipped, or stalled overall, and also know the average number of these ranks per ballot.

I'd also like to make the tool a bit easier to use. Right now it runs for an hour+ and it would be great if it could pick up where it left off if it bugged halfway through.
