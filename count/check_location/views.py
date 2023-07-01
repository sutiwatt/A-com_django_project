import pandas as pd
from django.shortcuts import render

def process_location_inventory(location_inven):
    # Process the location_inven DataFrame
    location_inven.columns = location_inven.iloc[0]
    location_inventory = location_inven[1:]
    
    pattern = r'^05-M[A-M]-1[a-zA-Z0-9]{2}$'
    df_MF = location_inventory[location_inventory['location'].str.match(pattern)]
    
    pattern = r'^05-M[A-B]-2[a-zA-Z0-9]{2}$'
    df_MF_2 = location_inventory[location_inventory['location'].str.match(pattern)]
    
    location_pickface = pd.concat([df_MF, df_MF_2])
    location_pickface = location_pickface.loc[location_pickface['Partner'] == '489-unilever-th']
    location_pickface = location_pickface[['location', 'Item key', 'UPC', 'available qty']]
    location_pickface = location_pickface.groupby(['location', 'Item key', 'UPC'])['available qty'].sum().reset_index()
    
    return location_pickface

def group_data(location_pickface):
    grouped_data = location_pickface.groupby('check').size().reset_index(name='count')
    return grouped_data

def show_location_pickface(request):
    if request.method == 'POST':
        location_inven_file = request.FILES['location_inven_file']
        master_location_file = request.FILES['master_location_file']

        # Read the uploaded files into DataFrames
        location_inven = pd.read_excel(location_inven_file)
        master_location = pd.read_excel(master_location_file)

        location_pickface = process_location_inventory(location_inven)

        # Process the master_location DataFrame
        master_location.columns = master_location.iloc[1]
        master_location = master_location.iloc[2:]
        master_location_final = master_location.copy()
        master_location_final['Description'] = master_location_final['LONG_DESCRIPTION'].str.split(" - ", expand=True)[1]
        master_location_final = master_location_final[['Location_Type', 'Location', 'ACOMM_ITEM_KEY', 'UPC_CODE', 'Description']]
        master_location_final.sort_values(by='Location', inplace=True)
        master_location_final.rename(columns={'ACOMM_ITEM_KEY': 'Item key'}, inplace=True)
        master_location_final.drop_duplicates(subset=['Location', 'Item key'], inplace=True)
        master_location_final = master_location_final.groupby(['Item key', 'UPC_CODE'])['Location'].agg(list).reset_index()
        master_location_final = master_location_final.loc[master_location_final['Item key'] != 'ว่าง']
        master_location_final = master_location_final.sort_values(by='Location')

        # Create a set of unique 'Item key' values from master_location_final
        master_item_keys = set(master_location_final['Item key'])

        # Create an empty list to store the check results
        check_results = []

        # Iterate over the rows of location_pickface DataFrame
        for index, row in location_pickface.iterrows():
            item_key = row['Item key']
            location = row['location']
        
            # Check if 'Item key' exists in master_item_keys
            if item_key in master_item_keys:
                # Get the corresponding 'Location' list from master_location_final
                valid_locations = master_location_final.loc[master_location_final['Item key'] == item_key, 'Location'].values[0]
            
                # Check if 'location' exists in valid_locations
                if location in valid_locations:
                    check_results.append('Correct')
                else:
                    check_results.append('Wrong')
            else:
                check_results.append('Wrong')

        # Add the 'check' column to location_pickface DataFrame
        location_pickface['check'] = check_results
        location_pickface_1 = location_pickface.loc[location_pickface['check'] == 'Wrong']
        location_pickface_1 = location_pickface_1[['location','Item key','UPC','available qty']]

        # Group the data
        grouped_data = group_data(location_pickface)

        # Convert the dataframes to HTML tables
        html_table_location_pickface = location_pickface_1.to_html(index=False)
        html_table_grouped_data = grouped_data.to_html(index=False)

        context = {
            'html_table_location_pickface': html_table_location_pickface,
            'html_table_grouped_data': html_table_grouped_data
        }

        return render(request, 'check_location\location_pickface.html', context)
    else:
        return render(request, 'check_location\location_pickface.html')
