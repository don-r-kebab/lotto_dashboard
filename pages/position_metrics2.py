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
import flask_buddy as fb
from flask_buddy import Config

print(__name__)
print(st.session_state['configfile'])

CONFIG = Config()
CONFIG.read_config(
    config_file=st.session_state['configfile']
)

plot = "Open Contracts"
by = "Expiration"
ptype = "Barplot"

def plot_open_contracts(stconf_con: st.container, stplot_con: st.container ,config:Config):
    st_key = "plot_open_contracts"
    with st.spinner("Building Data Frame"):
        table = __get_open_contracts_by_expiration(config=config)
    with stconf_con:
        col1,col2 = st.columns(2)
        col1.subheader("What to show")
        col2.subheader("Settings")
        add_net = col2.checkbox("Add Net Values?", value=False)
        ptype_filter_box = col2.multiselect(
            "Contract Type Filter",
            ["Long", "Short"],
            ["Long", "Short"],
            key = f"{st_key}_pytpe_filter"
        )
        if add_net:
            neg_table = table.copy()
            neg_table.loc[neg_table['ptype']=="long","count"] *= -1
            gb = neg_table.groupby("exp").sum().reset_index()
            gb.insert(1,"ptype","Net")
            gb.insert(1,"ctype","NET")
            table = pd.concat([table,gb]).sort_values(["exp", "ptype"])
        show_how = col1.selectbox(
            "Show how?",
            (
                "Barplot",
                "Table"
            ),
            index=0
        )
        if show_how == "Barplot":
            plot_by = col1.selectbox(
                "Plot by?",
                (
                    "Expiration",
                )
            )
            col2.write("###### Display settings")
            display_options = col2.multiselect(
                "open_contract_barplot_by_expiration_display_options",
                ['Tight Layout', "Title", "Show Bar Values"],
                ['Tight Layout', "Title", "Show Bar Values"]
            )
        if show_how == "Table":
            group_by = col1.selectbox(
                "Group By?",
                (
                    "Nothing",
                    "Expiration"
                ),
                index=0
            )
            if group_by == "Expiration":
                pass
        if "Long" not in ptype_filter_box:
            table = table.loc[table['ptype'] != "long"]
        if "Short" not in ptype_filter_box:
            table = table.loc[table['ptype'] != "short"]

            #tight_layout = col2.checkbox("Tight Layout", value=True)
            #title = col2.checkbox("Title", value=True)
            #show_bar_values = col2.checkbox("Barplot Value Labels", value=True)
    if show_how == "Table":
        stplot_con.table(table)
    else:
        fig, ax = plt.subplots()
        with st.spinner("Generating plot"):
            if show_how == "Barplot":
                sns.barplot(
                        ax=ax,
                        data=table,
                        x="exp",
                        y="count",
                        hue="ptype"
                )
                for xtl in ax.get_xticklabels():
                    xtl.set_rotation(90)
                if "Title" in display_options:
                    ax.set_title("Contract count by expiration")
                if "Tight Layout" in display_options:
                    fig.tight_layout()
        stplot_con.pyplot(fig)


def __get_open_contracts_by_expiration(config: Config):
    positions = dataccess.get_positions_json(config)
    p = {}
    d = []
    pentry: dict
    for pentry in positions:
        pins = pentry['instrument']
        if pins['assetType'] == "OPTION":
            putcall = pins['putCall']
            raw = pentry["instrument"]['symbol'].split("_")[1][0:6]
            raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
            if raw_exp not in p:
                p[raw_exp] = {
                "long": 0.0,
                "short": 0.0
            }
            p[raw_exp]['long'] += pentry['longQuantity']
            p[raw_exp]['short'] += pentry['shortQuantity']
            e = [raw_exp, putcall, 'long', pentry['longQuantity']]
            d.append((e))
            e = [raw_exp, putcall, 'short', pentry['shortQuantity']]
            d.append(e)
    for exp in p:
        for ptype in p[exp]:
            #d.append([exp, ptype, p[exp][ptype]])
            pass
    #df = pd.DataFrame.from_dict(p, orient='columns')
    df = pd.DataFrame(d)
    df.columns = ['exp', 'ctype', 'ptype', 'count']
    df = df.groupby(["exp", "ctype", "ptype"]).sum().reset_index()
    return df

def plot_outstanding_premium(stconf_con, stplot_con, config):
    plot_key = "outstanding_premium"
    with st.spinner("Fetching Data"):
        table = __get_outstanding_premium_by_expiration(config)
        table = table.drop(columns=["Quantity"])
    with stconf_con:
        col1, col2 = stconf_con.columns(2)

        col1.subheader("What to show")
        col2.subheader("Settings")
        show_how = col1.selectbox(
            "Show how?",
            (
                "Barplot",
                "Table"
            ),
            index=0
        )

        show_by = col1.selectbox(
            "Show Against",
            ("Expiration",),
            key=f"{plot_key}_show_by"
        )
        group_by = col1.selectbox(
            "Breakdown By",
            (
                "Combined",
                "Long vs Short",
                "Call vs Put",
                "All against All"
            )
        )
        filter_putcall_options = col2.multiselect(
            "Outstanding Premium Put Call",
            ['PUT', "CALL"],
            ['PUT', "CALL"],
            key=f"{plot_key}_put_call"
        )

        if "PUT" not in filter_putcall_options:
            table = table.loc[table['Contract Type'] != "PUT", :]
        if "CALL" not in filter_putcall_options:
            table = table.loc[table['Contract Type'] != "CALL", :]
        if group_by == "Combined":
            #table = table.groupby(["Expiration", "Longshort", "Contract Type", "Price Type"]).sum()
            table = table.groupby(["Expiration", "Price Type"]).sum().reset_index()
        if show_how == "Table":
            stplot_con.table(table)
        else:
            plotdf = table
            fig, ax = plt.subplots()
            with st.spinner("Generating plot"):
                if show_how == "Barplot" and group_by == "Combined":
                    xfield = "Value"
                    yfield = "Expiration"
                    sns.barplot(
                        ax=ax,
                        data=plotdf.sort_values("Expiration"),
                        x=xfield,
                        y=yfield,
                        hue="Price Type"
                    )
                    for xtl in ax.get_xticklabels():
                        xtl.set_rotation(90)
                    #if "Title" in display_options:
                    #    ax.set_title("Contract count by expiration")
                    #if "Tight Layout" in display_options:
                    #    fig.tight_layout()
                    for container in ax.containers:
                        ax.bar_label(container)
            stplot_con.pyplot(fig)



def __get_outstanding_premium_by_expiration(conf: Config):
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    acc_json = client.get_account(conf.accountnum, fields=[fb.FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    p = {}
    d = []
    #df = pd.DataFrame()
    #df.columns = ['exp', 'ptype', 'count']
    for pentry in positions:
        pins = pentry['instrument']
        if pins['assetType'] == "OPTION":
            sym_split = pentry["instrument"]['symbol'].split("_")
            raw = sym_split[1][0:6]
            raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
            if raw_exp not in p:
                p[raw_exp] = {
                    "Current Mark": 0.0,
                    "Opening Price": 0.0
                }
            quantity = None
            longshort = None
            ctype = None
            mark = None
            openval = None
            if pentry['longQuantity'] > 0:
                quantity = pentry['longQuantity']
                longshort = "long"
                mark = abs(pentry['marketValue'])
                openval = quantity * pentry['averagePrice']*100
                ctype = pentry["instrument"]['putCall']
            elif pentry['shortQuantity'] > 0:
                quantity = pentry['shortQuantity']
                longshort = "short"
                mark = abs(pentry['marketValue'])
                openval = quantity * pentry['averagePrice']*100
                ctype = pentry["instrument"]['putCall']

            e = [raw_exp, quantity, longshort, ctype, "Mark", mark]
            d.append(e)
            e = [raw_exp, quantity, longshort, ctype, "Opening Price", openval]
            d.append(e)
            #p[raw_exp]['Current Mark'] += abs(pentry['marketValue'])
            #p[raw_exp]['Opening Price'] += (
            #    (pentry['longQuantity'] + pentry['shortQuantity']) * pentry['averagePrice']*100
            #)
    #for exp in p:
    #    for ptype in p[exp]:
    #        d.append([exp, ptype, p[exp][ptype]])
    #df = pd.DataFrame.from_dict(p, orient='columns')
    df = pd.DataFrame(d)
    df.columns = ['Expiration', 'Quantity', 'Longshort', "Contract Type", "Price Type", 'Value']
    return df
    #print(df.head())

def get_otm_df():
    global CONFIG
    conf = CONFIG
    #print(conf)
    df = dataccess.get_otm_df(conf)
    df['expiration'] = "000101"
    for idx in df.index:
        sym = df.loc[idx,'symbol']
        raw = sym.split("_")[1][0:6]
        raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
        df.loc[idx, 'expiration'] = raw_exp
    return df.drop(columns='symbol')


def get_daily_premium_sold(STARTDATE=None):
    global CONFIG
    conf = CONFIG
    pmtlt_conn = dataccess.get_pmtlt_db_conn()
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



fig = None
ax = None
table = None


main_select_con = st.container()
with main_select_con:
#with st.container():
    plot_what = st.selectbox(
        "Plot what?",
        (
            "None",
            "Percent OTM",
            "Open Contracts",
            "Outstanding Premium",
            "Daily Premium"
        ),
        index=0
    )
st.write("Moop")
data_config_expander = st.expander(
    "Configuration",
    expanded=True
)
data_show_container = st.container()
plot_tuning_expander = st.expander("Plot Tuning Options")
notes_expander = st.expander("Plot notes")
with data_config_expander:
    if plot_what == "Daily Premium":
        days_back_str = st.text_input(
            "How many days back?",
            "14"
        )
        plot_by = st.selectbox(
            "Show daily premium by?",
            (
                "Date",
            ),
            index=0
        )
        plot_type = st.selectbox(
            "How to view daily premium?",
            (
                "Table",
                "Barplot",
                "Regplot"
            ),
            index=0
        )
        days_back = datetime.today() - timedelta(days=int(days_back_str))

    elif plot_what == "Percent OTM":
        plot_by = st.selectbox(
            "Show - Percent OTM by?",
            (
                "None",
                "Table",
                "Total",
                "By Expiration and type"
            )
        )
    elif plot_what == "Open Contracts":
        plot_open_contracts(data_config_expander, data_show_container, CONFIG)
    elif plot_what == "Outstanding Premium":
        plot_outstanding_premium(data_config_expander, data_show_container, CONFIG)
    elif plot_what == "fase":

        by_index = 0
        plot_by = st.selectbox(
            "Plot - Outstanding premium By?",
            (
                "Expiration",
            ),
            index=0
        )
        if plot_by == "Expiration":
            type_index = 0
        plot_type = st.selectbox(
            "Plot - Outstanding Premium by expiration how?",
            (
                "Barplot",
                "Table"
            ),
            index=type_index
        )
        if plot_type == "Barplot":
            hue_set = st.selectbox(
                "Measures to show",
                (
                    "All",
                    "Opening Price",
                    "Current Mark"
                ),
                index=0
            )
## End select box expander
