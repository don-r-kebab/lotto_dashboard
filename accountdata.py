import sqlalchemy.engine

from datastructures import Config


class AccountData(object):

    def __init__(self):
        self.nlv = 0
        self.bp = 0
        self.bp_available = 0
        self.bpu = 0
        self.starting_nlv = 0
        self.starting_bp = 0
        self.starting_bpu = 0.0
        self.sutmax = 0

    def reset(self):
        self.nlv = 0
        self.bp = 0
        self.bp_available = 0
        self.bpu = 0
        self.starting_nlv = 0
        self.starting_bp = 0
        self.starting_bpu = 0.0
        self.sutmax = 0

    def get_account_data(self, config: Config, api=False):
        if config is None:
            raise Exception("Unable to get account data, no config provided")
        if api is True:
            self._calc_account_data_api(config)
        else:
            self._calc_account_data_db()

    def _calc_account_data_api(self, conf: Config):
        import tda.auth
        from tda.client import Client as TDAclient
        client: TDAclient
        client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
        acc = client.get_account(conf.accountnum).json()['securitiesAccount']
        self.nlv = acc['currentBalances']['liquidationValue']
        self.bp_available = acc['currentBalances']['buyingPowerNonMarginableTrade']
        self.bpu = 1 - (self.bp_available / float(self.nlv))
        self.bpu = round(self.bpu * 100, 2)

        self.starting_nlv = acc['initialBalances']['liquidationValue']
        self.starting_bp = acc['initialBalances']['buyingPower']
        self.starting_bpu = 1 - self.starting_bp / float(self.starting_nlv)
        self.starting_bpu = round(self.starting_bpu * 100, 2)

        self.sutmax = int((self.nlv / float(1000))) * 5

    def _calc_account_data_db(self):
        import pmltdb
        from datetime import datetime
        import sqlalchemy
        conn: sqlalchemy.engine.Engine
        conn = pmltdb.db_conn()
        q = f"""
        SELECT date, nlv, buying_power, maintenance_requirement
        FROM account_info
        WHERE date == date({datetime.today()})
        """
        res = conn.connect().execute(q)
        for d in [dict(r) for r in res]:
            print(d)


    def to_dataframe(self, index_label: str = "Stats"):
        pass
