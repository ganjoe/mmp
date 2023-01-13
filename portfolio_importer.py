# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 14:09:35 2023

@author: danie
"""
#from io import StringIO
#import datetime
import pandas as pd
#import json
#import logging
#import numpy


from degiro_connector.trading.api import API
from degiro_connector.trading.models.trading_pb2 import Credentials,   ProductSearch
import degiro_connector.core.helpers.pb_handler as payload_handler
from degiro_connector.quotecast.api import API as QuotecastAPI
from degiro_connector.quotecast.models.quotecast_pb2 import Quotecast
import math

 

# SETUP API
quotecast_api = QuotecastAPI(user_token=323523)

# BUILD REQUEST
request = Quotecast.Request()


# SETUP CREDENTIALS
credentials = Credentials(
    username = 'danielmeier',
    password = 'Yehf050477',
    int_account = 31041792,  # OPTIONAL FOR LOGIN
)

trading_api = API(credentials=credentials)
trading_api.connect()

#------------------------------------------------------------------------------------------------------#

source_file = 'transfer.xlsx'
target_file = 'transfer_out.xlsx'

#dict für suchanfragen
search_request = {'isin':'DE000FTG1111', 'currency':'EUR'}


def dgSearchISIN(search_request):
    request_lookup = ProductSearch.RequestLookup(search_text=search_request['isin'])
    products_lookup = trading_api.product_search(request=request_lookup, raw=False)
    products_lookup_dict = payload_handler.message_to_dict(message=products_lookup)
    
    if search_request['currency'] == 'nan':
         search_request['currency']= 'USD'
        
    #Nur die Dicts selektieren die den Suchstring enthalten, den degiro findet bei jedem string 'etwas'
    liste = products_lookup_dict['products']
    print('dgSearchISIN:\t', search_request['isin'], '\tEinträge gefunden: ', len(liste), end='')
    sliste = []
    for dicts in liste:   
        if dicts['isin'] == search_request['isin']:
            sliste.append(dicts)
            print('\t match: isin', end='') 
        if dicts['symbol']== search_request['isin']:
            sliste.append(dicts)
            print('\t match: symbol', end='')
        if dicts['id']== search_request['isin']:
            sliste.append(dicts)   
            print('\t match: id', end='')
        if dicts['name']== search_request['isin']:
            sliste.append(dicts)
            print('\t match: name', end='')
        
    print('\t geamt:', len(sliste))    
    
    if not sliste:
        ergebnis = {'isin':'not found'}
        return ergebnis

# die Suchantwort mit der Zielwährung selektieren
    pliste = []
    for dicts in sliste:
        if dicts['currency'] == search_request['currency']:
            pliste.append(dicts)

# # die Suchantwort mit der vorzugsbörse wählen
    if not pliste:
        ergebnis = {'currency': 'not found'}
        return ergebnis

    return pliste[0]

def dgFillPrice(product_dict):
    
    request = Quotecast.Request()
    request.subscriptions[product_dict['vwdId']].extend(
        [
            "LastDate",
            "LastTime",
            "LastPrice",
            "LastVolume",
            "LastPrice",
            "AskPrice",
            "BidPrice",
        ]
    )

    # FETCH METRICS
    ticker_dict = quotecast_api.fetch_metrics(
        request=request,
    )
    
    return ticker_dict[product_dict['vwdId']]


#source_file in pandas öffnen
try:
    df = pd.read_excel(source_file)
except:
    print("datei kann nicht geöffnet werden "+ source_file)



for values, row in df.iterrows():
    #isin aus excel
    isin = row['isin']
    #leerzeichen entfernen die durch copy&paste 
    try:
        search_request['isin'] = isin.strip()
    except Exception:
        print('nan?')
    #währung als selektor für suchergebnisse
    search_request['currency'] = row['currency']
    print('suche: ',search_request)
    ergebnis = dgSearchISIN(search_request)
    #die suchstrings können fehlermeldungen enthalten und werden daher zurückgeschrieben
    df.loc[values,('name')] = ergebnis['name']
    df.loc[values,('currency')] = ergebnis['currency']
    df.loc[values,('isin')] = ergebnis['isin']
    df.loc[values,('type')] = ergebnis['productType']
    # Preise aus der Degiro Produktsuche, oder falls nicht vorhanden, vom kursprovider
    try:
        df.loc[values,('price')] = ergebnis['closePrice']
    except:
        try:
            df.loc[values,('price')] =dgFillPrice(ergebnis)['LastPrice']
        except:
            df.loc[values,('price')] = 0
        pass
            
for values, row in df.iterrows():

    # Sollwert = soll * bemessung * faktor / 100
    #   Sollwert    ist das Investment in einen Wert
    #   Bemessung   ist die Summe aller Investments, also Portfolio - cash
    #   Faktor      ist bei Aktien 1 und bei optionen der Hebelfaktor
    #   soll        ist die gewichtung im portfolio (bezogen auf bemessung)
    #   100         ist die skalierung von soll auf Prozent ( 2.3% -> 0,023)
    
    try:
        df.loc[values,['soll']] = df['soll'][values].strip('%')
    except:
        pass
    try:
        df.loc[values,['sollwert']]= ((float(df.loc[values,['soll']])
                                      * float(df.loc[0,['bemessung']]))
                                      / float(df['faktor'][values])
                                      /100)
    except:
        print(" sollwert konnte nicht berechnet werden, faktor = 0 ?")
        df.loc[values,['sollwert']]= 0

    # sollzahl = sollwert / price (abgerundet auf null stellen mit math.floor)
    # 
    try: df.loc[values,['sollzahl']] =  (math.floor
                                        (float(df.loc[values,['sollwert']]) 
                                        /float(df.loc[values,['price']])))
    except: 
        print(" sollwert konnte nicht berechnet werden, price = 0 ?")
        df.loc[values,['sollzahl']] = 0

    #   Istwert  =  sollzahl * preis

    try:
        df.loc[values,['istwert']]= (float(df.loc[values,['sollzahl']])
                                     * float(df.loc[values,['price']]))

    except:
        print(" fehler istwert berechnen")
        df.loc[values,['istwert']]= 0
        
    #   Ist  =  istwert / bemessung * 100
    #   die tatsächliche gewichtung des investments

    try:
        df.loc[values,['ist']]= (float(df.loc[values,['istwert']])
                                     / float(df.loc[0,['bemessung']])
                                     * 100)

    except:
        print(" fehler bei 'ist' berechnung aufgetreten. bemessung == 0 ?")
        df.loc[values,['ist']]= 0
        
    #   Fehler  =  abs ( ist - soll)
    #   die abweichung in der gewünschten portfoliogewichtung

    try:
        df.loc[values,['fehler']]= (float(df.loc[values,['soll']])- 
                                    float(df.loc[values,['ist']]))
        
    except:
            pass
#-------------------------------------------------------------------------#


    #   Summe = summe(istwert)
    #   wert aller investments. 
    # Der Text wird in die Spalte Portfolio geschrieben
df.loc[0,['summe']]= df['istwert'].sum()