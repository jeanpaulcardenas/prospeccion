import geopandas
from geopy.distance import geodesic
from math import cos, sin, pi
import json
import os
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt

gdf = gpd.read_file('./gadm41_ESP_4.json')  # Or gadm41_ESP_3.json for municipalities

# Inspect column names to find Córdoba's field
print(gdf.columns)
# Level 2: NAME_2 is province, Level 3: NAME_3 is municipality

# Filter for Córdoba (province or city)
# cordoba: gpd.geodataframe.GeoDataFrame = gdf[(gdf['NAME_4'] == 'Córdoba')]  Adjust based on the file
# print(cordoba.geometry, type(cordoba))
# print(f'area: {cordoba.geometry.to_crs(crs="EPSG:25831").area}')
# Plot Córdoba only
# cordoba.plot(edgecolor='black', figsize=(8, 8))



class GeoFinder:
    def __init__(self, gadm_file_path: str):
        self.gdf: gpd.geodataframe.GeoDataFrame = gpd.read_file(gadm_file_path)

    def get_lvl_4(self, lvl_4: str):
        try:
            city = self.gdf[(gdf['NAME_4'] == 'Córdoba')]
            return city
        except KeyError as e:
            print(e)
            return None


cordoba = GeoFinder(gadm_file_path="./gadm41_ESP_4.json").get_lvl_4('Córdoba')
# plt.show()
cordoba_as_rectangle = cordoba.envelope
idx = cordoba.geometry.index[0]
min_x, min_y, max_x, max_y = cordoba_as_rectangle.bounds.loc[idx]
print(cordoba_as_rectangle.bounds.loc[idx])
print(min_x, min_y, max_x, max_y)
top_left = min_x, max_y
top_right = max_x, max_y
bottom_left = min_x, min_y
distance_x = geodesic(top_left, top_right)
print(distance_x)
distance_y = geodesic(top_left, bottom_left)
print(distance_y)
radius = 20
earth_radius = 6371
angle = 135
figure = plt.plot(figsize=(8, 8))
r_lat = max_y + radius * cos(angle * pi/180) / earth_radius
r_long = min_x + radius * sin(angle * pi/180) / earth_radius
first_center = (r_long, r_lat)
first_center_p = Point(first_center)
cordoba.envelope.plot(edgecolor='black', figsize=(8, 8))
print(first_center)
print(geodesic(top_left, first_center))
center = gpd.geoseries.GeoSeries(first_center_p)
center.plot()
plt.show()
