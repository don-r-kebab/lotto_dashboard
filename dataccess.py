
import tda
import json
from tda.client import Client as TDAclient
import utils
import pandas as pd
from datastructures import Config
from datetime import datetime, time

ACCOUNT_FIELDS = tda.client.Client.Account.Fields

def get_otm_df(conf: Config):
    try:
        client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
        position_data = get_positions_json(config=conf)
        utils.flatten_positions(position_data)
        pdf = pd.DataFrame(position_data)
        pdf['spotPrice'] = 0
        symbols = pdf.loc[pdf['underlyingSymbol'].notnull(), 'underlyingSymbol'].unique()
    except Exception as e:
        raise e
    try:
        quotesj = client.get_quotes(symbols).json()
        curr_price = {}
        for ticker in quotesj:
            tdata = quotesj[ticker]
            curr_price[ticker] = tdata['lastPrice']
            pdf.loc[pdf['underlyingSymbol']==ticker, 'spotPrice'] = tdata['lastPrice']
    except Exception as e:
        raise e
    #print(json.dumps(quotes.json(), indent=4))
    #print(pdf.head())
    pdf['quantity'] = (pdf['longQuantity'] - pdf['shortQuantity'])
    pdf['currentValue'] = (pdf['marketValue']/abs(pdf['quantity']))/100
    pdf['pnl'] = pdf['averagePrice']/pdf['currentValue']
    pdf['otm'] = -1

    pdf['percentChange'] = (pdf['averagePrice']+pdf['currentValue'])/pdf['averagePrice']*100
    pdf['strikePrice'] = pdf['symbol'].str.split("_", expand=True).iloc[:,1].str.slice(start=7).astype(float)
    # This is me wrestling with datetime in matrix form to calculate dte
    #pdf['emonth'] = pdf['symbol'].str.split("_", expand=True).iloc[:, 1].str.slice(start=0, stop=1).astype(int)
    #pdf['eday'] = pdf['symbol'].str.split("_", expand=True).iloc[:, 1].str.slice(start=2, stop=3).astype(int)
    #pdf['eyear'] = pdf['symbol'].str.split("_", expand=True).iloc[:, 1].str.slice(start=4, stop=5).astype(int)
    pdf['ctype'] = pdf['symbol'].str.split("_", expand=True).iloc[:, 1].str.slice(start=6, stop=7).astype(str)
    #pdf['edate'] = pd.to_datetime(pdf['symbol'].str.split("_", expand=True).iloc[:,1].str.slice(start=0, stop=6), format='%m%d%y', errors='ignore')
    #pdf['dte'] = (pdf['edate']-datetime.date.today()).dt.days
    pdf['otm'] = abs((pdf['strikePrice']/pdf['spotPrice'])-1)
    subdf = pdf.loc[
        (pdf['assetType']=="OPTION")
        & (pdf['quantity'] < 0),
        [
            'underlyingSymbol',
            "symbol",
            'description',
            'quantity',
            'averagePrice',
            'currentValue',
            'ctype',
            'strikePrice',
            #'percentChange',
            'spotPrice',
            'otm'
        ]
    ].sort_values(['otm'])
    return subdf

def get_positions_json(config: Config):
    client = tda.auth.easy_client(config.apikey, config.callbackuri, config.tokenpath)
    acc_json = client.get_account(config.accountnum, fields=[ACCOUNT_FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    return positions

def get_pmtlt_db_conn():
    from appdirs import user_data_dir, user_config_dir
    from pathlib import Path
    import sqlalchemy
    #global CONFIG
    #conf = CONFIG
    PACKAGE_NAME = "pmtlottotracker"
    AUTHOR = "PMTraders"
    CONFIG_DIR = user_config_dir(appname=PACKAGE_NAME, appauthor=AUTHOR)
    CONFIG_PATH = Path(CONFIG_DIR, "config.toml")
    DATA_DIR = user_data_dir(appname=PACKAGE_NAME, appauthor=AUTHOR)
    DB_PATH = Path(DATA_DIR, "Lotto-Tracker.db")
    uri = "sqlite:///{}".format(DB_PATH)
    #print(uri)
    conn = sqlalchemy.create_engine(uri)
    #print(conn)
    return conn

def get_order_count(client: TDAclient, conf: Config):
    ocount = 0
    TODAY = datetime.today()
    bod = datetime.combine(TODAY, time.min)
    eod = datetime.combine(TODAY, time.max)
    orders = client.get_orders_by_path(
        conf.accountnum,
        to_entered_datetime=eod,
        from_entered_datetime=bod
    )
    orders = json.loads(orders.text)
    for order in orders:
        et = order['enteredTime']
        submit_time = datetime.strptime(et, "%Y-%m-%dT%H:%M:%S%z")
        if submit_time.date()==TODAY:
            ocount += 1
    return ocount

def get_premium_today(client: TDAclient, config: Config):
    TODAY = datetime.today()
    bod = datetime.combine(TODAY, time.min)
    eod = datetime.combine(TODAY, time.max)
    orders = client.get_orders_by_path(
        config.accountnum,
        to_entered_datetime=eod,
        from_entered_datetime=bod
    )
    orders = json.loads(orders.text)
    t = 0
    for order in orders:
        try:
            ot = order['orderType']
            if ot == "TRAILING_STOP":
                continue
            price = order['price']
            quant = order['filledQuantity']
            tot = price * quant
            olc = order['orderLegCollection']
            if olc[0]['orderLegType'] != "OPTION":
                continue
            pe = None
            cot = order['complexOrderStrategyType']
            if cot == "NONE":
                for olcd in olc:
                    pe = olcd['positionEffect']
                    instruct = olcd['instruction']
                    if instruct == "SELL_TO_OPEN":
                        pass
                    elif instruct == "BUY_TO_OPEN":
                        tot *= -1
                    elif instruct == "SELL_TO_CLOSE":
                        pass
                    elif instruct == "BUY_TO_CLOSE":
                        tot *= -1
            else:
                ot = order['orderType']
                if ot == "NET_DEBIT":
                    tot *= -1
                elif ot == "NET_CREDIT":
                    pass
                else:
                    raise Exception("invalid order found {}".format(json.dumps(order, indent=4)))
            t += tot
        except Exception as e:
            print(order)
            print(e)
            pass
    #print(json.dumps(orders, indent=4))
    return t

def sut_test(pjson, sutmax=-1):
    res = []
    unweighed_calc = {
        'CALL_COUNT': 0,
        'CALL_REMAINING': sutmax,
        'CALL_PCT_USED': 0,
        'PUT_COUNT': 0,
        'PUT_REMAINING': sutmax,
        'PUT_PCT_USED': 0,
        "type": "unweighted"
    }
    #print(json.dumps(unweighed_calc, indent=4))
    for pos in pjson:
        p_ins = pos['instrument']
        if p_ins['assetType'] != "OPTION":
            continue
        try:
            otype = pos['instrument']['putCall']
            count_type = otype  + "_COUNT"
            remaining_type =  otype + "_REMAINING"
        except KeyError as ke:
            print(json.dumps(pos, indent=4))
            print(ke)
            raise ke
        unweighed_calc[count_type] -= pos['shortQuantity']
        unweighed_calc[count_type] += pos['longQuantity']
        unweighed_calc[remaining_type] -= pos['shortQuantity']
        unweighed_calc[remaining_type] += pos['longQuantity']
    #print(unweighed_calc)
    if unweighed_calc["CALL_REMAINING"] > sutmax:
        unweighed_calc["CALL_REMAINING"] = sutmax
    if unweighed_calc["PUT_REMAINING"] > sutmax:
        unweighed_calc["PUT_REMAINING"] = sutmax
    unweighed_calc["CALL_PCT_USED"] = -1*round((unweighed_calc['CALL_COUNT']/sutmax)*100, 2)
    unweighed_calc["PUT_PCT_USED"] = -1*round((unweighed_calc['PUT_COUNT']/sutmax)*100, 2)
    res.append(unweighed_calc)
    return res