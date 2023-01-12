# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 19:45:39 2023

@author: danie
"""

from io import StringIO
import datetime
import pandas as pd

from degiro_connector.trading.api import API
from degiro_connector.trading.models.trading_pb2 import Credentials, PositionReport


# SETUP CREDENTIALS
credentials = Credentials(
    username = 'danielmeier',
    password = 'Yehf050477',
    int_account = 31041792,  # OPTIONAL FOR LOGIN
)

trading_api = API(credentials=credentials)
trading_api.connect()


# SETUP REQUEST
today = datetime.date.today()
to_date = PositionReport.Request.Date(    year=today.year,    month=today.month,    day=today.day,)
request = PositionReport.Request(    format=PositionReport.Format.CSV,    country="DE",    lang="de",    to_date=to_date,)

# FETCH DATA
position_report = trading_api.get_position_report(    request=request,    raw=False,)
format = position_report.Format.Name(position_report.format)

#content ist ein String mit Inhalt einer CSV datei
content = position_report.content

#Einlesen der CSV ohne die Datei zu schreiben
csvStringIO = StringIO(content)
df = pd.read_csv(csvStringIO, sep=",", header = None)

#Header manuell Hinzufügen
df.columns = ["Name", "ISIN", "Quantity", "Price", "Currency", "Investment"]

#Cashfund speichern
cash = float(df.iloc[1,4].split(' ')[1])

#Orginal Header und Cashfund angaben löschen
df = df.drop([0,1], axis = 0)

#Index neu vergeben
df.reset_index(inplace = True,drop=True)

#das Komma im String durch einen Punkt ersetzen
for values, row in df.iterrows():
    row['Price'] = row['Price'].replace(',','.')
    
for values, row in df.iterrows():
    row['Investment'] = row['Investment'].replace(',','.')

#Alle Zahlen nach Float konvertieren
df['Quantity'] =    df['Quantity'].astype(float)
df['Investment'] =  df['Investment'].astype(float)
df['Price'] =       df['Price'].astype(float)

# Gesamtwert Summieren
gesamtwert = float(0)
for values, row in df.iterrows():
    gesamtwert += row['Investment']
    
# neue Spalte ergänzen für ist-gewichtung
df.insert(loc = len(df.axes[1]), column = 'current %', value = 0)

# Dictionary für Zusammenfassung
summary = {'Gesamtwert': gesamtwert,'Cash': cash, 'Letzte Aktualisierung': datetime.date.today()}

# Cash als Position einfügen
zeile = len(df)
df.loc[zeile,['Name']] = ['Cash:']
df.loc[zeile,['Investment']] = summary['Cash']

#gewichtung ausrechnen
for values, row in df.iterrows():
    df.loc[values,['current %']]= ( row['Investment'] / gesamtwert) * 100

# Weitere Infos als letzte Zeile anhängen
zeile = zeile + 1
df.loc[zeile,['Name']] = ['Gesamt:']
df.loc[zeile,['Investment']] = summary['Gesamtwert']
zeile = zeile + 1
df.loc[zeile,['Name']] = ['Datum:']
df.loc[zeile,['ISIN']] = summary['Letzte Aktualisierung']

try:
    df.to_excel('report.xlsx')
except:
    print("report.xlsx konnte nicht geschrieben werden")


