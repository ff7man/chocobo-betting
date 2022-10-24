import pandas as pd
adf = pd.read_csv('b1000.csv')
adf = adf.dropna()
adf = adf.drop(['order-b152','mystery_typeb156','intel_adjb124','intel_typeb104','all'],1)
adf = adf.drop(['b4-chocop','b73','b81','b104','b118','b124','b141','Cooperation','Acceleration'],1)
adf = adf.drop(['b8','b22-camera1','b38-camera2','b62','b85','b90','b114','b146','b2-jockeyp'],1)
# change rank bronze->plat->silver->gold
adf.loc[adf['jockeyb28'] == "0",'jockey'] = "3" # plat #1
adf.loc[adf['jockeyb28'] == "1",'jockey'] = "2" # gold #
adf.loc[adf['jockeyb28'] == "2",'jockey'] = "0" # bronze #0
adf.loc[adf['jockeyb28'] == "3",'jockey'] = "1" # silver #2
adf.loc[adf['Sprinting'] == "2",'Sprinting'] = "1" # Change sprinting to be 1 instead of 2
dfs = []
for i in range(0,len(adf),8):
 tempdf = adf.iloc[i:i+6].reset_index(drop=True)
 tempdf.iloc[0]['Willingness to Sprint'] = tempdf.iloc[1]['Willingness to Sprint']
 dfs.append(tempdf)
ndf = pd.concat(dfs)
cols = ndf.columns.drop(['Willingness to Sprint','name'])
ndf[cols] = ndf[cols].apply(pd.to_numeric,errors='coerce')
ndf['Willingness to Sprint'] = ndf['Willingness to Sprint'].astype(str)
ndf['name'] = ndf['name'].astype(str)

print("Sorting by Win-Order")
result = ndf.groupby(['win-order']).mean().sort_values('win-order',ascending=True)
print(result)

print("Sorting by Sprinting")
result = ndf.groupby(['Sprinting']).mean().sort_values('win-order',ascending=True)
print(result)

print("Sorting by Intelligence")
result = ndf.groupby(['Intelligence']).mean().sort_values('win-order',ascending=True)
print(result)

print("Sorting by sprinting and intelligence")
result = ndf.groupby(['Sprinting','Intelligence']).mean().sort_values('win-order',ascending=True)
print(result)

print("Sorting by sprinting and jockey")
result = ndf.groupby(['Sprinting','jockey']).mean().sort_values('win-order',ascending=True)
print(result)

print("Sorting by sprinting, jockey, and intelligence")
result = ndf.groupby(['Sprinting','jockey','Intelligence']).mean().sort_values('win-order',ascending=True)
print(result)

print("Sorting by jockey, sprinting, and intelligence")
result = ndf.groupby(['jockey','Sprinting','Intelligence']).mean().sort_values('win-order',ascending=True)
print(result)

print("Sorting by jockey and intelligence")
result = ndf.groupby(['jockey','Intelligence']).mean().sort_values('win-order',ascending=True)
result = ndf.groupby(['jockey','Intelligence']).mean().sort_values('win-order',ascending=True)
print(result)

print("Sorting by jockey and course")
result = ndf.groupby(['jockey','Willingness to Sprint']).mean().sort_values('win-order',ascending=True)
print(result)

print("Sorting by jockey, course, and intel")
result = ndf.groupby(['jockey','Willingness to Sprint','Intelligence']).mean().sort_values('win-order',ascending=True)
print(result)

print("Sorting by jockey, course, and sprinting")
result = ndf.groupby(['jockey','Willingness to Sprint','Sprinting']).mean().sort_values('win-order',ascending=True)
print(result)
