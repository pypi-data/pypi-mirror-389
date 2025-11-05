def show():
    code = """Question 1
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
path=r'C:\Users\nmims.student\Desktop\Abhishek Pracs\IMLT\Data'
data=pd.read_csv(path+'\\yob1880.txt',names=['Name','Gender','Birth'],header=None)
data.groupby('Gender')['Birth'].sum()

#Question 2
years=range(1880,2018)
pieces=[]
columns=['Name','Gender','Birth']
for year in years:
    path='C:\\Users\\nmims.student\\Desktop\\Abhishek Pracs\\IMLT\\Data\\yob%d.txt'%year
    frame=pd.read_csv(path,names=columns)
    frame['Year']=year
    pieces.append(frame)

#Concatenate everything into a single dataframe
names=pd.concat(pieces,ignore_index=True)

#Question 3
total_births=names.pivot_table('Birth',index='Year',columns='Gender',aggfunc=sum)
print(total_births)
total_births.plot(title='Total births by gender and year')
plt.show()

#Question 4
total_births=names.pivot_table('Birth',index='Year',columns='Name',aggfunc=sum)
names['prop']=names['Birth']/names['Birth'].sum()
names.head()

#Question 5
top1000=names.nlargest(1000,['prop'])
print(top1000)

#Question 6
subset = total_births[['John', 'Harry', 'Mary', 'Marilyn']]
subset
subset.plot(subplots=True, figsize=(12, 10), grid=False,title="Number of births per year")

#Question 7

# uniquenames= names['Name'].unique().sum()
# len(uniquenames)
# uniquenames[:]

# df = boysfromnames[boysfromnames.year == 2010]
# df1 = boysfromnames[boysfromnames.year == 1900]

# popularity= df.sort_values(by='prop', ascending=False)
# popularity.head(int(len(popularity)/2))


# popularity1= df1.sort_values(by='prop', ascending=False)
# popularity1.head(int(len(popularity1)/2))
"""
    print(code)