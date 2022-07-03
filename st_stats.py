import streamlit as st
import pandas as pd
import tda
from  tda.client import Client

def todays_stats(
        stcontainer: st.container,
        client: Client,
        conf: Config
):
    with stcontainer:
        st.subheader("Today's Stats")
        try:
            todays_premium = round(fb.get_premium_today(client, conf.accountnum) * 100, 2)
            if todays_premium is None:
                todays_premium = 0
            todays_pct = round(todays_premium / fb.ACCOUNT_DATA['NLV'] * 100, 2)
            order_counts = fb.get_order_count(client, conf, conf.accountnum)
        except Exception as e:
            print(e)
            raise e
        #col1, col_2 = st.columns(2)
        st.markdown(
            f"""
            - Today's Premium:&nbsp;&nbsp;&nbsp;&nbsp;${todays_premium} ({todays_pct}%)
            - Today's orders:&nbsp;&nbsp;&nbsp;&nbsp;{order_counts}
            """
        )

        #st.write("Today's Premium:")
        #st.write("--{} ({}%)".format(todays_premium, todays_pct))
        #st.write("Today's Orders:")
        #st.write("\t{}".format(order_counts))

def sut_call_table(
        stcontainer: st.container,
        position_json: dict,
        sutmax: int = 0,
        label: str = None
):
    heading = "Call SUT"
    with stcontainer:
        st.subheader(heading)
        with st.spinner("Loading SUT Data"):
            sutdf = fb.sut_test(position_json, sutmax)
            sdf = pd.DataFrame(sutdf, index=[0])
            sdf.index = sdf['type'].astype(str)
            sdf = sdf.drop(columns=['type'])
            method_list = sdf.index
        method = st.selectbox(
            "Calculation Method",
            method_list,
            index=0,
            key="call_sut_method_{}".format(label)
        )
        mdf = sdf.loc[method, :]
        tab = [
            ["Unit Count", int(mdf['CALL_COUNT'])],
            ["Units remaining", int(mdf['CALL_REMAINING'])],
            ["Sut Max", sutmax],
            ["Call Percent Used", (int(mdf['CALL_PCT_USED']))]
        ]
        st.table(tab)

def sut_data_table(
        stcontainer: st.container,
        position_json: dict,
        sutmax: int = 0,
        contract_type: str = None,
        label: str = None
):
    with stcontainer:
        if contract_type == "C" or contract_type == "CALL":
            heading = "Call SUT"
        elif contract_type == "P" or contract_type == "PUT":
            heading = "Put SUT"
        st.subheader(heading)
        with st.spinner("Loading SUT Data"):
            sutdf = fb.sut_test(position_json, sutmax)
            sdf = pd.DataFrame(sutdf, index=[0])
            sdf.index = sdf['type'].astype(str)
            sdf = sdf.drop(columns=['type'])
            method_list = sdf.index
        method = st.selectbox(
            "Calculation Method",
            method_list,
            index=0,
            key="{}_{}"
        )
        mdf = sdf.loc[method, :]
        tab = None
        if contract_type == "C" or contract_type == "CALL":
            tab = [
            # ["SUT Max", fb.ACCOUNT_DATA['Max_Short_Units']],
                ["Unit Count", int(mdf['CALL_COUNT'])],
                ["Units remaining", int(mdf['CALL_REMAINING'])],
                ["Sut Max", sutmax],
                ["Call Percent Used", (int(mdf['CALL_PCT_USED']))]
            # ["Call Percent Used", "{}%%".format(int(mdf['CALL_PCT_USED']))]
            ]
        elif contract_type == "P" or contract_type == "PUT":
            tab = [
                ["Unit Count", int(mdf['PUT_COUNT'])],
                ["Units remaining", int(mdf['PUT_REMAINING'])],
                ["Sut Max", sutmax],
                ["Percent Used", int(mdf['PUT_PCT_USED'])]
            ]
        st.table(tab)