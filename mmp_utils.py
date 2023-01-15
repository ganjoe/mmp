# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 13:07:49 2023

@author: pymd02
"""
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

def searchTickerInStocks(search_request):
    request_lookup = ProductSearch.RequestStocks(search_text=search_request['ticker'])
    products_lookup = trading_api.product_search(request=request_lookup, raw=False)
    products_lookup_dict = payload_handler.message_to_dict(message=products_lookup)
    products = products_lookup_dict['products']
    
    anzahl = len(products)
    print('suchergebnisse: ', len(products))
    
    while anzahl > 0:
        #print('anzahl', anzahl)
        anzahl -=1
        if products[anzahl]['symbol'] != search_request['ticker']:
            products.pop(anzahl)
            anzahl = len(products)
            #print('ticker nicht gefunden', anzahl)
    
    if len(products) == 0:
        print('ticker nicht gefunden: ', search_request)
    else:
        print( 'ticker gefunden: ', len(products))
    return products

# request_lookup = ProductSearch.RequestStocks(search_text='MS')
# products_lookup = trading_api.product_search(request=request_lookup, raw=False)
# products_lookup_dict = payload_handler.message_to_dict(message=products_lookup)
# products = products_lookup_dict['products']


