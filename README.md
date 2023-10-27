# Overview
This is a script that'll run rcv cruncher on all the elections you have in the `cvr` folder, and summarize the results in a csv file (assuming you specify an output file, otherwise it'll output a json blob to the console).

You can find descriptions of most of the stats [here](https://rcv-cruncher.readthedocs.io/en/latest/statistics.html).

Here's additional fields that this computes:
 * **competitive_ratio**: This is defined as the ratio in first place votes between the 3rd place candidate and the 1st place candidate. It's useful for comparing to results from [this paper](https://www.researchgate.net/publication/258164743_Frequency_of_monotonicity_failure_under_Instant_Runoff_Voting_Estimates_based_on_a_spatial_model_of_elections)

# Setup

This project assumes you download CVRs from [here](https://dataverse.harvard.edu/dataverse/rcv_cvrs) and put them in a folder called `cvr` (I have Moab 2021 committed to the repo as an example)

# Outputs

Here's information for each of the output files (the date corresponds to the date the CVRs were imported from Dataverse, not the date the simulation was ran).

The outputs have also been posted as a [Google spreadsheet](https://docs.google.com/spreadsheets/d/1iMa8Gw6-7Nu06JMKAstaMd7U3GwrCSUn3hfHoepCUAw/edit?usp=sharing)

## 10-25-2023

I collected all the [single](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/AMK8PJ) and [sequential](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/04LOQX) IRV datafiles and ran single-winner IRV on all of them.

There were 455 elections in the dataset, however `Easthampton_11022021_Mayor` and `Payson_11052019_CityCouncil` 1-3 were bugged, and I added Aspen manually, so the final number was still 452

It assumed the following settings. Individual elections require different settings, but these will hopefully be close enough for a starting point:

```
     exhaust_on_duplicate_candidate_marks=False,
     exhaust_on_overvote_marks=True,
     exhaust_on_N_repeated_skipped_marks=0
```

This dataset also specifes a number of overrides for fields that aren't computed by rcv_cruncher. The overrides also include the Aspen election. This election was said to use STV, but the specific algorithm they used was closer to block-IRV, so I felt it was fair to include it here.

# Future work

The FairVote RCV Cruncher tool was very helpful and gave us 99% of the data we needed. The only other bit I'd like to include is number of stalled or untransferred votes. These are the number of 
