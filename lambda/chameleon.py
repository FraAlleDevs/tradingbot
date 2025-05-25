import pandas
import time 

csvFile = pandas.read_csv('../data/btcusd_1-min_data.csv')
print(csvFile.iloc(0,1))
