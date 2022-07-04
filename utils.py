#!/usr/bin/env python3

def flatten_positions(pjson):
    for pdict in pjson:
        for k in pdict['instrument']:
            pdict[k] = pdict['instrument'][k]
        del(pdict['instrument'])
    #print(json.dumps(pdict[k], indent=4))
    return

def check_streamlit():
    """
    Function to check whether python code is run within streamlit

    Returns
    -------
    use_streamlit : boolean
        True if code is run within streamlit, else False
    """
    try:
        from streamlit.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except ModuleNotFoundError:
        return False

