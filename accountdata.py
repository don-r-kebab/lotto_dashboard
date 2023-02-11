from datastructures import Config
from tda.client import Client as TDAclient
import json


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

    def calc_account_data(self, client: TDAclient, conf: Config):
        try:
            acc_data = client.get_account(conf.accountnum).json()
            acc = acc_data['securitiesAccount']
        except KeyError as ke:
            print(json.dumps(acc))
            raise
        self.nlv = acc['currentBalances']['liquidationValue']
        self.bp_available = acc['currentBalances']['buyingPowerNonMarginableTrade']
        self.bpu = 1 - (self.bp_available / float(self.nlv))
        self.bpu = round(self.bpu * 100, 2)

        self.starting_nlv = acc['initialBalances']['liquidationValue']
        self.starting_bp = acc['initialBalances']['buyingPower']
        self.starting_bpu = 1 - self.starting_bp / float(self.starting_nlv)
        self.starting_bpu = round(self.starting_bpu * 100, 2)

        self.sutmax = int((self.nlv / float(1000))) * 5

    def to_dataframe(self, index_label: str = "Stats"):
        pass
