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

plot = "Open Contracts"
by = "Expiration"
ptype = "Barplot"


red_alert_df = dataccess.get_otm_df(CONFIG).drop(columns=['ctype', 'symbol'])

st.dataframe(red_alert_df)

def plot_open_contracts_by_expiration(plot_type):
    global CONFIG, FIELDS
    conf = CONFIG
    print(conf)
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    acc_json = client.get_account(conf.accountnum, fields=[FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    p = {}
    d = []
    #df = pd.DataFrame()
    #df.columns = ['exp', 'ptype', 'count']
    for pentry in positions:
        pins = pentry['instrument']
        if pins['assetType'] == "OPTION":
            raw = pentry["instrument"]['symbol'].split("_")[1][0:6]
            raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
            if raw_exp not in p:
                p[raw_exp] = {
                "long": 0.0,
                "short": 0.0
            }
            p[raw_exp]['long'] += pentry['longQuantity']
            p[raw_exp]['short'] += pentry['shortQuantity']
    for exp in p:
        for ptype in p[exp]:
            d.append([exp, ptype, p[exp][ptype]])
    #df = pd.DataFrame.from_dict(p, orient='columns')
    df = pd.DataFrame(d)
    df.columns = ['exp', 'ptype', 'count']
    print(df.head())
    if plot_type == "Barplot":
        fig, ax = plt.subplots()
        sns.barplot(
            ax=ax,
            data=df,
            x="exp",
            y="count",
            hue="ptype"
        )
        ax.set_title("Contract count by expiration")
        for xtl in ax.get_xticklabels():
            xtl.set_rotation(90)
        fig.tight_layout()
        return fig,ax

def get_outstanding_premium_by_expiration(plot_type):
    global CONFIG
    conf = CONFIG
    #print(conf)
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    acc_json = client.get_account(conf.accountnum, fields=[FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    p = {}
    d = []
    #df = pd.DataFrame()
    #df.columns = ['exp', 'ptype', 'count']
    for pentry in positions:
        pins = pentry['instrument']
        if pins['assetType'] == "OPTION":
            raw = pentry["instrument"]['symbol'].split("_")[1][0:6]
            raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
            if raw_exp not in p:
                p[raw_exp] = {
                "Current Mark": 0.0,
                "Opening Price": 0.0
            }
            p[raw_exp]['Current Mark'] += abs(pentry['marketValue'])
            p[raw_exp]['Opening Price'] += (
                (pentry['longQuantity'] + pentry['shortQuantity']) * pentry['averagePrice']*100
            )
    for exp in p:
        for ptype in p[exp]:
            d.append([exp, ptype, p[exp][ptype]])
    #df = pd.DataFrame.from_dict(p, orient='columns')
    df = pd.DataFrame(d)
    df.columns = ['Expiration', 'Measure', 'Value']
    return df
    #print(df.head())

def get_otm_df():
    global CONFIG
    conf = CONFIG
    #print(conf)
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    acc_json = client.get_account(conf.accountnum, fields=[FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    df = fb.get_red_alert_df2(client, positions)
    df['expiration'] = "000101"
    for idx in df.index:
        sym = df.loc[idx,'symbol']
        raw = sym.split("_")[1][0:6]
        raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
        df.loc[idx, 'expiration'] = raw_exp
    return df.drop(columns='symbol')

def get_pmtlt_db_conn():
    import appdirs
    from appdirs import user_data_dir, user_config_dir
    from pathlib import Path
    import sqlite3
    import sqlalchemy
    global CONFIG
    conf = CONFIG
    PACKAGE_NAME = "pmtlottotracker"
    AUTHOR = "PMTraders"
    CONFIG_DIR = user_config_dir(appname=PACKAGE_NAME, appauthor=AUTHOR)
    CONFIG_PATH = Path(CONFIG_DIR, "config.toml")
    DATA_DIR = user_data_dir(appname=PACKAGE_NAME, appauthor=AUTHOR)
    DB_PATH = Path(DATA_DIR, "Lotto-Tracker.db")
    uri = "sqlite:///{}".format(DB_PATH)
    print(uri)
    conn = sqlalchemy.create_engine(uri)
    print(conn)
    return conn

def get_daily_premium_sold(STARTDATE=None):
    global CONFIG
    conf = CONFIG
    pmtlt_conn = get_pmtlt_db_conn()
    q = """
    SELECT option_symbol, date, price, filled_quantity, underlying_symbol, asset_type, instruction, status
    FROM orders_history
    WHERE status='FILLED'
    """
    if STARTDATE is not None:
        q = q + f" AND date > date({STARTDATE})"
    df = pd.read_sql_query(q, pmtlt_conn)

    df['date'] = pd.to_datetime(df['date'])
    df['total'] = df['price'] * df['filled_quantity']
    df.loc[df['instruction']=="BUY_TO_CLOSE",'total'] = df.loc[df['instruction']=="BUY_TO_CLOSE",'total'] * -1
    df.loc[df['instruction']=="BUY_TO_OPEN",'total'] = df.loc[df['instruction']=="BUY_TO_OPEN",'total'] * -1
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    #print(df.head())
    #print(df.info())
    return df



