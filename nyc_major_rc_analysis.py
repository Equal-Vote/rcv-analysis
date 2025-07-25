import pandas as pd
import numpy as np
import os
import re

def convert_to_one_big_csv(folder_location):
    
    folder = folder_location
    os.chdir(folder)
    os.makedirs('output', exist_ok=True)

    files_list = [f for f in os.listdir() if f.lower().endswith('.xlsx')]

    # This file name will need to be updated for 2025
    candidates_file_name = 'Primary Election 2025 - 06-24-2025_CandidacyID_To_Name.xlsx'
    # candidates_file_name = '2021P_CandidacyID_To_Name.xlsx'
    candidate_ids = pd.read_excel(candidates_file_name)
    if candidates_file_name in files_list:
        files_list.remove(candidates_file_name)

    candidate_ids.to_csv('output/2021P_CandidacyID_To_Name.csv')
    print("Candidate IDs as 'output/2021P_CandidacyID_To_Name.csv'")

    required_columns = [
        'Cast Vote Record',
        'Precinct',
        # 'DEM Mayor Choice 1 of 5 Citywide (024306)',
        # 'DEM Mayor Choice 2 of 5 Citywide (224306)',
        # 'DEM Mayor Choice 3 of 5 Citywide (324306)',
        # 'DEM Mayor Choice 4 of 5 Citywide (424306)',
        # 'DEM Mayor Choice 5 of 5 Citywide (524306)'
        'DEM Mayor Choice 1 of 5 Citywide (026916)',
        'DEM Mayor Choice 2 of 5 Citywide (226916)',
        'DEM Mayor Choice 3 of 5 Citywide (326916)',
        'DEM Mayor Choice 4 of 5 Citywide (426916)',
        'DEM Mayor Choice 5 of 5 Citywide (526916)'
    ]

    combined = []

    for file in files_list:
        try:
            df = pd.read_excel(file, usecols=required_columns)
            df['Source_File'] = file
            combined.append(df)
            print(f"Processed: {file}")
        except Exception as e:
            print(f"Skipped {file}: {e}")

    result = pd.concat(combined, ignore_index=True)

    # Double check that the column names are the same for the 2025 election
    result.rename(columns={
        # 'DEM Mayor Choice 1 of 5 Citywide (024306)':'Choice 1',
        # 'DEM Mayor Choice 2 of 5 Citywide (224306)':'Choice 2',
        # 'DEM Mayor Choice 3 of 5 Citywide (324306)':'Choice 3',
        # 'DEM Mayor Choice 4 of 5 Citywide (424306)':'Choice 4',
        # 'DEM Mayor Choice 5 of 5 Citywide (524306)':'Choice 5'

        'DEM Mayor Choice 1 of 5 Citywide (026916)':'Choice 1',
        'DEM Mayor Choice 2 of 5 Citywide (226916)':'Choice 2',
        'DEM Mayor Choice 3 of 5 Citywide (326916)':'Choice 3',
        'DEM Mayor Choice 4 of 5 Citywide (426916)':'Choice 4',
        'DEM Mayor Choice 5 of 5 Citywide (526916)':'Choice 5'
    },inplace=True)

    result.to_csv('output/NYC_Mayor_RC_Data.csv', index=False)
    print("Combined CSV saved as 'output/NYC_Mayor_RC_Data.csv'")


def nyc_mayoral_analysis(candidate1,candidate2,candidate3,folder_location):
    os.chdir(folder_location)
    
    df = pd.read_csv('output/NYC_Mayor_RC_Data.csv')
    candidate_ids = pd.read_csv('output/2021P_CandidacyID_To_Name.csv')  

    target_names = {
        candidate1: None,
        candidate2: None,
        candidate3: None
    }

    candidate_ids['DefaultBallotName'] = candidate_ids['DefaultBallotName'].astype(str)

    for target in target_names:
        parts = target.strip().split()
        first = parts[0]
        last = parts[-1]

        pattern = rf'\b{first}\b.*\b{last}\b' 
        match = candidate_ids[candidate_ids['DefaultBallotName'].str.contains(pattern, flags=re.IGNORECASE, regex=True)]

        if not match.empty:
            found_id = str(match.iloc[0]['CandidacyID'])
            print(f"Found match for '{target}': ID = {found_id}, Name = {match.iloc[0]['DefaultBallotName']}")
            target_names[target] = found_id
        else:
            print(f"No match found for '{target}'.")


    id_to_name = {v: k.split()[1] for k, v in target_names.items() if v is not None}
    main_ids = list(id_to_name.keys())

    # If the regex above isn't working, adjust these to the correct politicians Ids and Names
    # id_to_name = {
    #     '219978': 'Garcia',
    #     '219469': 'Wiley',
    #     '217572': 'Adams'
    # }

    main_ids = list(id_to_name.keys())
    choice_cols = ['Choice 1', 'Choice 2', 'Choice 3', 'Choice 4', 'Choice 5']

    filtered_df = df[df[choice_cols].apply(lambda row: any(str(val) in main_ids for val in row), axis=1)]

    def extract_top_two(row):
        seen = []
        for c in row[choice_cols]:
            c_str = str(c)
            if c_str in main_ids and c_str not in seen:
                seen.append(c_str)
            if len(seen) == 2:
                break
        return tuple(seen)

    filtered_df.loc[:, 'top_two'] = filtered_df.apply(extract_top_two, axis=1)
    top_two_counts = filtered_df['top_two'].value_counts()

    columns = []
    counts = []
    first_choices = []
    second_choices = []
    third_choices = []

    for top_two, count in top_two_counts.items():
        names = [id_to_name.get(str(c), '') for c in top_two]
        third = [id_to_name[k] for k in main_ids if k not in top_two]
        columns.append(' > '.join(names))  
        counts.append(count)
        first_choices.append(names[0] if len(names) > 0 else '')
        second_choices.append(names[1] if len(names) > 1 else '')
        third_choices.append(third[0] if len(third) == 1 else '')

    output_df = pd.DataFrame(
        [counts, first_choices, second_choices, third_choices],
        index=['Num. Voters', '1st choice', '2nd choice', '3rd (implied)'],
        columns=columns
    )

    output_df.to_csv('output/NYC_Majoral_RC_Results.csv')

    print(output_df)

def main():
    print("Starting STAR voting analysis...")
    # Adjust this to your file location with the excel files
    folder_location = r'C:\w\rcv-analysis\2025_Primary_CVR_2025-07-17'
    # convert_to_one_big_csv(folder_location)

    # Run this for the 2025 election
    nyc_mayoral_analysis('Zohran Mamdani','Andrew Cuomo','Brad Lander',folder_location)

    # Currently setup for the 2021 election
    # nyc_mayoral_analysis('Eric Adams','Maya Wiley','Kathryn Garcia',folder_location)



if __name__ == "__main__":
    main()


# Things that need to be fixed for the new election
# - Update file name: "2021P_CandidacyID_To_Name"
# - Check column names: 'DEM Mayor Choice 1 of 5 Citywide (024306)'
# - Cross your fingers that the regex works (otherwise manually put in candidate ids)
