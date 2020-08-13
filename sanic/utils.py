from os import environ as os_environ
from re import findall as re_findall
from importlib.util import spec_from_file_location, \
                           module_from_spec
from typing import Union



def str_to_bool(val):
    """Takes string and tries to turn it into bool as human would do.  

    If val is in case insensitive ("y", "yes", "yep", "yup", "t", "true", "on", "enable", "enabled", "1") returns True.  
    If val is in case insensitive ("n", "no", "f", "false", "off", "disable", "disabled", "0") returns False.  
    Else Raise ValueError."""

    val = val.lower()
    if val in ("y", "yes", "yep", "yup", "t", "true", "on", "enable", "enabled", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "disable", "disabled", "0"):
        return False
    else:
        raise ValueError("Invalid truth value %r" % (val,))



def load_module_from_file_location(name: str, location: Union[bytes, str], enc: str = "utf8", *args, **kwargs):
    """Returns loaded module provided as a file path.  
    
    :param name:  
        The same as importlib.util.spec_from_file_location name param.  
    :param args:  
        Coresponds to importlib.util.spec_from_file_location location parameters,  
        but with this differences:  
        - It has to be of a string or bytes type.  
        - You can also use here environment variables in format ${some_env_var}.  
          Mark that $some_env_var will not be resolved as environment variable.  
    :enc:  
        If location parameter is of a bytes type, then use this encoding to decode it into string.  
    :param args:  
        Coresponds to the rest of importlib.util.spec_from_file_location parameters.  
    :param kwargs:  
        Coresponds to the rest of importlib.util.spec_from_file_location parameters.  
    
    For example You can:  
    
        some_module = load_module_from_file_location("some_module_name", "/some/path/${some_env_var})"""
    
    # 1) Parse location.
    if isinstance(location, bytes):
        location = location.decode(enc)
    
    # A) Check if location contains any environment variables in format ${some_env_var}.
    env_vars_in_location = set(re_findall("\${(.+?)}", location))
    
    # B) Check these variables exists in environment.
    not_defined_env_vars = env_vars_in_location.difference(os_environ.keys())
    if not_defined_env_vars:
        raise Exception("The following environment variables are not set: " + ", ".join(not_defined_env_vars))  # TO ASK: Can we raise better exception type here ???
    
    # C) Substitute them in location.
    for env_var in env_vars_in_location:
        location = location.replace("${" + env_var + "}", os_environ[env_var])
    
    # 2) Load and return module.
    _mod_spec = spec_from_file_location(name, location, *args, **kwargs)
    module = module_from_spec(_mod_spec)
    _mod_spec.loader.exec_module(module)
    
    return module
