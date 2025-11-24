import pandas as pd

"""this is just a module to do customized filtering or others"""

df = pd.read_csv('C:/Users/Jean/Desktop/prospeccion/España/illes balears.csv')
print(len(df))
print(df.info())
df = df[(~pd.isna(df['url']) & (df['rating'] > 3) & (df['reviews_count'] > 5))]

print(len(df))
df.to_csv('./filtrado_baleares.csv', index=False)
