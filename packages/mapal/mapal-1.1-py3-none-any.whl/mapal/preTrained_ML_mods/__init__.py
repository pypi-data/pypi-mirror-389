"""
mapal.preTrained_ML_mods
---------------------------------------
Package to use pre-trained machine learning (ML) models for making predictions for alloy systems

List of functions:
---------------------------------------
mods_list : prints models available along with model keys to access a model
info : generates detailed information about any model key
predict_hardness : predict hardness for alloys using a 'hardness prediction model'
predict_phase_fractions : predict BCC/FCC/IM phase fractions for alloys using a 'phase prediction model'
"""


# --- Import Python built-in libraries ---
import os;
import json;
import gc;
import logging;

# --- Import mapal packages ---
import mapal;
from mapal import alloy_features, miedema_calc;

# --- Import python libraries ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'; #stops tensorflow error messages
import tensorflow as tf;
from tensorflow.keras import models;
tf.get_logger().setLevel(logging.ERROR);

import numpy as np;
import pandas as pd;

SEP = os.sep;


# -----------------------------------------------
def load_model_info(info_file):
    
    """loads json file containing information about the pre-trained ML models available in MAPAL
    
    Parameters
    ----------
    info_file : str (default="model_info.json")
        name of json file containing the model information.
    
    Returns
    ----------
    dict_mod_info: dict
        dictionary containing information about all models available in MAPAL
    """
    
    ref_dir = os.path.abspath(mapal.preTrained_ML_mods.__file__).split("__init__.py")[0];
    mod_info_filepath = f"{ref_dir}{info_file}";
    
    with open(mod_info_filepath, 'r', encoding="latin-1") as f:
        dict_mod_info = json.load(f);
    
    return (dict_mod_info);



# ---------------------------------------
def mods_list():

    """prints models available along with model keys to access a model

    Parameters
    ----------
    no inputs required

    Returns
    ----------
    prints quick information about all pre-trained ML models available
    """
    
    info_file="model_info.json";
    dict_mod_info = load_model_info(info_file);
    
    print("---------------------------------------", flush=True);
    print("--- Pre-trained ML models available in MAPAL ---", flush=True);
    
    for mod_key in list(dict_mod_info.keys()):
        print(f"model_key-'{mod_key}': {dict_mod_info[mod_key]['description']}", flush=True);
    
    print("---------------------------------------", flush=True);



# ---------------------------------------
def get_mod_info(mod_key="all"):

    """generates detailed information about any model key

    Parameters
    ----------
    mod : str
        model key for which information is required e.g. “M1” or “M2”

    Returns
    ----------
    dict_info : dict
        dictionary with information about the queried model; it has 7 keys:
            “model key” :  model key used for access
            “description” :  brief description of model
            “reference” :  reference of the model (usually a published work)
            "DOI" : digital object identifier of model reference
            “features” :  list of features used by the model
            “model_output” : the output produced by the model
            “model_input” :  inputs taken by the model
    """
    
    info_file="model_info.json";
    dict_mod_info = load_model_info(info_file);
    
    if mod_key != "all":
        dict_mod_info = dict_mod_info[mod_key];
    
    return (dict_mod_info);



# -----------------------------------------------
def predict(mod_key, input_alloys, input_contains_concentration=False):

    """generate predictions using a pre-trained model accessed through "mod_key"

    Parameters
    ----------
    mod_key : str
        model key that identifies each pre-trained model. Use "preTrained_ML_mods.mods_list()" function to see all models available
    input_alloys : list/array/pandas DataFrame
        contains input alloys for which prediction is to be made
    input_contains_concentration : boolean (default=False)
        boolean to decide if the input_alloys contains concentration of elements or not. If set to False, then the input_alloys is first converted to a dataframe with concentration information. The alloys created using mapal.create_alloys contain element concentrations.
        
    Returns
    ----------
    ML_prediction : array/dictionary/pandas dataframe
        Output predicted by the model accessed. The data type of output may vary from model to model. Use "preTrained_ML_mods.get_mod_info('mod_key)" function to see information of each model.
    """
    
    func = getattr(mapal.preTrained_ML_mods, f"run_model_{mod_key}");
    
    return (func(input_alloys, input_contains_concentration));




# -----------------------------------------------
def run_model_M1(input_alloys, input_contains_concentration=False):
    
    """runs pre-trained model "M1" to predict phase fraction of FCC, BCC and Intermetallic phases for input alloys

    Parameters
    ----------
    input_alloys : list/array/pandas DataFrame
        contains input alloys for which prediction is to be made
    input_contains_concentration : boolean (default=False)
        boolean to decide if the input_alloys contains concentration of elements or not. If set to False, then the input_alloys is first converted to a dataframe with concentration information.
        
    Returns
    ----------
    HV_pred_array : array
        array containing predict vicker's hardness of input alloys
    """
    
    print("------------------------------------------------", flush=True);
    print("--- Pre-trained model loaded (M1: Vickers hardness prediction) ---", flush=True);
    
    # If input alloys do not contain element concentration, convert them to one
    if input_contains_concentration==False:
        df_alloys = convert_alloy_list_to_dataframe(input_alloys);
    else:
        df_alloys = input_alloys.copy();
    
    el_col_list = [col for col in list(df_alloys.columns) if "xEl" in col];
    el_list = [col.split("[")[1].strip("]") for col in el_col_list];
    
    print(f"Creating alloy features...", end=" ", flush=True);
    
    dict_db_el, _ = mapal.element_data.load_element_database();
    
    n_alloys = len(df_alloys);
    alloy_list = list(df_alloys["alloy_name"]);
    
    el_col_list = [f"xEl[{el}]" for el in el_list]; #col names list with element conc.
    ci = np.array(df_alloys[el_col_list]); # composition array
    
    #below two lines needed only when handling very large datasets
    del df_alloys; # delete df_alloys as not needed after this
    gc.collect();
    
    df_feats = pd.DataFrame();
    
    el_prop_list = [[dict_db_el[el]["r_met"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["R_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;

    R = 0.008314; # kJ/(Kelvin.mole)
    with np.errstate(divide="ignore"):
        log_ci = np.log(ci);
        log_ci[np.isneginf(log_ci)] = 0;
        df_feats["S_config"] = np.sum((ci * log_ci * (-R)), axis=1);
        del log_ci; # delete log_ci after this
        gc.collect();
    
    np.errstate(divide="warn");
    
    el_prop_list = [[dict_db_el[el]["VEC"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["VEC"] = np.sum(ci * xi, axis=1);
    
    el_prop_list = [[dict_db_el[el]["r_cov"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["R_cov_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;
    
    el_prop_list = [[dict_db_el[el]["density_S"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["density_avg"] = np.sum(ci * xi, axis=1);
    
    el_prop_list = [[dict_db_el[el]["E"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["E_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;
    
    el_prop_list = [[dict_db_el[el]["G"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["G_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;
    
    el_prop_list = [[dict_db_el[el]["Vm"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["Vm_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;
    
    H_ch_list, H_el_list = [], [];
    for alloy_name in alloy_list:
        H_dict = miedema_calc.get_miedema_enthalpy(alloy_name);
        H_ch_list.append(H_dict["H_chem"]);
        H_el_list.append(H_dict["H_el"]);
        
    df_feats["H_ch_M_L_R"] = H_ch_list;
    df_feats["H_el_M_S_R"] = H_el_list;
    
    del ci, xi, alloy_list, H_ch_list, H_el_list, el_prop_list;
    gc.collect();
    
    print("DONE.", flush=True);
    
    print("Normalizing features...", end=" ", flush=True);
    # Normalize features
    xmin_HV = np.array([0.003471, 0.009134, 2.8, 0.022247, 2.771, 0.03094, 0.01621, 0.028474, -30.22, 0.18]);
    xmax_HV = np.array([0.141008, 0.017288, 10, 0.126806, 13.6175, 0.642879, 0.591673, 0.352015, 6.43, 14.63]);
    x_norm_HV = (df_feats - xmin_HV)/(xmax_HV - xmin_HV);
    print("DONE.", flush=True);
    
    print(f"Predicting vickers hardness...", end=" ", flush=True);
    ref_dir = os.path.abspath(mapal.preTrained_ML_mods.__file__).split("__init__.py")[0];
    mod_dir = f"{ref_dir}M1-trained-model{SEP}";
    mod_files_dir = f"{mod_dir}mod_files{SEP}";
    model_featnames_filepath = f"{mod_dir}mod_feats_input.csv";
    
    model_list = os.listdir(mod_files_dir);
    df_mod_featnames = pd.read_csv(model_featnames_filepath).set_index("mod_id");

    mod_count = 0;
    for mod in sorted(model_list):

        mod_id = int(mod.split(".")[0]); #find code of model_save file
        feat_names_current_mod = df_mod_featnames.loc[mod_id].iloc[0].split(",");
        model = models.load_model(f"{mod_files_dir}{mod}", compile=False); #loading the tained model into 'model' variable
        pred = model.predict(np.array(x_norm_HV[feat_names_current_mod])); #predicting the hardness
    
        if mod_count == 0:
            comb_model_HV = np.zeros(shape=pred.shape);
        else:
            comb_model_HV = comb_model_HV + pred;

        mod_count += 1;

    HV_pred_array = comb_model_HV / len(model_list);
    HV_pred_array = HV_pred_array.reshape(-1);
    
    del pred, comb_model_HV;
    gc.collect();
    
    print("DONE.", flush=True)
    print("------------------------------------------------", flush=True)
    
    
    return (HV_pred_array)
    
    

# -----------------------------------------------
def run_model_M2(input_alloys, input_contains_concentration=False):
    
    """runs pre-trained model "M2" to predict phase fraction of FCC, BCC and Intermetallic phases for input alloys

    Parameters
    ----------
    input_alloys : list/array/pandas DataFrame
        contains input alloys for which prediction is to be made
    input_contains_concentration : boolean (default=False)
        boolean to decide if the input_alloys contains concentration of elements or not. If set to False, then the input_alloys is first converted to a dataframe with concentration information.
        
    Returns
    ----------
    dict_phase_predict : dictionary
        dictionary containing three keys: "f_FCC", "f_BCC" and "f_IM" which contain the predicted phase fraction of FCC, BCC and Intermetallic phases respectively.
    """
    
    print("------------------------------------------------", flush=True);
    print("--- Pre-trained model loaded (M2: FCC, BCC & Intermetallic phase fraction prediction) ---", flush=True);
    
    # If input alloys do not contain element concentration, convert them to one
    if input_contains_concentration==False:
        df_alloys = convert_alloy_list_to_dataframe(input_alloys);
    else:
        df_alloys = input_alloys.copy();
    
    el_col_list = [col for col in list(df_alloys.columns) if "xEl" in col];
    el_list = [col.split("[")[1].strip("]") for col in el_col_list];
    
    print(f"Creating alloy features...", end=" ", flush=True);
    
    dict_db_el, _ = mapal.element_data.load_element_database();
    
    n_alloys = len(df_alloys);
    alloy_list = list(df_alloys["alloy_name"]);
    
    el_col_list = [f"xEl[{el}]" for el in el_list]; #col names list with element conc.
    ci = np.array(df_alloys[el_col_list]); # composition array
    
    del df_alloys; # delete df_alloys as not needed after this
    gc.collect();
    
    df_feats = pd.DataFrame();
    
    el_prop_list = [[dict_db_el[el]["r_met"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["R_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;

    R = 0.008314; # kJ/(Kelvin.mole)
    with np.errstate(divide="ignore"):
        log_ci = np.log(ci);
        log_ci[np.isneginf(log_ci)] = 0;
        df_feats["S_config"] = np.sum((ci * log_ci * (-R)), axis=1);
        del log_ci; # delete log_ci after this
        gc.collect();
    
    np.errstate(divide="warn");
    
    el_prop_list = [[dict_db_el[el]["VEC"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["VEC"] = np.sum(ci * xi, axis=1);
    
    el_prop_list = [[dict_db_el[el]["r_cov"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["R_cov_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;
    
    el_prop_list = [[dict_db_el[el]["density_S"] for el in el_list]]
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["density_avg"] = np.sum(ci * xi, axis=1);
    
    el_prop_list = [[dict_db_el[el]["E"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["E_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;
    
    el_prop_list = [[dict_db_el[el]["G"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["G_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;
    
    el_prop_list = [[dict_db_el[el]["K"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["K_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;
    
    el_prop_list = [[dict_db_el[el]["EN_Allen"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["EN_Allen_avg"] = np.sum(ci * xi, axis=1)
    
    el_prop_list = [[dict_db_el[el]["Vm"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["Vm_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;
    
    el_prop_list = [[dict_db_el[el]["Coh_E"] for el in el_list]];
    xi = np.array(el_prop_list * n_alloys); # element property array
    df_feats["E_coh_avg"] = np.sum(ci * xi, axis=1);
    df_feats["E_coh_delta"] = np.sum(ci* (1 - (xi / ((np.sum(ci * xi, axis=1)).reshape(n_alloys, 1))))**2, axis=1)**0.5;

    H_ch_list, H_el_list = [], [];
    for alloy_name in alloy_list:
        H_dict = miedema_calc.get_miedema_enthalpy(alloy_name);
        H_ch_list.append(H_dict["H_chem"]);
        H_el_list.append(H_dict["H_el"]);
        
    df_feats["H_ch_M_L_R"] = H_ch_list;
    df_feats["H_el_M_S_R"] = H_el_list;
    
    del ci, xi, alloy_list, H_ch_list, H_el_list, el_prop_list;
    gc.collect();
    
    print("DONE.", flush=True);
    
    print("Normalizing features...", end=" ", flush=True);
    # Normalize features
    xmin_f_phase = np.array([0.003471, 0.006465, 3.35, 0.022247, 2.9945, 0.03094, 0.035845,
        0.050667, 1.295556, 0.031103, 2.193125, 0.015294, -35.81, 0.21]);
    
    xmax_f_phase = np.array([0.193801, 0.018268, 10.4, 0.190032, 13.6175, 0.704672, 1.372104,
        0.880694, 1.936923, 0.51737, 7.8475, 0.447229, 5.23, 27.12]);
    
    x_norm_f_phase = (df_feats - xmin_f_phase)/(xmax_f_phase - xmin_f_phase);
    print("DONE.", flush=True);
    
    print(f"Predicting phase fraction of FCC, BCC & Intermetallic phases...", end=" ", flush=True);
    ref_dir = os.path.abspath(mapal.preTrained_ML_mods.__file__).split("__init__.py")[0];
    mod_dir = f"{ref_dir}M2-trained-model{SEP}";
    mod_files_dir = f"{mod_dir}mod_files{SEP}";
    
    model_list = os.listdir(mod_files_dir);
    n_models = len(model_list);

    n_alloys = len(x_norm_f_phase);
    
    f_FCC_sum = np.zeros(shape=(n_alloys,));
    f_BCC_sum = np.zeros(shape=(n_alloys,));
    f_IM_sum = np.zeros(shape=(n_alloys,));
    
    for mod in sorted(model_list):
        model = models.load_model(f"{mod_files_dir}{mod}", compile=False);
        f_phase_pred = model.predict(x_norm_f_phase);
        
        f_FCC_sum += f_phase_pred[:,0];
        f_BCC_sum += f_phase_pred[:,1];
        f_IM_sum += f_phase_pred[:,2];
        
    f_FCC_pred_array = f_FCC_sum / n_models;
    f_BCC_pred_array = f_BCC_sum / n_models;
    f_IM_pred_array = f_IM_sum / n_models;
    
    del x_norm_f_phase, f_phase_pred, f_FCC_sum, f_BCC_sum, f_IM_sum;
    gc.collect();
    
    print("DONE.", flush=True);
    print("------------------------------------------------", flush=True);
    
    dict_phase_predict = {"f_FCC": f_FCC_pred_array,
                          "f_BCC": f_BCC_pred_array,
                          "f_IM": f_IM_pred_array
        };
    
    return (dict_phase_predict);



# -----------------------------------------------
def convert_alloy_list_to_dataframe(alloy_list):
    
    """converts list of alloy names into a pandas dataframe that contains concentration of elements in each alloy

    Parameters
    ----------
    alloy_list : list
        list of alloy names
    
    Returns
    ----------
    df_alloys : pandas DataFrame
        contains alloy names along with the concentration of elements in each alloy
    """
    
    
    n_alloys = len(alloy_list);

    # Find unique elements present in entire alloy list
    el_list_all_alloys = [];
    for alloy in alloy_list:
        el_list_all_alloys += alloy_features.get_comp_dict(alloy)["el_list"];

    unique_el_list = list(np.unique(el_list_all_alloys));

    # Find concentration of each element in all alloys
    x_el_dict = {el:[] for el in unique_el_list};

    for alloy in alloy_list:
        el_list = alloy_features.get_comp_dict(alloy)["el_list"];
        el_at_frac_list = alloy_features.get_comp_dict(alloy)["el_at_frac_list"];
        for el in list(x_el_dict.keys()):
            if el in el_list:
                x_el_dict[el].append(el_at_frac_list[el_list.index(el)]);
            else:
                x_el_dict[el].append(0);

    # Create df_alloys 
    df_alloys = pd.DataFrame();
    df_alloys["alloy_id"] = np.arange(1, n_alloys + 1, 1);
    df_alloys["alloy_name"] = np.array(alloy_list);

    for el in list(x_el_dict.keys()):
        df_alloys["xEl[%s]"%(el)] = np.array(x_el_dict[el]);

    df_alloys = df_alloys.set_index("alloy_id");
    
    return (df_alloys);