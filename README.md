# Overview
This is a script that'll run rcv cruncher and all the electiosn you have in the cvr folder, and summarize the results in a csv file

You can find descriptions of most of the stats [here](https://rcv-cruncher.readthedocs.io/en/latest/statistics.html)

Here's additional fields that this computes
 * **competitive_ratio**: This is defined as the ratio in first place votes between the 3rd place candidate and the 1st place candidate. It's useful for comparing to results from [this paper](https://www.researchgate.net/publication/258164743_Frequency_of_monotonicity_failure_under_Instant_Runoff_Voting_Estimates_based_on_a_spatial_model_of_elections)

# Setup

This project assumes you download cvrs from [here](https://dataverse.harvard.edu/dataverse/rcv_cvrs) and put them in a folder called cvr (I have moab committed to the repo as an example)

# Outputs

Here's information for each of the output files (the date corresponds to the date the CVRs were imported from dataverse, not the date the simulation was ran)

The outputs can also been posted as a [google spreadsheet](https://docs.google.com/spreadsheets/d/1iMa8Gw6-7Nu06JMKAstaMd7U3GwrCSUn3hfHoepCUAw/edit?usp=sharing)

## 10-25-2023

This was ran on all the single and sequential irv datafiles and ran single winner irv on all of them

There were 455 elections in the dataset, however Easthampton_11022021_Mayor, and Payson_Citycouncil 1-3 were bugged, and I added Aspen manually, so the final number was still 452

It assumed the following settings, individual elections require different settings, but these will hopefully be close enough for a starting point


```
     exhaust_on_duplicate_candidate_marks=False,
     exhaust_on_overvote_marks=True,
     exhaust_on_N_repeated_skipped_marks=0
```

This dataset also specifes a number of overrides for fields that aren't computed by rcv cruncher. The overrides also include the Aspen election. This election was said to use STV, but the specific algorithm they used was closer to block-IRV, so I felt it was fair to include it here

# Future work

The FairVote RCV Cruncher tool was very helpful and gave us 99% of the data we needed. The only other bit I'd like to include is number of stalled or untransferred votes. These are the number of 
