#!/usr/bin/env python3
import sys
import json
import argparse
import tda
from datastructures import Config

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
    ap.add_argument("--tdaconfig", dest="tdaconfig", default="tda-config.json")
    ap.add_argument("--nosetup", dest="nosetup", default=False, action="store_true")
    ap.add_argument("--configfile", dest='configfile', default="config.json")
    args = vars(ap.parse_args())
    c = Config()
    if ap['nosetup'] is False:
        setup(c, args['tdaconfig'], None)
    elif args['configfile'] is not None:
        c.read_config(args['configfile'])
    else:
        raise FileNotFoundError("Config file provided is None and \"--nosetup\" was specified")
    client = setup_client(c)
    res = client.get_account(c.accountnum)
    sys.exit(0)
