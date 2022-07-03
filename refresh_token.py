#!/usr/bin/env python3
import sys
import json
import argparse
import tda

class Config(object):
    def __init__(self):
        self.apikey = None
        self.callbackuri = None
        self.accountnum = None
        self.tokenpath = None

    def read_config(self, config_file):
        #print("Reading config")
        fh = open(config_file, 'r')
        c = json.load(fh)
        fh.close()
        self.apikey = c["apikey"]
        self.callbackuri = c["callbackuri"]
        self.tokenpath = c['tokenpath']
        self.accountnum = c['accountnum']

    def write_config(self, cfile):
        fh = open(cfile, 'w')
        fh.write(json.dumps(self.__dict__))
        fh.close()

    def __str__(self):
        return json.dumps(self.__dict__, indent=4)

def setup(conf: Config, tokenpath, cfile):
    cf = {}
    print("Let's setup the configuration!")
    print("What was your APPKEY?: ")
    conf.apikey = input()
    print("What is you callback URL?")
    conf.callbackuri = input()
    print("What is your primary account number?")
    conf.accountnum = input()
    print("conf.apikey", cf)
    conf.tokenpath = tokenpath
    #conf.write_config(cfile)


def setup_client(conf: Config):
    client = tda.auth.client_from_manual_flow(conf.apikey, conf.callbackuri, conf.tokenpath)
    return client



if __name__ == '__main__':
    print("Let's get a refresh token")
    ap = argparse.ArgumentParser()
    #ap.add_argument("--newtoken", action="store_true", dest='newtoken', default=False)
    ap.add_argument("--tdaconfig", dest="tdaconfig", default="refresh.json")
    ap.add_argument("--configfile", dest='configfile', default="config.json")
    args = vars(ap.parse_args())
    c = Config()
    if args['configfile'] is not None:
        c.read_config(args['configfile'])
    else:
        setup(c, args['tdaconfig'], None)
    client = setup_client(c)
    res = client.get_account(c.accountnum)
    sys.exit()
