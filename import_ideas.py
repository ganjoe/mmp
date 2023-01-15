
import pandas as pd
from mmp_utils import searchTickerInStocks as stocksearch

source_file = 'ideas.xlsx'
target_file = 'transfer.xlsx'

try:
    dfs = pd.read_excel(source_file)
except:
    print("datei kann nicht geöffnet werden " , source_file)
    
dft = pd.DataFrame({'ticker':[], 'basiswert':[], 'side':[], 'soll':[], 'proxy':[], 'isin':[]})
dft['ticker'] = dfs['Symbol']
dft['basiswert'] = dfs['Issue']
dft['side'] = dfs['Position']
dft['soll'] = dfs['Current Weight of Portfolio (%)']
dft['stoploss'] = dfs['Stop']

for values, row in dft.iterrows():
    try:    dft.loc[values,['soll']] = dft['soll'][values].strip('%')
    except:    pass

search_request = {'type':'STOCK',
                  'isin':'', 
                  'currency':'',
                  'ticker':'MSFT',
                  'name':'',
                  'id':''}
# suche nach ticker und währung

ergebnis =stocksearch({'ticker':'MS'})

for values, row in dft.iterrows():
    ergebnis =stocksearch({'ticker':row['ticker']})
    if len(ergebnis) > 0:
        dft.loc[values,['isin']]= ergebnis[0]




















