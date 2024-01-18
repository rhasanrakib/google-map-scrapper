import os
import json
import pandas as pd

folder_path = "./json_reviews"
output_path = "./map_datasets/"

if not os.path.exists(output_path):
    os.makedirs(output_path)

json_data = []

for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)

        with open(file_path, "r") as json_file:
            try:
                data = json.load(json_file)
                if not isinstance(data, list):
                    data = [data]
                json_data+=data
            except json.JSONDecodeError as e:
                print(f"Error parsing {file_path}: {e}")

df = pd.DataFrame(json_data)
df.to_csv(output_path+'info.csv',index=False)

