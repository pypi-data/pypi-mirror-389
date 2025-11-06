"""
mapal.create_alloys
---------------------------------------
Package to create alloys over user-defined compositional spaces including (binary), 
(ternary) and (ternary with 1 component fixed) 

List of functions:
---------------------------------------
binary : generates compositions for a binary system with two components
ternary : generates compositions for a ternary system with three components
ternary_1Cfixed : generates compositions for a ternary system where concentration of one component is fixed
equiatomic_alloys : generates all possible equiatomic compositions from a set of elements
all_possible_compositions : generates all possible compositions from given list of elements
"""

# --- Import Python built-in libraries ---
import re
from itertools import combinations

# --- Import Python add-on libraries ---
import numpy as np
import pandas as pd

# --- Import mapal packages ---
from mapal import alloy_features as af



# ---------------------------------------
def binary(A, B, dc = 0.01, cAmin = 0.0, cAmax = 1.0):

    """generates compositions for a binary system with two components.

    Parameters
    ----------
    A : str
        component 'A': an element (e.g. "Al" or "Fe") or a multicomponent system (e.g. "AlCo" or "CrFeNi")
    B : str
        component 'B': an element (e.g. "Al" or "Fe") or a multicomponent system (e.g. "AlCo" or "CrFeNi")
    dc : float (optional; default = 0.01; range (0,1))
        concentration step size (in atomic fraction)
    cAmin : float (optional; default = 0.0; range (0,1))
        min concentration of component A
    cAmax : float (optional; default = 1.0; range (0,1))
        max concentration of component A

    Returns
    ----------
    df_alloys : pandas dataframe
        dataframe with alloy names and compositions in atomic fractions of component A & B
    """

    print(" --------------------------------------- ", flush=True);
    print("Creating alloys for (%s)-(%s)..."%(A, B), end="  ", flush=True);

    A_comp_dict = af.get_comp_dict(A);
    B_comp_dict = af.get_comp_dict(B);

    # Creating composition array (col 0 and 1 contain atomic fraction of component A and B)
    xA = cAmin;
    xB = np.around((1 - xA), 3);
    comp_array = np.zeros(shape = (1, 2));
    comp_array[0, 0] = np.abs(xA);
    comp_array[0, 1] = np.abs(xB);

    while ((xA + dc) <= (cAmax + dc / 10) and
            (xA + dc) <= (1 + dc / 10)):
        
        xA = np.abs(np.around((xA + dc), 3));    # xA increased by dc in every loop
        xB = np.abs(np.around((1 - xA), 3));
        comp_row = np.array([[xA, xB]]);
        comp_array = np.vstack((comp_array, comp_row));
    
    # Creating alloy name for each composition
    alloy_name_list = [];
    all_el_list = sorted(A_comp_dict["el_list"] + B_comp_dict["el_list"]);
    x_el_dict = {el:[] for el in all_el_list};
    
    for comp in comp_array:
        alloy_name = "";
        for el in all_el_list:
            
            if el in A_comp_dict["el_list"]:
                el_stoich_in_A = A_comp_dict["el_at_frac_list"][A_comp_dict["el_list"].index(el)];
                el_at_frac = round(comp[0] * el_stoich_in_A, 3);
    
            if el in B_comp_dict["el_list"]:
                el_stoich_in_B = B_comp_dict["el_at_frac_list"][B_comp_dict["el_list"].index(el)];
                el_at_frac = round(comp[1] * el_stoich_in_B, 3);
            
            alloy_name += str(el) + str(el_at_frac);
            x_el_dict[el].append(el_at_frac);

        alloy_name_list.append(alloy_name);

    # Creating pandas dataframe with composition details
    n_alloys = len(alloy_name_list);
    
    df_alloys = pd.DataFrame();
    df_alloys["alloy_id"] = np.arange(1, n_alloys + 1, 1);
    df_alloys["alloy_name"] = np.array(alloy_name_list);
    df_alloys["xA[A=%s]"%(A)] = comp_array[:, 0];
    df_alloys["xB[B=%s]"%(B)] = comp_array[:, 1];
    
    for el in all_el_list:
        df_alloys["xEl[%s]"%(el)] = np.array(x_el_dict[el]);
    
    df_alloys = df_alloys.set_index("alloy_id");
    
    print("DONE.", flush=True);
    print(" --------------------------------------- ", flush=True);


    return (df_alloys);



# ---------------------------------------
def ternary(A, B, C, dc = 0.01):

    """generates compositions for a ternary system with three components.

    Parameters
    ----------
    A : str
        component 'A': an element (e.g. "Al") or a multicomponent system (e.g. "CrFe")
    B : str
        component 'B': an element (e.g. "Ti") or a multicomponent system (e.g. "CoNi")
    C : str
        component 'C': an element (e.g. "Zr") or a multicomponent system (e.g. "WMo")
    dc : float (optional; default = 0.01; range (0,1))
        concentration step size (in atomic fraction)

    Returns
    ----------
    df_alloys : pandas dataframe
        dataframe with alloy names and compositions in atomic fractions of component A, B & C
    """

    
    print(" --------------------------------------- ", flush=True);
    print("Creating alloys for (%s)-(%s)-(%s) ternary system..."%(A, B, C), end="  ", flush=True);

    A_comp_dict = af.get_comp_dict(A);
    B_comp_dict = af.get_comp_dict(B);
    C_comp_dict = af.get_comp_dict(C);
    
    alloy_comp_list = [];
    
    for cA in np.arange(0, 1 + dc/10, dc):
        for cB in np.arange(0, min(1, 1-cA) + dc/10, dc):
            cC = 1-cA-cB;
            
            alloy_comp_list.append([np.around(np.abs(cA),3),
                          np.around(np.abs(cB),3),
                          np.around(np.abs(cC),3)]);
    
    comp_array = np.array(alloy_comp_list);
    
    # Creating alloy name for each composition
    alloy_name_list = [];
    all_el_list = sorted(A_comp_dict["el_list"] + B_comp_dict["el_list"] + C_comp_dict["el_list"]);
    x_el_dict = {el:[] for el in all_el_list};
    
    for comp in comp_array:
        alloy_name = "";
        for el in all_el_list:
            
            if el in A_comp_dict["el_list"]:
                el_stoich_in_A = A_comp_dict["el_at_frac_list"][A_comp_dict["el_list"].index(el)];
                el_at_frac = round(comp[0] * el_stoich_in_A, 3);
    
            if el in B_comp_dict["el_list"]:
                el_stoich_in_B = B_comp_dict["el_at_frac_list"][B_comp_dict["el_list"].index(el)];
                el_at_frac = round(comp[1] * el_stoich_in_B, 3);
                
            if el in C_comp_dict["el_list"]:
                el_stoich_in_C = C_comp_dict["el_at_frac_list"][C_comp_dict["el_list"].index(el)];
                el_at_frac = round(comp[2] * el_stoich_in_C, 3);
            
            alloy_name += str(el) + str(el_at_frac);
            x_el_dict[el].append(el_at_frac);

        alloy_name_list.append(alloy_name);
        
    n_alloys = len(alloy_name_list);
    
    df_alloys = pd.DataFrame();
    df_alloys["alloy_id"] = np.arange(1, n_alloys + 1, 1);
    df_alloys["alloy_name"] = np.array(alloy_name_list);
    df_alloys["xA[A=%s]"%(A)] = comp_array[:, 0];
    df_alloys["xB[B=%s]"%(B)] = comp_array[:, 1];
    df_alloys["xC[C=%s]"%(C)] = comp_array[:, 2];

    for el in all_el_list:
        df_alloys["xEl[%s]"%(el)] = np.array(x_el_dict[el]);
    
    df_alloys = df_alloys.set_index("alloy_id");

    print("DONE.", flush=True);
    print(" --------------------------------------- ", flush=True);


    return (df_alloys);



# ---------------------------------------
def ternary_1Cfixed(A, B, C, Cfix, dc = 0.01, cAmin = 0, cAmax = "auto"):

    """generates compositions for a ternary system where concentration of one component is fixed

    Parameters
    ----------
    A : str
        component 'A': an element (e.g. "Al") or a multicomponent system (e.g. "CrFe")
    B : str
        component 'B': an element (e.g. "Ti") or a multicomponent system (e.g. "CoNi")
    C : str
        component 'C': an element (e.g. "Zr") or a multicomponent system (e.g. "WMo")
    Cfix : float (range: (0,1))
        fixed composition value (atomic fraction) of component C
    dc : float (optional; default = 0.01; range (0,1))
        concentration step size (in atomic fraction)
    cAmin : float (optional; default = 0.0; range (0,1))
        min concentration of component A
    cAmax : float (optional; default = (1-Cfix); range (0,1))
        max concentration of component A; if not specified, it is set to max possible value i.e. (1-Cfix)

    Returns
    ----------
    df_alloys : pandas dataframe
        dataframe with alloy names and compositions in atomic fractions of component A, B & C
    """

    print("Concentration of (%s) fixed at '%.3f'" % (C, Cfix), flush=True);
    
    cAmax_allowed = 1 - Cfix;
    
    if cAmax == "auto":
        cAmax = cAmax_allowed;

    if cAmax > cAmax_allowed:
        print("Defined max concentration of component A (i.e. cAmax) is greater than max possible value of %.3f allowed by fixed composition of %.3f for component C" % (cAmax_allowed, Cfix));
        
        print("Max. concentration of component A has been reset to %.3f" % (cAmax_allowed));
        cAmax = cAmax_allowed;
        

    print("Creating alloys for (%s)-(%s)-(%s) ternary system..." % (A, B, C), end="  ", flush=True);
    
    A_comp_dict = af.get_comp_dict(A);
    B_comp_dict = af.get_comp_dict(B);
    C_comp_dict = af.get_comp_dict(C);
    
    alloy_comp_list = [];
    cmax = 1 - Cfix;
    
    for cA in np.arange(cAmin, cAmax + dc/10, dc):
        cB = 1-cA-Cfix;

        alloy_comp_list.append([np.around(np.abs(cA),3),
                      np.around(np.abs(cB),3),
                      np.around(np.abs(Cfix),3)]);
    
    comp_array = np.array(alloy_comp_list);
    
    
    # Creating alloy name for each composition
    alloy_name_list = [];
    all_el_list = sorted(A_comp_dict["el_list"] + B_comp_dict["el_list"] + C_comp_dict["el_list"]);
    x_el_dict = {el:[] for el in all_el_list};
    
    for comp in comp_array:
        alloy_name = "";
        for el in all_el_list:
            
            if el in A_comp_dict["el_list"]:
                el_stoich_in_A = A_comp_dict["el_at_frac_list"][A_comp_dict["el_list"].index(el)];
                el_at_frac = round(comp[0] * el_stoich_in_A, 3);
    
            if el in B_comp_dict["el_list"]:
                el_stoich_in_B = B_comp_dict["el_at_frac_list"][B_comp_dict["el_list"].index(el)];
                el_at_frac = round(comp[1] * el_stoich_in_B, 3);
                
            if el in C_comp_dict["el_list"]:
                el_stoich_in_C = C_comp_dict["el_at_frac_list"][C_comp_dict["el_list"].index(el)];
                el_at_frac = round(comp[2] * el_stoich_in_C, 3);
            
            alloy_name += str(el) + str(el_at_frac);
            x_el_dict[el].append(el_at_frac);

        alloy_name_list.append(alloy_name);
    

    n_alloys = len(alloy_name_list);
    
    df_alloys = pd.DataFrame();
    df_alloys["alloy_id"] = np.arange(1, n_alloys + 1, 1);
    df_alloys["alloy_name"] = np.array(alloy_name_list);
    df_alloys["xA[A=%s]"%(A)] = comp_array[:, 0];
    df_alloys["xB[B=%s]"%(B)] = comp_array[:, 1];
    df_alloys["xC[C=%s]"%(C)] = comp_array[:, 2];

    for el in all_el_list:
        df_alloys["xEl[%s]"%(el)] = np.array(x_el_dict[el]);
    
    df_alloys = df_alloys.set_index("alloy_id");

    print("DONE.", flush=True);
    print(" --------------------------------------- ", flush=True);


    return (df_alloys);



# ---------------------------------------
def equiatomic_alloys(el_list, n_el):
    
    """generates all possible equiatomic alloys containing 'n_el' number of elements from 'el_list'

    Parameters
    ----------
    el_list : list
        list of all elements to be included
    n_el : int
        number of elements in alloys
    
    Returns
    ----------
    df_alloy_names : pandas dataframe
        dataframe with all possible equiatomic alloy names
    """

    n_el = int(n_el);
    print(" --------------------------------------- ", flush=True);
    print("Creating all equiatomic alloys with %d elements from" % (n_el), el_list, "...", end = "  ", flush=True);

    comb_list = list(combinations(el_list, int(n_el)));

    alloy_name_list = [];
    for comb in comb_list:
        temp = "";
        temp = temp.join(comb);
        alloy_name_list.append(str(temp));

    df_alloy_names = pd.DataFrame();
    df_alloy_names["alloy_name"] = alloy_name_list;
    

    print("DONE.", flush=True);
    print(" --------------------------------------- ", flush=True);


    return (df_alloy_names);
    
    

# ---------------------------------------
def all_possible_compositions(el_list, dc=0.01, cmin=0.0):
    
    """generates all possible compositions from given list of elements

    Parameters
    ----------
    el_list : list
        list of all elements to be included
    dc : float (optional; default = 0.01; range (0,1))
        concentration step size (in atomic fraction)
    cmin : float (optional; default = 0.0; range (0,1))
        min concentration of each element
    
    Returns
    ----------
    df_alloys : pandas dataframe
        dataframe with alloy names and compositions in atomic fractions for all possible alloys
    """
    
    n_el = len(el_list);
    el_list = sorted(el_list);
    
    print(" --------------------------------------- ", flush=True);
    print(f"Creating all possible alloys containing {el_list} elements", end = "  ", flush=True);
    
    alloy_comp_list = [];
    alloy_names_list = [];
    cmax = 1 - (cmin * (n_el-1));
    
    if n_el == 2:
        for cA in np.arange(cmin, (min(cmax, 1) + dc/10), dc):
            cB = 1-cA;
            if cB >= cmin - dc/10:
                alloy_comp_list.append([np.around(np.abs(cA),2),
                              np.around(np.abs(cB),2)]);

                alloy_name = "".join([(el_i + str(ci)) for (el_i, ci) in zip(el_list, alloy_comp_list[-1])]);
                alloy_names_list.append(alloy_name);
    
    if n_el == 3:
        for cA in np.arange(cmin, (min(cmax, 1) + dc/10), dc):
            for cB in np.arange(cmin, (min(cmax, 1-cA) + dc/10), dc):
                cC = 1-cA-cB;
                if cC >= cmin - dc/10:
                    alloy_comp_list.append([np.around(np.abs(cA),2),
                                  np.around(np.abs(cB),2),
                                  np.around(np.abs(cC),2)]);

                    alloy_name = "".join([(el_i + str(ci)) for (el_i, ci) in zip(el_list, alloy_comp_list[-1])]);
                    alloy_names_list.append(alloy_name);
    
    if n_el == 4:
        for cA in np.arange(cmin, (min(cmax, 1) + dc/10), dc):
            for cB in np.arange(cmin, (min(cmax, 1-cA) + dc/10), dc):
                for cC in np.arange(cmin, (min(cmax, 1-cA-cB) + dc/10), dc):
                    cD = 1-cA-cB-cC;
                    if cD >= cmin - dc/10:
                        alloy_comp_list.append([np.around(np.abs(cA),2),
                                      np.around(np.abs(cB),2),
                                      np.around(np.abs(cC),2),
                                      np.around(np.abs(cD),2)]);

                        alloy_name = "".join([(el_i + str(ci)) for (el_i, ci) in zip(el_list, alloy_comp_list[-1])]);
                        alloy_names_list.append(alloy_name);
    
    if n_el == 5:
        for cA in np.arange(cmin, (min(cmax, 1) + dc/10), dc):
            for cB in np.arange(cmin, (min(cmax, 1-cA) + dc/10), dc):
                for cC in np.arange(cmin, (min(cmax, 1-cA-cB) + dc/10), dc):
                    for cD in np.arange(cmin, (min(cmax, 1-cA-cB-cC) + dc/10), dc):

                        cE = 1-cA-cB-cC-cD;
                        if cE >= cmin - dc/10:
                            alloy_comp_list.append([np.around(np.abs(cA),2),
                                          np.around(np.abs(cB),2),
                                          np.around(np.abs(cC),2),
                                          np.around(np.abs(cD),2),
                                          np.around(np.abs(cE),2)]);

                            alloy_name = "".join([(el_i + str(ci)) for (el_i, ci) in zip(el_list, alloy_comp_list[-1])]);
                            alloy_names_list.append(alloy_name);
    
    if n_el == 6:
        for cA in np.arange(cmin, (min(cmax, 1) + dc/10), dc):
            for cB in np.arange(cmin, (min(cmax, 1-cA) + dc/10), dc):
                for cC in np.arange(cmin, (min(cmax, 1-cA-cB) + dc/10), dc):
                    for cD in np.arange(cmin, (min(cmax, 1-cA-cB-cC) + dc/10), dc):
                        for cE in np.arange(cmin, (min(cmax, 1-cA-cB-cC-cD) + dc/10), dc):

                            cF = 1-cA-cB-cC-cD-cE;
                            if cF >= cmin - dc/10:
                                alloy_comp_list.append([np.around(np.abs(cA),2),
                                              np.around(np.abs(cB),2),
                                              np.around(np.abs(cC),2),
                                              np.around(np.abs(cD),2),
                                              np.around(np.abs(cE),2),
                                              np.around(np.abs(cF),2)]);

                                alloy_name = "".join([(el_i + str(ci)) for (el_i, ci) in zip(el_list, alloy_comp_list[-1])]);
                                alloy_names_list.append(alloy_name);
    
    if n_el == 7:
        for cA in np.arange(cmin, (min(cmax, 1) + dc/10), dc):
            for cB in np.arange(cmin, (min(cmax, 1-cA) + dc/10), dc):
                for cC in np.arange(cmin, (min(cmax, 1-cA-cB) + dc/10), dc):
                    for cD in np.arange(cmin, (min(cmax, 1-cA-cB-cC) + dc/10), dc):
                        for cE in np.arange(cmin, (min(cmax, 1-cA-cB-cC-cD) + dc/10), dc):
                            for cF in np.arange(cmin, (min(cmax, 1-cA-cB-cC-cD-cE) + dc/10), dc):

                                cG = 1-cA-cB-cC-cD-cE-cF;
                                if cG >= cmin - dc/10:
                                    alloy_comp_list.append([np.around(np.abs(cA),2),
                                                  np.around(np.abs(cB),2),
                                                  np.around(np.abs(cC),2),
                                                  np.around(np.abs(cD),2),
                                                  np.around(np.abs(cE),2),
                                                  np.around(np.abs(cF),2),
                                                  np.around(np.abs(cG),2)]);

                                    alloy_name = "".join([(el_i + str(ci)) for (el_i, ci) in zip(el_list, alloy_comp_list[-1])]);
                                    alloy_names_list.append(alloy_name);
                                
    if n_el == 8:
        for cA in np.arange(cmin, (min(cmax, 1) + dc/10), dc):
            for cB in np.arange(cmin, (min(cmax, 1-cA) + dc/10), dc):
                for cC in np.arange(cmin, (min(cmax, 1-cA-cB) + dc/10), dc):
                    for cD in np.arange(cmin, (min(cmax, 1-cA-cB-cC) + dc/10), dc):
                        for cE in np.arange(cmin, (min(cmax, 1-cA-cB-cC-cD) + dc/10), dc):
                            for cF in np.arange(cmin, (min(cmax, 1-cA-cB-cC-cD-cE) + dc/10), dc):
                                for cG in np.arange(cmin, (min(cmax, 1-cA-cB-cC-cD-cE-cF) + dc/10), dc):

                                    cH = 1-cA-cB-cC-cD-cE-cF-cG;
                                    if cH >= cmin - dc/10:
                                        alloy_comp_list.append([np.around(np.abs(cA),2),
                                                      np.around(np.abs(cB),2),
                                                      np.around(np.abs(cC),2),
                                                      np.around(np.abs(cD),2),
                                                      np.around(np.abs(cE),2),
                                                      np.around(np.abs(cF),2),
                                                      np.around(np.abs(cG),2),
                                                      np.around(np.abs(cH),2)])

                                        alloy_name = "".join([(el_i + str(ci)) for (el_i, ci) in zip(el_list, alloy_comp_list[-1])]);
                                        alloy_names_list.append(alloy_name);
                                
    if n_el == 9:
        for cA in np.arange(cmin, (min(cmax, 1) + dc/10), dc):
            for cB in np.arange(cmin, (min(cmax, 1-cA) + dc/10), dc):
                for cC in np.arange(cmin, (min(cmax, 1-cA-cB) + dc/10), dc):
                    for cD in np.arange(cmin, (min(cmax, 1-cA-cB-cC) + dc/10), dc):
                        for cE in np.arange(cmin, (min(cmax, 1-cA-cB-cC-cD) + dc/10), dc):
                            for cF in np.arange(cmin, (min(cmax, 1-cA-cB-cC-cD-cE) + dc/10), dc):
                                for cG in np.arange(cmin, (min(cmax, 1-cA-cB-cC-cD-cE-cF) + dc/10), dc):
                                    for cH in np.arange(cmin, (min(cmax, 1-cA-cB-cC-cD-cE-cF-cG) + dc/10), dc):

                                        cI = 1-cA-cB-cC-cD-cE-cF-cG-cH;
                                        if cI >= cmin - dc/10:
                                            alloy_comp_list.append([np.around(np.abs(cA),2),
                                                          np.around(np.abs(cB),2),
                                                          np.around(np.abs(cC),2),
                                                          np.around(np.abs(cD),2),
                                                          np.around(np.abs(cE),2),
                                                          np.around(np.abs(cF),2),
                                                          np.around(np.abs(cG),2),
                                                          np.around(np.abs(cH),2),
                                                          np.around(np.abs(cI),2)]);

                                            alloy_name = "".join([(el_i + str(ci)) for (el_i, ci) in zip(el_list, alloy_comp_list[-1])]);
                                            alloy_names_list.append(alloy_name);


    n_alloys = len(alloy_comp_list);
    
    df_alloys = pd.DataFrame();
    df_alloys["alloy_id"] = np.arange(1, n_alloys + 1, 1);
    df_alloys["alloy_name"] = np.array(alloy_names_list);
    
    for (i, el) in zip(range(0, n_el), el_list):
        df_alloys[f"xEl[{el}]"] = np.array(alloy_comp_list)[:,i];
        
    df_alloys = df_alloys.set_index("alloy_id");
    
    print("DONE.", flush=True);
    print(" --------------------------------------- ", flush=True);
    
    
    return (df_alloys);