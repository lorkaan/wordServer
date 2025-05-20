import os

def getEnviron(environ_var, default_val):
    try:
        cur_var = os.environ[environ_var]
    except KeyError as e:
        cur_var = None
    if type(cur_var) == str and len(cur_var) > 0:
        return cur_var
    else:
        return default_val

def getEnvironArray(var_name, delimiter=","):
    arr = getEnviron(var_name, "").split(delimiter)
    for val in arr:
        if len(val) == 0:
            arr.remove(val)
        else:
            continue
    return arr