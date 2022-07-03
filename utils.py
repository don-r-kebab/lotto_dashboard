#!/usr/bin/env python3

def flatten_positions(pjson):
    for pdict in pjson:
        for k in pdict['instrument']:
            pdict[k] = pdict['instrument'][k]
        del(pdict['instrument'])
    #print(json.dumps(pdict[k], indent=4))
    return