import datetime
from datetime import datetime, timedelta

import matplotlib
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import tda

import dataccess
import streamlit_lotto_dashboard as sb
from datastructures import Config

print(__name__)
print(st.session_state['configfile'])

FIELDS = tda.client.Client.Account.Fields
CONFIG = Config()
CONFIG.read_config(
    config_file=st.session_state['configfile']
)

client = tda.auth.easy_client(CONFIG.apikey, CONFIG.callbackuri, CONFIG.tokenpath)
with st.container():
    start_date = st.date_input(
        label="moo",
        value=datetime.today()
    )
    end_date = st.date_input(
        label="enddate",
        value=datetime.today()
    )
st.write(type(start_date))
orders = dataccess.get_orders_back(
    client=client,
    conf=CONFIG,
    startdate=datetime(start_date.year, start_date.month, start_date.day),
    enddate=datetime(end_date.year, end_date.month, end_date.day)
)

st.json(orders)
#for oday_count in orders:
    #order_json = orders[oday_count]


