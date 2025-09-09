import pandas as pd
import re
import numpy as np

from google.colab import drive
import folium
from folium import plugins

file_name = 'observatorio-de-obras-urbanas.csv'

keys = ('nombre', 'lat', 'lng')
map_records = []
df = pd.read_csv(file_name, encoding='ISO-8859-1', delimiter=';')

# Clean and convert 'lat' and 'lng' columns using pandas
df['lat'] = df['lat'].astype(str).str.replace(',', '.', regex=False)
df['lng'] = df['lng'].astype(str).str.replace(',', '.', regex=False)

# Use to_numeric with errors='coerce' to handle conversion and invalid values
df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
df['lng'] = pd.to_numeric(df['lng'], errors='coerce')

# Drop rows where either lat or lng is NaN (could not be converted)
df.dropna(subset=['lat', 'lng'], inplace=True)

map = folium.Map(location=[-34.6218974,-58.4078541], zoom_start=12)

for index, row in df.iterrows():
  map_records.append({key: row[key] for key in keys})


heat_data = []
for index in range(len(map_records)):
  coords = [map_records[index]['lat'], map_records[index]['lng']]
  heat_data.append(coords)

# plugins.HeatMap(heat_data).add_to(map)
plugins.FastMarkerCluster(data=heat_data).add_to(map)
map
