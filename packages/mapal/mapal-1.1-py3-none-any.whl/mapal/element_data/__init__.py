"""
mapal.element_data
---------------------------------------
Package to access element data from the in-built element database.
Two keys (property key and element key) are required to query any value from the database.

List of functions:
---------------------------------------
el_properties_list : generates list of all 'property keys' available in the in-built element database
el_prop_info : prints information about a property key
get_el_property : returns queried element property
"""

# --- Import mapal modules ---
import mapal;

# --- Import Python built-in libraries ---
import os;
import json;

SEP = os.sep;


# -----------------------------------------------
def load_element_database(database_to_use = "mapal_EL1"):
    
    """loads element database and its information file
    
    Parameters
    ----------
    database_to_use : str (default="mapal-element-database")
        element database source directory. Users can create customized database directories.
        
    Returns
    ----------
    dict_db_el : dict
        dictionary containing element database
    dict_db_el_info : dict
        dictionary containing information about properties included in element database
    """
    
    ref_dir = os.path.abspath(mapal.element_data.__file__).split("__init__.py")[0];
    
    db_el_filepath = f"{ref_dir}{database_to_use}{SEP}db_element.json";
    db_el_info_filepath = f"{ref_dir}{database_to_use}{SEP}db_element_info.json";
    
    with open(db_el_filepath, 'r', encoding="latin-1") as f:
        dict_db_el = json.load(f);
        
    with open(db_el_info_filepath, 'r', encoding="latin-1") as f:
        dict_db_el_info = json.load(f);
    
    return (dict_db_el, dict_db_el_info);



# -----------------------------------------------
def el_properties_list(database_to_use = "mapal_EL1"):
    
    """generates the list of all 'property keys' available in the in-built element database

    Parameters
    ----------
    database_to_use : str (default="mapal_EL1")
        element database source directory. Users can create customized database directories.
    
    Returns
    ----------
    el_prop_keys : list
        a list of all property keys available in built-in element database
    """
    
    dict_db_el, dict_db_el_info = load_element_database(database_to_use);
    el_prop_keys = list(dict_db_el_info.keys());

    return (el_prop_keys);



# -----------------------------------------------
def el_prop_info(prop_key, database_to_use = "mapal_EL1"):
    
    """prints information about an element property key

    Parameters
    ----------
    prop_key : str
        'property key' for which information is needed
    database_to_use : str (default="mapal_EL1")
        element database source directory. Users can create customized database directories.
    
    Returns
    ----------
        prints information on console
    """
    
    dict_db_el, dict_db_el_info = load_element_database(database_to_use);

    if prop_key in list(dict_db_el_info.keys()):

        print("\n---Generated information about '%s' property key---" % (prop_key));
        print("Property key:", prop_key);
        
        for info_key in list(dict_db_el_info[prop_key].keys()):
            print("%s: %s" % (info_key, dict_db_el_info[prop_key][info_key]));

        print("------------------------\n");

    else:
        print("Property key '%s' does not exist in database." % (prop_key));
        
    return (None);



# -----------------------------------------------
def get_el_property(el, prop_key, database_to_use = "mapal_EL1"):

    """get property of an element from built-in element database

    Parameters
    ----------
    el : str
        'element key' for which property is needed e.g., “Al” or “Fe”
    prop_key : str
        'property key' to be searched e.g., "EN_Allen" or "VEC"
    database_to_use : str (default="mapal_EL1")
        element database source directory. Users can create customized database directories.
    
    Returns
    ----------
    el_prop : str/float/int (depening on property)
        value of property queried from element database
    """
    
    dict_db_el, dict_db_el_info = load_element_database(database_to_use);

    if (el in list(dict_db_el.keys())) and (prop_key in list(dict_db_el_info.keys())):
        el_prop = dict_db_el[el][prop_key];
        return (el_prop);

    elif (el in list(dict_db_el.keys())) and (prop_key not in list(dict_db_el_info.keys())):
        raise ValueError("Property key '%s' does not exist in database." % (prop_key));
        return (None);
    
    elif (el not in list(dict_db_el.keys())) and (prop_key in list(dict_db_el_info.keys())):
        raise ValueError("Element '%s' not in database." % (el));
        return (None);

    else:
        raise ValueError("Element '%s' and property '%s' not in database." % (el, prop_key));
        return (None);