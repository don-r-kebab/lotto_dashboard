import datetime
import json

import streamlit as st
import argparse
import tda
from tda.client import Client as TDAclient
import pandas as pd

import dataccess
from datastructures import Config
from accountdata import AccountData

from streamlit_autorefresh import st_autorefresh


## Settings commands

REFRESH_TIME_MS = 1000*300
refresh_count = 0
st.set_page_config(layout="wide")
#st_autorefresh(REFRESH_TIME_MS, key=refresh_count)


#### Globals

CONFIG: Config = Config()
ACCOUNT_DATA: AccountData = AccountData()
CONFIG_OK = False
DB_OK = False
ALLOW_API = True
ALLOW_DB = True
USE_PMLT_DB = True
USE_API = True

CONTRACT_TYPE = tda.client.Client.Options.ContractType
ORDER_STATUS = tda.client.Client.Order.Status
FIELDS = tda.client.Client.Account.Fields
TRANSACTION_TYPES = tda.client.Client.Transactions.TransactionType



def get_display_df(ad: AccountData, index: list =["Stats"]):
    d = {}
    d['NLV'] = ad.nlv
    d['BPu'] = ad.bpu
    d['Buying Power'] = ad.bp_available
    d['Short Unit Max'] = ad.sutmax
    df = pd.DataFrame(d, index=index)
    return df


#@st.caching
def main(**argv):
    global CONFIG, ACCOUNT_DATA, FIELDS, USE_PMLT_DB
    conf: Config = CONFIG
    adata: AccountData = ACCOUNT_DATA
    #client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    #adata.calc_account_data(config=conf, api=USE_PMLT_DB)
    adata.get_account_data(config=conf, api=USE_PMLT_DB)
    #acc_json = client.get_account(conf.accountnum, fields=[FIELDS.POSITIONS]).json()
    #accdata = acc_json['securitiesAccount']
    #positions = accdata['positions']
    st.write("Updated - {}".format(datetime.datetime.now()))

    with st.sidebar:
        print("Use db?", USE_PMLT_DB)
        data_source = st.selectbox(
            "Data source to use?",
            (
                "PMT Lotto Track DB",
                "API"
            )
        )
        if data_source == "API":
            USE_PMLT_DB = False
        else:
            USE_PMLT_DB = True
        print("Use db?", USE_PMLT_DB)
        with st.expander(
                "Account Stats",
                expanded=True
        ):
            sidebar_df = get_display_df(adata)
            sidebar_df['BPu'] = sidebar_df['BPu'].astype(int)
            st.table(sidebar_df.T)
        if USE_PMLT_DB is False:
            ALLOW_DB = st.checkbox(
                "Allow Database",
                value=False
            )
            st.write("Some plots require database")
        else:
            ALLOW_API = st.checkbox(
                "Allow API",
                value=False
            )
            st.write("May enable/disable certain function")
    return 0

    st.title("Lotto Dashboard")
    #with st.expander("Account"):
    #    pass
    #    st.write(fb.ACCOUNT_DATA)
    #ee    #sutdf = fb.sut_test()

    with st.expander(
        "Today's stats",
        expanded=True
    ):
        st.header("Today's Stats")
        try:
            todays_premium = round(dataccess.get_premium_today(client, conf)*100,2)
            if todays_premium is None:
                todays_premium = 0
            todays_pct = round(todays_premium/adata.nlv * 100,2)
            order_counts = dataccess.get_order_count(client, conf)
        except Exception as e:
            print(e)
            raise e
        col1, col_2 = st.columns(2)
        col1.write("Today's Premium:")
        col_2.write("\t{} ({}%)".format(todays_premium, todays_pct))
        col1.write("Today's Orders:")
        col_2.write("\t{}".format(order_counts))
    with st.expander(
        "Short Unit Test",
        expanded=True
    ):
        st.header("Short Unit Test", )
        sutdf = dataccess.sut_test(positions, adata.sutmax)
        sdf = pd.DataFrame(sutdf, index=[0])
        sdf.index = sdf['type'].astype(str)
        sdf = sdf.drop(columns=['type'])
        method_list = sdf.index
        method = st.selectbox(
            "Calculation Method",
            method_list,
            index=0
        )
        st.write("SUT Max: {}".format(adata.sutmax))

        sut_col1, sut_col2 = st.columns(2)
                #print(idx)
                #print(sdf.loc[idx,:])
        mdf = sdf.loc[method,:]
        calls = [
            #["SUT Max", fb.ACCOUNT_DATA['Max_Short_Units']],
            ["Unit Count", int(mdf['CALL_COUNT'])],
            ["Units remaining", int(mdf['CALL_REMAINING'])],
            ["Call Percent Used", (int(mdf['CALL_PCT_USED']))]
            #["Call Percent Used", "{}%%".format(int(mdf['CALL_PCT_USED']))]
        ]
        puts = [
            ["Unit Count", int(mdf['PUT_COUNT'])],
            ["Units remaining", int(mdf['PUT_REMAINING'])],
            ["Percent Used", int(mdf['PUT_PCT_USED'])]
        ]
        #sut_col1.write(method)
        sut_col1.subheader("Call SUT")
        sut_col1.table(calls)
        sut_col2.subheader("Put SUT")
        sut_col2.table(puts)
        #sut_col2.table(sdf.loc[method,:].T)



        #print(sdf)
        #sut_col1.write("Moo")
        #sut_col2.table(sdf.T)
        #for sut_calc in sutdf:
        #    method = sut_calc['type']
        #    del(sut_calc['type'])
        #    print(sut_calc)
        #    sdf = pd.DataFrame(sut_calc)
        #    sut_col1.write("{}:".format(method))
        #    sut_col2.table(sdf, index=[0])

    with st.expander(
        "Red Alert! - Threatened Postions",
        expanded=True
    ):
        otm_select_values = ("40", "35", "30", "25", "20", "15", "10")
        min_otm_select_value = st.selectbox(
            "Min Percent OTM",
            otm_select_values,
            index=2
        )
        min_otm = int(min_otm_select_value)/100.0
        print(min_otm)
        red_alert_df = dataccess.get_otm_df(conf)
        st.dataframe(
            red_alert_df.loc[red_alert_df['otm'] < min_otm, :]
        )

def setup():


if __name__ == '__main__':
    print("Starting LottoBuddy")
    CONFIG = Config()
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--configfile",
        dest='configfile',
        default='./lotto_config.json',
        metavar="[lotto_config.json]",
        help="Configuration file with TDA APP data created with --setup"
    )
    #ap.add_argument("--tdaconfig", dest="tdaconfig", default=None)
    ap.add_argument(
        "--tdaconfig",
        dest="tdaconfig",
        default="./tda-config.json",
        metavar="[tda-config.json]",
        help="Config file name for where to store TDA API token. Default: ./tda-config.json")
    ap.add_argument(
        "--port",
        dest="port",
        default=5000,
        metavar="int",
        help="Change flask port from default 5000. This is important for Mac's because 5000 is taken by airply by default"
    )
    # This is intended to enabling/disabling auto-refresh on dashboard
    # Currently not implemented and is hard coded to be true
    ap.add_argument("--update", default=False, action="store_true")
    args = vars(ap.parse_args())
    CONFIG.read_config(args['configfile'])
    st.session_state['configfile'] = args['configfile']
    st.session_state['tdaconfig'] = args['tdaconfig']
    main(**args)

