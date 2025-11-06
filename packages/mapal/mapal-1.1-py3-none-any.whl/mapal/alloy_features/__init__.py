"""
mapal.alloy_features
---------------------------------------
Package to create various alloy features

List of functions:
---------------------------------------
list_operators : return list of operators available to mutate elemental properties to alloy features
list_features : return list of alloy features available
get_feat_value : returns the value of a feature for a list of alloys
get_comp_dict : creates 'dictionary' with alloy composition from alloy name string
get_comp_avg : calculates composition-weighted average value of any feature for an alloy
get_asymmetry : calculates composition-weighted asymmetry value of any feature for an alloy
get_local_mismatch : calculates local-mismatch value of any feature for an alloy
get_sqdiff : calculates composition-weighted average of square-difference value of any feature for an alloy
get_S_config : calculates configurational entropy of mixing for an alloy
get_Singh_parameter : calculates geometrical parameter proposed by Singh et al. for multicomponent alloys
get_Wang_parameter : calculates Wang's geometrical solid-angle ratio parameter proposed by Wang et al. for multicomponent alloys
get_modulus_mismatch : calculates modulus mismatch parameter for an alloy
get_latt_dist_energy : calculates lattice distortion energy parameter for an alloy
get_energy_strength_model : calculates energy term used in strengthening model
get_Peierl_Nabarro_factor : calculates Peierls-Nabarro factor
"""

# --- Import Python add-on libraries ---
import numpy as np;
import re

# --- Import mapal packages ---
import mapal;



# -----------------------------------------------
def list_operators():

    """print list of operator keys available to mutate elemental properties into alloy features

    Parameters
    ----------
    no inputs required

    Returns
    ----------
    op_list : list
        list of operators available
    """

    op_list = ["comp_avg", "asymmetry", "local_mismatch", "sqdiff", "modulus_mismatch"];


    return (op_list);



# -----------------------------------------------
def list_features():

    """return list of alloy features available

    Parameters
    ----------
    no inputs required

    Returns
    ----------
    feat_list : list
        list of features available
    """

    feat_list = ["S_config", "Singh_parameter", "Wang_parameter", "latt_dist_energy",
                 "energy_strength_model", "Peierl_Nabarro_factor"];


    return (feat_list);



# -----------------------------------------------
def get_feat_value(alloy_list, feature, verbose=1):

    """return list of feature values for a list of alloys

    Parameters
    ----------
    alloy_list : str/list/array
        list of alloy names
    feature : str/tuple
        feature to be calculated, can be either a feature string (e.g. “S_config”) 
        or (operator, el_prop) tuple e.g. (”comp_avg”, “VEC”)
    verbose : int (default=1)
        Set verbose=0 to stop calculation messages from being printed in terminal

    Returns
    ----------
    feat_val_list : list
        list of feature values
    """

    if type(feature) == tuple:
        (operator, el_prop) = feature;
        feat_name = "%s_%s" % (operator, el_prop);
        if verbose == 1:
            print("Calculating '%s' feature values..." % (feat_name), end="  ");
        func = getattr(mapal.alloy_features, "get_" + operator);
        feat_val_list = func(alloy_list, el_prop);
        
    else:
        feat_name = feature;
        if verbose == 1:
            print("Calculating '%s' feature values..." % (feat_name), end="  ");
        func = getattr(mapal.alloy_features, "get_" + feature);
        feat_val_list = func(alloy_list);
    
    if verbose == 1:
        print("DONE.");
    

    return (feat_val_list);



# -----------------------------------------------
def get_comp_dict(alloy_name):
	
    """generates compositions for a binary system with two components.

    Parameters
    ----------
    alloy_name : str
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”

    Returns
    ----------
    dict_alloy_comp : dict
        composition dict with two keys:
            “el_list”: list of elements in alloys
            “el_at_frac_list”: list of atomic fraction of each element in alloy
    """

    exclude = set("() {}[]''/,;:?\|~`@#$%&^*-_");
    alloy_name = ''.join(ch for ch in alloy_name if ch not in exclude);

    # split string wherever capital letter is found
    el_stoich_pairs_list = re.findall("[A-Z][^A-Z]*", alloy_name);
    el_list = [];
    el_stoich_list = [];

    # from each 'el_stoich_pair' extract element name and stoichiometry
    for el_stoich_pair in el_stoich_pairs_list:
        el = "".join(ch for ch in el_stoich_pair if (not ch.isdigit() and ch != "."));
        stoich = "".join(ch for ch in el_stoich_pair if (ch.isdigit() or ch == "."));
        if stoich == "":
            stoich = float(1);
        el_list.append(el);
        el_stoich_list.append(float(stoich));

    # creating atomic fractions
    stoich_total = np.sum(el_stoich_list);
    el_at_frac_list = list(np.around(np.array(el_stoich_list)/stoich_total, 4));

    # sort with elements arranged in alphabetical order
    tuples = zip(*sorted(zip(el_list, el_at_frac_list)));
    el_list_sort, el_at_frac_list_sort = [list(tuple) for tuple in tuples];

    dict_alloy_comp = {
        "el_list": el_list_sort,
        "el_at_frac_list": el_at_frac_list_sort
    };


    return (dict_alloy_comp);



# -----------------------------------------------
def get_comp_avg(alloy_name, feat_key):

    """calculates composition-weighted average value of any feature for an alloy

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”
    feat_key : str
        feature key e.g. "r_cov" or "EN_Allen"

    Returns
    ----------
    avg_feat : float/list
        composition-weighted average value of feature
    """
    
    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];
        
    list_avg_feat = [];
    
    for alloy in alloy_name:
        alloy = str(alloy);
        dict_alloy_comp = get_comp_dict(alloy);
        el_list = dict_alloy_comp["el_list"];
        el_prop_list = [mapal.element_data.get_el_property(el, feat_key) for el in el_list];
        c_el_list = dict_alloy_comp["el_at_frac_list"];
        
        avg_feat = 0;
        
        for (c_el, el_prop) in zip(c_el_list, el_prop_list):
            avg_feat += (c_el * el_prop);
        
        list_avg_feat.append(avg_feat);

    if input_type == str:
        return (list_avg_feat[0]);
    else:
        return (list_avg_feat);



# -----------------------------------------------
def get_asymmetry(alloy_name, feat_key):

    """calculates composition-weighted asymmetry value of any feature for an alloy

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”
    feat_key : str
        feature key e.g. "r_cov" or "EN_Allen"

    Returns
    ----------
    asymm_feat : float/list
        composition-weighted asymmetry value of feature
    """
    
    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];
        
    list_asymm_feat = [];

    for alloy in alloy_name:
        alloy = str(alloy);
        dict_alloy_comp = get_comp_dict(alloy);
        el_list = dict_alloy_comp["el_list"];
        el_prop_list = [mapal.element_data.get_el_property(el, feat_key) for el in el_list];
        c_el_list = dict_alloy_comp["el_at_frac_list"];
        
        avg_feat = get_comp_avg(alloy, feat_key);
        asymm_feat_sum = 0;  # summation term inside the square root

        for (c_el, el_prop) in zip(c_el_list, el_prop_list):
            asymm_feat_sum += (c_el * (1-(el_prop/avg_feat))**2);

        asymm_feat = (asymm_feat_sum)**(0.5);
        
        list_asymm_feat.append(asymm_feat);
    
    
    if input_type == str:
        return (list_asymm_feat[0]);
    else:
        return (list_asymm_feat);



# -----------------------------------------------
def get_local_mismatch(alloy_name, feat_key):

    """calculates local-mismatch value of any feature for an alloy

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”
    feat_key : str
        feature key e.g. "r_cov" or "EN_Allen"

    Returns
    ----------
    loc_mismatch_feat : float/list
        local-mismatch value of feature for alloy
    """

    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];
	
    
    list_loc_mismatch_feat = [];

    for alloy in alloy_name:
        alloy = str(alloy);
        dict_alloy_comp = get_comp_dict(alloy);
        el_list = dict_alloy_comp["el_list"];
        el_prop_list = [mapal.element_data.get_el_property(el, feat_key) for el in el_list];
        c_el_list = dict_alloy_comp["el_at_frac_list"];

        n_element = len(el_list);
        loc_mismatch_feat = 0;
                    
        for i in range(0, n_element - 1):              # j represents first element in binary; say A
            for j in range(i + 1, n_element):          # k represents second element in binary; say B: j=0-> k=1,2,3,4 :: j=1->k=2,3,4 ::j =2->

                loc_mismatch_feat += ((c_el_list[i] * c_el_list[j])*abs(el_prop_list[i] - el_prop_list[j]));
        
        list_loc_mismatch_feat.append(loc_mismatch_feat);

    if input_type == str:
        return (list_loc_mismatch_feat[0]);
    else:
        return (list_loc_mismatch_feat);
        


# -----------------------------------------------
def get_sqdiff(alloy_name,feat_key):

    """calculates composition-weighted square-difference value of any feature for an alloy

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”
    feat_key : str
        feature key e.g. "r_cov" or "EN_Allen"

    Returns
    ----------
    sqDiff_feat : float/list
        composition-weighted square-difference value of feature for alloy
    """
    
    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];

    list_sqDiff_feat = [];

    for alloy in alloy_name:
        alloy = str(alloy);
        dict_alloy_comp = get_comp_dict(alloy);
        el_list = dict_alloy_comp["el_list"];
        el_prop_list = [mapal.element_data.get_el_property(el, feat_key) for el in el_list];
        c_el_list = dict_alloy_comp["el_at_frac_list"];

        avg_feat = get_comp_avg(alloy, feat_key);
        sqDiff_feat_sum = 0; # summation term inside the square troot
        
        for (c_el, el_prop) in zip(c_el_list, el_prop_list):
            sqDiff_feat_sum += (c_el * ((el_prop - avg_feat)**2));

        sqDiff_feat = sqDiff_feat_sum**0.5;
        
        list_sqDiff_feat.append(sqDiff_feat);
        
    if input_type == str:
        return (list_sqDiff_feat[0]);
    else:
        return (list_sqDiff_feat);



# -----------------------------------------------
def get_modulus_mismatch(alloy_name, modulus_key):

    """calculates modulus mismatch parameter for an alloy

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”
    modulus_key : str
        modulus key: “E”-Youngs modulus, “G”-Shear modulus and “K”-Bulk modulus

    Returns
    ----------
    mod_mismatch : float/list
        modulus mismatch parameter for an alloy
    """


    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];

    list_mod_mismatch = [];

    for alloy in alloy_name:
        alloy = str(alloy);
        dict_alloy_comp = get_comp_dict(alloy);
        el_list = dict_alloy_comp["el_list"];
        el_mod_list = [mapal.element_data.get_el_property(el, modulus_key) for el in el_list];
        c_el_list = dict_alloy_comp["el_at_frac_list"];

        mod_avg = get_comp_avg(alloy, modulus_key);
        mod_mismatch = 0;
        
        for (c_el, el_mod) in zip(c_el_list, el_mod_list):
            term1 = 2 * c_el * (el_mod - mod_avg)/(el_mod + mod_avg);
            term2 = 1 + (0.5 * (abs(term1)));
            mod_mismatch += (term1/term2);

        list_mod_mismatch.append(mod_mismatch);

    if input_type == str:
        return (list_mod_mismatch[0]);
    else:
        return (list_mod_mismatch);



# -----------------------------------------------
def get_S_config(alloy_name):

    """calculates composition-weighted square-difference value of any feature for an alloy

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”

    Returns
    ----------
    S_config : float/list
        configurational entropy of mixing for alloy (units: kJ/K.mol)
    """

    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];


    list_S_config = [];

    for alloy in alloy_name:
        alloy = str(alloy);
        dict_alloy_comp = get_comp_dict(alloy);
        c_el_list = dict_alloy_comp["el_at_frac_list"];

        R = 0.008314; # kJ/(Kelvin.mole)
        S_config = 0;
        
        for c_el in c_el_list:
            if c_el != 0:
                S_config -= (R * c_el * np.log(c_el));
        
        list_S_config.append(S_config);
        
    if input_type == str:
        return (list_S_config[0]);
    else:
        return (list_S_config);


# -----------------------------------------------
def get_Singh_parameter(alloy_name):

    """calculates geometrical parameter proposed by Singh et al. for multicomponent alloys

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”

    Returns
    ----------
    Singh_param : float/list
        value of Singh's geometrical parameter
    """
    
    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];


    list_Singh_param = [];

    for alloy in alloy_name:
        alloy = str(alloy);
        S_config = get_S_config(alloy);
        asymm_r = get_asymmetry(alloy,"r_met");
        Singh_param = S_config / (asymm_r**2);

        list_Singh_param.append(Singh_param);
        
    if input_type == str:
        return (list_Singh_param[0]);
    else:
        return (list_Singh_param);


# -----------------------------------------------
def get_Wang_parameter(alloy_name):

    """calculates Wang's geometrical solid-angle ratio parameter proposed by Wang et al. for multicomponent alloys

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”

    Returns
    ----------
    wang_param : float/list
        value of Wang's geometrical parameter
    """
    
    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];
        
    list_wang_param = [];
    
    for alloy in alloy_name:
        alloy = str(alloy);
        dict_alloy_comp = get_comp_dict(alloy);
        el_list = dict_alloy_comp["el_list"];
        el_r_list = [mapal.element_data.get_el_property(el, "r_met") for el in el_list];

        r_avg = get_comp_avg(alloy, "r_met");
        r_min = np.min(el_r_list);
        r_max = np.max(el_r_list);
        wS = 1 - (((r_min + r_avg)**2 - r_avg**2)/((r_min + r_avg)**2))**0.5;
        wL = 1 - (((r_max + r_avg)**2 - r_avg**2)/((r_max + r_avg)**2))**0.5;
        wang_param = wS / wL;

        list_wang_param.append(wang_param);
        
    if input_type == str:
        return (list_wang_param[0]);
    else:
        return (list_wang_param);


# -----------------------------------------------
def get_latt_dist_energy(alloy_name):

    """calculates lattice distortion energy parameter for an alloy

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”

    Returns
    ----------
    latt_dist_energy : float/list
        lattice distortion energy parameter
    """

    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];
        
        
    list_latt_dist_energy = [];

    for alloy in alloy_name:
        alloy = str(alloy);
        E_avg = get_comp_avg(alloy, "E");
        asymm_r = get_asymmetry(alloy, "r_met");
        latt_dist_energy = 0.5 * E_avg * asymm_r;

        list_latt_dist_energy.append(latt_dist_energy);
        
    if input_type == str:
        return (list_latt_dist_energy[0]);
    else:
        return (list_latt_dist_energy);    


# -----------------------------------------------
def get_energy_strength_model(alloy_name):

    """calculates energy term used in strengthening model

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”

    Returns
    ----------
    energy_term : float/list
        energy term value
    """

    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];
 
    list_energy_term = [];

    for alloy in alloy_name:
        alloy = str(alloy);
        poiss_no_avg = get_comp_avg(alloy, "poisson_num");
        G_avg = get_comp_avg(alloy, "G");
        asymm_r = get_asymmetry(alloy, "r_met");
        energy_term = G_avg * asymm_r * ((1 + poiss_no_avg) / (1 - poiss_no_avg));

        list_energy_term.append(energy_term);
        
    if input_type == str:
        return (list_energy_term[0]);
    else:
        return (list_energy_term);



# -----------------------------------------------
def get_Peierl_Nabarro_factor(alloy_name):

    """calculates Peierls-Nabarro factor

    Parameters
    ----------
    alloy_name : str/list/array
        alloy name string e.g. “NiAl2”, “BaTiO3”, “Al1.5Ti0.25CrFeNi”

    Returns
    ----------
    PN_factor : float/list
        Peierls-Nabarro factor
    """
    
    input_type = type(alloy_name);
    
    #if single alloy name entered as input, convert it to a list
    if type(alloy_name) == str:
        alloy_name = [alloy_name];
    
    list_PN_factor = [];

    for alloy in alloy_name:
        alloy = str(alloy);
        poiss_no_avg = get_comp_avg(alloy, "poisson_num");
        G_avg = get_comp_avg(alloy, "G");
        PN_factor = 2 * (G_avg / (1 - poiss_no_avg));

        list_PN_factor.append(PN_factor);
        
    if input_type == str:
        return (list_PN_factor[0]);
    else:
        return (list_PN_factor);