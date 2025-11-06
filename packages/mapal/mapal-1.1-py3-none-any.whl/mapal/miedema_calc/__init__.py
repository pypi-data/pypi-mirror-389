"""
mapal.miedema_calc
---------------------------------------
Package to implement Miedema's theory of alloy cohesion to estimate mixing enthalpies 

List of functions:
---------------------------------------
get_miedema_enthalpy : calculates mixing enthalpies using Miedema's framework
get_miedema_vol_correction : calculates overall effective volume correction applied to each element in Miedema's model
"""

# --- Import Python add-on libraries ---
import numpy as np

# --- Import mapal packages ---
import mapal;

# load element database file
dict_db_el, _ = mapal.element_data.load_element_database();




# -----------------------------------------------
def get_miedema_enthalpy(alloy_name, state="liquid", show_calc=False, model="R"):

    """Calculates binary enthalpies using Miedema's model and extends it to multi-component alloys using Takeuchi and Inoue's extended regular solid solution.

    Parameters
    ----------
    alloy_name : str
        alloy name string e.g. "NiAl2", "BaTiO3", "Al1.5Ti0.25CrFeNi"
    state : str (optional, default="liquid")
        state of alloy; possible values: "liquid" or "solid"; this affects 
        calculation only when the binary pair has a transition and non-transition
    show_calc : bool (optional, default=False)
        if set to True, prints all calculation steps on the terminal
    model : str (optional, default="R")
        "R"-regular model: Equiatomic binary enthalpies are extended to multi-component alloy
        "NR"-non regular model: Original concentrations are used straight-away for enthalpy calculations

    Returns
    ----------
    enthalpy_dict : dict
        enthalpy dict with five keys:
            "H_chem" : chemical enthalpy of mixing
            "H_el" : elastic enthalpy of mixing
            "H_mix" : total enthalpy of mixing (=H_chem+H_el)
            "H_IM" : formation enthalpy of intermetallic
            "units" : units of enthalpy (kJ/mol)
    """

    dict_alloy_comp = mapal.alloy_features.get_comp_dict(alloy_name);
    el_list = dict_alloy_comp["el_list"];
    c_el_list = dict_alloy_comp["el_at_frac_list"];

    n_element = len(el_list);
    
    n_binaries = int(
            np.math.factorial(n_element)/
            (np.math.factorial(n_element-2)*np.math.factorial(2))
            ); # calculating no. of unique binary systems in alloy
    
    H_mix_alloy_array = np.zeros(n_binaries); # array to store H_mix of binaries; shape=(no. of binaries,)
    H_chem_alloy_array = np.zeros(n_binaries); # array to store H_chem of binaries; shape=(no. of binaries,)
    H_el_alloy_array = np.zeros(n_binaries); # array to store H_elastic of binaries; shape=(no. of binaries,)
    H_IM_alloy_array = np.zeros(n_binaries); # array to store H_chem of binaries; shape=(no. of binaries,)

   
    # printing calculations if 'show_calc' boolean is 'True'
    if show_calc == True:
        
        print('alloy Composition:\n', dict_alloy_comp);
        print('\nNo. of elements=', n_element);
        print('No. of binaries=', n_binaries);
    
    count = 0
    
    
    # loop to iterate over binary systems and calculate one binary enthalpy in each run; runs for 'no. of elements-1' times
    for j in range(0,n_element-1):              # j represents first element in binary; say A
        
        # loop to create
        for k in range(j+1,n_element):          # k represents second element in binary; say B: j=0-> k=1,2,3,4 :: j=1->k=2,3,4 ::j =2->

            # Calculating delta_Hmix of each equiatomic binary
            el_A = el_list[j];

            if model == 'R': cA = 0.5;      # if 'regular model', then equiatomic system: i.e. cA=0.5=cB
            if model == 'NR': cA = c_el_list[j];    # if 'non-regular model', then equiatomic system: i.e. cA=cB=actual conc in alloy
            
            # collecting el_A element data from 'db_element' database
            Vm_A = dict_db_el[el_A]["Vm"]; 
            w_fn_A = dict_db_el[el_A]["phi_workFunc"];
            nWS_A = dict_db_el[el_A]["nWS"];
            K_A = dict_db_el[el_A]["K"];
            G_A = dict_db_el[el_A]["G"];
            type_A = dict_db_el[el_A]["el_type"];

            el_B = el_list[k];

            if model == 'R': cB = 0.5;      # if 'regular model', then equiatomic system: i.e. cA=0.5=cB
            if model == 'NR': cB = c_el_list[k];    # if 'non-regular model', then equiatomic system: i.e. cA=cB=actual conc in alloy
            
            # collecting el_B element data from 'db_element' database
            Vm_B = dict_db_el[el_B]["Vm"]; 
            w_fn_B = dict_db_el[el_B]["phi_workFunc"];
            nWS_B = dict_db_el[el_B]["nWS"];
            K_B = dict_db_el[el_B]["K"];
            G_B = dict_db_el[el_B]["G"];
            type_B = dict_db_el[el_B]["el_type"];

            # surface concentrations of el_A and el_B
            cA_s = cA * (Vm_A**2/3) / (cA * (Vm_A**2/3) + 0.5 * (Vm_B**2/3));
            cB_s = cB * (Vm_B**2/3) / (cB * (Vm_A**2/3) + 0.5 * (Vm_B**2/3));

            del_w_fn = w_fn_A - w_fn_B; # diff in work function
            del_nWS1_3 = nWS_A**(1/3) - nWS_B**(1/3); # delta(nWS^1_3)
            nWS_1_3_avg = (1/2) * (nWS_A**(-1/3) + nWS_B**(-1/3)); # average((nWS^-1_3)

            # volume concentrations of el_A and el_B
            Vm_A_corr = 1.5*cA_s*(Vm_A**(2/3))*(w_fn_A-w_fn_B)*((1/nWS_B)-(1/nWS_A))/(2*nWS_1_3_avg);
            Vm_B_corr = 1.5*cB_s*(Vm_B**(2/3))*(w_fn_B-w_fn_A)*((1/nWS_A)-(1/nWS_B))/(2*nWS_1_3_avg);
            Vm_A_alloy = Vm_A + Vm_A_corr; # corrected volume of el_A
            Vm_B_alloy = Vm_B + Vm_B_corr; # corrected volume of el_B

            # Selecting P,Q,R based on type of elements and alloy_phase
            if (type_A == "transition" and
                type_B == "transition"):

                P = 14.2; Q = 9.4 * P; R = 0;

            if (type_A == "non_transition" and
                type_B == "non_transition"):

                P = 10.7; Q = 9.4 * P; R = 0;

            if (type_A != type_B):
                P = 12.35; Q = 9.4 * P;

                R_P_A = dict_db_el[el_A]["R_P_ratio"];
                R_P_B = dict_db_el[el_B]["R_P_ratio"];
                R_P = R_P_A * R_P_B;

                if state == 'solid': R = 1 * R_P * P; 
                else: R = 0.73 * R_P * P;
            
            
            tau = (1/nWS_1_3_avg)*(-P*(del_w_fn**2)+Q*(del_nWS1_3**2)-R); # tau parameter
            H_chem_AB = (cA*cB)*(cB_s*(Vm_A_alloy**(2/3))+cA_s*(Vm_B_alloy**(2/3)))*tau; # calculating H_chemical

            H_IM_AB = (1+8*(cA_s*cB_s)**2)*(cA*cB)*(cB_s*(Vm_A_alloy**(2/3))+cA_s*(Vm_B_alloy**(2/3)))*tau; # calculating H_Intermetallic
            
            H_el_AinB = 2*K_A*G_B*((Vm_A_alloy-Vm_B_alloy)**2)/(3*K_A*Vm_B_alloy + 4*G_B*Vm_A_alloy); # H_elastic A in B (kJ/mol)
            H_el_BinA = 2*K_B*G_A*((Vm_A_alloy-Vm_B_alloy)**2)/(3*K_B*Vm_A_alloy + 4*G_A*Vm_B_alloy); # H_elastic B in A (kJ/mol)
            H_el_AB = cA*cB*(cB*H_el_AinB + cA*H_el_BinA); # H_elastic of A-B binary (kJ/mol)
            
            H_mix_AB = H_chem_AB + H_el_AB; # H_mix of binary = H_chemical + H_elastic
            
            # If 'regular' model is selected; then enthalpies scaled by 4*cA*cB factor where cA,cB are actual conc. in alloy
            if model == 'R':
                
                cA_alloy = c_el_list[j]; cB_alloy = c_el_list[k]; #actual at. conc. of A and B
                H_chem_alloy_array[count] = 4*cA_alloy*cB_alloy*H_chem_AB; # added to 'H_chemical' array
                H_el_alloy_array[count] = 4*cA_alloy*cB_alloy*H_el_AB; # added to 'H_elastic' array
                H_IM_alloy_array[count]= 4*cA_alloy*cB_alloy*H_IM_AB; # added to 'H_elastic' array
                H_mix_alloy_array[count] = 4*cA_alloy*cB_alloy*H_mix_AB; # added to 'H_mix' array
                
            
            # If 'non-regular' model is selected; no scaling is required
            if model == 'NR':
                
                H_chem_alloy_array[count] = H_chem_AB; # added to 'H_chemical' array
                H_el_alloy_array[count] = H_el_AB; # added to 'H_elastic' array
                H_IM_alloy_array[count]= H_IM_AB;
                H_mix_alloy_array[count] = H_mix_AB; # added to 'H_mix' array
            
            # Printing calculations if 'show_calc' input in function call is 'True'
            if (show_calc==True):

                Bold_s='\033[1m'; Bold_f='\033[0m';
                print(Bold_s+'\nBinary No.',(count+1),'('+el_A+el_B+'):'+Bold_f);
                print('A=%s; cA=%.2f; Vm(A)=%.2f; Work_F(A)=%.2f; nWS(A)=%.2f; K(A)=%.2f; G(A)=%.2f; Type(A)=%s'
                      %(el_A, cA, Vm_A, w_fn_A, nWS_A, K_A, G_A, type_A));

                print('B=%s; cB=%.2f; Vm(B)=%.2f; Work_F(B)=%.2f; nWS(B)=%.2f; K(B)=%.2f; G(B)=%.2f; Type(B)=%s'
                      %(el_B, cB, Vm_B, w_fn_B, nWS_B, K_B, G_B, type_B));

                print('\tcA(s)=%.3f; cB(s)=%.3f; Vm(A)_alloy=%.3f; Vm(B)_alloy=%.3f'
                      %(cA_s, cB_s, Vm_A_alloy, Vm_B_alloy));

                print(Bold_s+'\tChemical Enthalpy:'+Bold_f);
                print('\tdelta(Work_F)=%.2f; delta(nWS^(1/3))=%.2f; nWS^(-1/3)avg=%.2f'
                      %(del_w_fn, del_nWS1_3, nWS_1_3_avg));

                print('\tP=%.2f; R=%.2f; Q=%.2f; Tau=%.3f'%(P, R, Q, tau))
                print(Bold_s+'\t\tH_chem('+el_A+el_B+')= %.3f kJ/mol'%(H_chem_AB)+Bold_f);

                print(Bold_s+'\tElastic Enthalpy:'+Bold_f)
                print('\tH_el(A in B)=%.3f; H_el(B in A)=%.3f'%(H_el_AinB, H_el_BinA));        
                print(Bold_s+'\t\tH_el('+el_A+el_B+')= %.3f kJ/mol'%H_el_AB+Bold_f);

                print(Bold_s+'\n\t\t\t\tdelta_H_mix('+el_A+el_B+')= %.3f kJ/mol'%H_mix_AB+Bold_f);
            
            count+=1;

    # alloy enthalpies = mean of all binary enthalpies
    H_chem_alloy = np.around(np.sum(H_chem_alloy_array),4); 
    H_el_alloy = np.around(np.sum(H_el_alloy_array),4);
    H_IM_alloy = np.around(np.sum(H_IM_alloy_array),4);
    H_mix_alloy = np.around(np.sum(H_mix_alloy_array),4);
    
    
    enthalpy_dict = {
      "H_chem": H_chem_alloy,
      "H_el": H_el_alloy,
      "H_mix": H_mix_alloy,
      "H_IM": H_IM_alloy,
      "units": "kJ/mol"
    };

    if show_calc == True:

        print('\nChemical Enthalpy of mixing of alloy(%s)=%.3f kJ/mol'%(alloy_name,H_chem_alloy));
        print('Elastic Enthalpy of mixing of alloy(%s)=%.3f kJ/mol'%(alloy_name,H_el_alloy));
        print('Intermetallic formation enthalpy of alloy(%s)=%.3f kJ/mol'%(alloy_name,H_IM_alloy));
        print('Enthalpy of mixing of alloy(%s)=%.3f kJ/mol\n'%(alloy_name,H_mix_alloy));

    
    return (enthalpy_dict);



# -----------------------------------------------
def get_miedema_vol_correction(alloy_name):

    """Calculates overall effective volume correction applied to each element in Miedemas model

    Parameters
    ----------
    alloy_name : str
        alloy name string e.g. "NiAl2", "BaTiO3", "Al1.5Ti0.25CrFeNi"

    Returns
    ----------
    dict_delta_Vm_abs : dict
        absolute volume correction dict with two keys:
            "dict_el_delta_Vm" : dict with 'element' keys and 'absolute volume correction' values 
            "total_Vm_corr" : sum of absolute volume correction for alloy
    dict_delta_Vm : dict
        volume correction dict with two keys:
            "dict_el_delta_Vm" : dict with 'element' keys and 'volume correction' values 
            "total_Vm_corr" : sum of volume correction for alloy
    """

    dict_alloy_comp = mapal.alloy_features.get_comp_dict(alloy_name);
    el_list = dict_alloy_comp["el_list"];
    c_el_list = dict_alloy_comp["el_at_frac_list"];
    
    dict_delta_Vm_abs = {
        "dict_el_delta_Vm":{el:0 for el in el_list},
        "total_Vm_corr": 0
    };
    
    dict_delta_Vm = {
        "dict_el_delta_Vm":{el:0 for el in el_list},
        "total_Vm_corr": 0
    };
    
    n_element = len(el_list); 
        
    count = 0
    
    # loop to iterate over binary systems; runs for 'no. of elements-1' times
    for j in range(0,n_element-1):              # j represents first element in binary; say A
        
        # loop to create
        for k in range(j+1,n_element):          # k represents second element in binary; say B: j=0-> k=1,2,3,4 :: j=1->k=2,3,4 ::j =2->

            el_A = el_list[j];
            cA = c_el_list[j];
            Vm_A = dict_db_el[el_A]["Vm"];
            w_fn_A = dict_db_el[el_A]["phi_workFunc"];
            nWS_A = dict_db_el[el_A]["nWS"];

            el_B = el_list[k];
            cB = c_el_list[k];
            Vm_B = dict_db_el[el_B]["Vm"];
            w_fn_B = dict_db_el[el_B]["phi_workFunc"];
            nWS_B = dict_db_el[el_B]["nWS"];

            # surface concentrations of el_A and el_B
            cA_s = cA * (Vm_A**2/3) / (cA * (Vm_A**2/3) + 0.5 * (Vm_B**2/3));
            cB_s = cB * (Vm_B**2/3) / (cB * (Vm_A**2/3) + 0.5 * (Vm_B**2/3));

            nWS_1_3_avg = (1/2) * (nWS_A**(-1/3) + nWS_B**(-1/3)); # average((nWS^-1_3)

            # volume concentrations of el_A and el_B
            Vm_A_corr = 1.5*cA_s*(Vm_A**(2/3))*(w_fn_A-w_fn_B)*((1/nWS_B)-(1/nWS_A))/(2*nWS_1_3_avg);
            Vm_B_corr = 1.5*cB_s*(Vm_B**(2/3))*(w_fn_B-w_fn_A)*((1/nWS_A)-(1/nWS_B))/(2*nWS_1_3_avg);

            
            dict_delta_Vm_abs["dict_el_delta_Vm"][el_A] += (cA * cB * abs(Vm_A_corr));
            dict_delta_Vm_abs["dict_el_delta_Vm"][el_B] += (cA * cB * abs(Vm_B_corr));
            dict_delta_Vm_abs["total_Vm_corr"] += (cA * cB * (abs(Vm_A_corr) + abs(Vm_B_corr)))
            
            
            dict_delta_Vm["dict_el_delta_Vm"][el_A] += (cA * cB * (Vm_A_corr));
            dict_delta_Vm["dict_el_delta_Vm"][el_B] += (cA * cB * (Vm_B_corr));
            dict_delta_Vm["total_Vm_corr"] += (cA * cB * ((Vm_A_corr) + (Vm_B_corr)));

    for el in el_list:
        dict_delta_Vm_abs["dict_el_delta_Vm"][el] = np.around(dict_delta_Vm_abs["dict_el_delta_Vm"][el], 5);
        dict_delta_Vm["dict_el_delta_Vm"][el] = np.around(dict_delta_Vm["dict_el_delta_Vm"][el], 5);

    
    dict_delta_Vm_abs["total_Vm_corr"] = np.around(dict_delta_Vm_abs["total_Vm_corr"], 5)
    dict_delta_Vm["total_Vm_corr"] = np.around(dict_delta_Vm["total_Vm_corr"], 5)

    return (dict_delta_Vm_abs, dict_delta_Vm);