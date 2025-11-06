"""
mapal.map_ML_predictions
---------------------------------------
Package to map predictions from pre-trained machine learning models over continuous
 compositional spaces in binary, ternary and multicomponent systems

List of functions:
---------------------------------------
HV_binary : maps ML predicted hardness to composition variations in a binary system
fPhase_binary : maps ML predicted phase fractions for FCC, BCC & Intermetallic phases to
                composition variations in a binary system
HV_ternary : maps ML predicted hardness to composition variations in a ternary system
fPhase_ternary : 
HV_ternary1Cfixed : maps ML predicted hardness to composition variations in a ternary
                    system where concentration of C component is fixed
fPhase_ternary1Cfixed : 
"""

# --- Import Python add-on libraries ---
import pandas as pd;
from matplotlib import pyplot as plt;
import numpy as np;
import plotly.figure_factory as ff

# --- Import mapal packages ---
from mapal import create_alloys;
from mapal import preTrained_ML_mods;



# -----------------------------------------------
def HV_binary(A, B, dc=0.01, cAmin=0, cAmax=1, mod_key="M1"):

    """maps ML predicted hardness to composition variations in binary system

    Parameters
    ----------
    A : str
        component A e.g. "Al" or "Al0.5Ti"
    B : str
        component B e.g. "Al" or "Al0.5Ti"
    dc : float (optional; default = 0.01; range (0,1))
        concentration step size (in atomic fraction)
    cAmin : float (optional; default = 0.0; range (0,1))
        min concentration of component A
    cAmax : float (optional; default = 1.0; range (0,1))
        max concentration of component A
    mod_key : str (optional, default="M1")
        model key to be used (currently only "M1" available for hardness prediction)

    Returns
    ----------
    fig : matplotlib figure object
        figure with predicted hardness plot
    df_alloys : pandas dataframe
        dataframe with all alloys and corresponding hardness prediction
    """

    df_alloys = create_alloys.binary(A, B, dc=dc, cAmin=cAmin, cAmax=cAmax);
    
    HV_predicted = preTrained_ML_mods.predict(mod_key, df_alloys, input_contains_concentration=True);
    df_alloys["HV_predicted"] = HV_predicted;
    
    fig_size = (10,8);
    fs = 28; #fontsize
    s_size = 70;
    fig = plt.figure(figsize=(fig_size));

    Y = HV_predicted;        
    x = df_alloys["xA[A=%s]"%(A)];        
    plot_title = "$(%s)_{x}(%s)_{1-x}$" % (A, B);
    y_label = "HV_Predicted";
    x_label = "x [%s at. fraction]" % (A);
    
    plt.title(plot_title, fontsize=fs+10);
    plt.scatter(x, Y, s=s_size, alpha=0.7, label=y_label);
    plt.xlabel(x_label, fontsize=fs+5);
    plt.ylabel(y_label, fontsize=fs+5);
    plt.xlim(cAmin, cAmax);
    plt.xticks(fontsize=fs-5); plt.yticks(fontsize=fs-5);
    plt.legend(fontsize=fs-5, frameon=False);

    plt.show();
    

    return (fig, df_alloys);



# -----------------------------------------------
def fPhase_binary(A, B, dc=0.01, cAmin=0, cAmax=1, mod_key="M2"):

    """maps ML predicted phase fractions for FCC, BCC & Intermetallic phases to
     composition variations in a binary system

    Parameters
    ----------
    A : str
        component A e.g. "Al" or "Al0.5Ti"
    B : str
        component B e.g. "Al" or "Al0.5Ti"
    dc : float (optional; default = 0.01; range (0,1))
        concentration step size (in atomic fraction)
    cAmin : float (optional; default = 0.0; range (0,1))
        min concentration of component A
    cAmax : float (optional; default = 1.0; range (0,1))
        max concentration of component A
    mod_key : str (optional, default="M2")
        model key to be used (currently only "M2" available for phase fraction prediction)

    Returns
    ----------
    fig : matplotlib figure object
        figure with predicted phase fraction plot
    df_alloys : pandas dataframe
        dataframe with all alloys and corresponding phase fraction prediction
    """

    df_alloys = create_alloys.binary(A, B, dc=dc, cAmin=cAmin, cAmax=cAmax);
    
    df_phaseFrac_pred = preTrained_ML_mods.predict(mod_key, df_alloys, input_contains_concentration=True);
    df_alloys["f_FCC"] = df_phaseFrac_pred["f_FCC"];
    df_alloys["f_BCC"] = df_phaseFrac_pred["f_BCC"];
    df_alloys["f_IM"] = df_phaseFrac_pred["f_IM"];

    
    fig_size = (10,8);
    fs = 28; #fontsize
    s_size = 70;
    fig = plt.figure(figsize=(fig_size));

    x = df_alloys["xA[A=%s]"%(A)];
    plot_title = "$(%s)_{x}(%s)_{1-x}$" % (A, B);
    x_label = "x [%s at. fraction]" % (A);
    y_label = "Predicted Phase Fraction";

    colors = ["limegreen", "deepskyblue", "hotpink"];
    phases = ["f_FCC", "f_BCC", "f_IM"];
    plt.title(plot_title, fontsize=fs+10);
    
    for (phase, col) in zip(phases, colors):
        Y = df_alloys[phase];
        plt.scatter(x, Y, s=s_size, c=col, alpha=0.7, label=phase);

    plt.xlabel(x_label, fontsize=fs+5);
    plt.ylabel(y_label, fontsize=fs+5);
    plt.xlim(np.amin(x), np.amax(x));
    plt.xticks(fontsize=fs-5); plt.yticks(fontsize=fs-5);
    plt.legend(fontsize=fs-5, frameon=False);

    plt.show();
    

    return (fig, df_alloys);



# -----------------------------------------------
def HV_ternary(A, B, C, dc=0.01, colorscale="Viridis", mod_key="M1"):

    """maps ML predicted hardness to composition variations in a ternary system

    Parameters
    ----------
    A : str
        component A e.g. "Al" or "Al0.5Ti"
    B : str
        component B e.g. "Al" or "Al0.5Ti"
    C : str
        component C e.g. "Al" or "Al0.5Ti"
    dc : float (optional; default = 0.01; range (0,1))
        concentration step size (in atomic fraction)
    colorscale : str (optional; default = "Viridis)
        colorscale used for feature contours (for options, refer to: https://plotly.com/python/builtin-colorscales/)
    mod_key : str (optional, default="M1")
        model key to be used (currently only "M1" available for hardness prediction)

    Returns
    ----------
    fig : plotly figure object
        ternary contour plot of predicted hardness
    df_alloys : pandas dataframe
        dataframe with all alloys and corresponding hardness prediction
    """

    df_alloys = create_alloys.ternary(A, B, C, dc=dc);
    alloyName_list = df_alloys["alloy_name"].to_list();
        
    HV_predicted = preTrained_ML_mods.predict(mod_key, df_alloys, input_contains_concentration=True);
    df_alloys["HV_predicted"] = HV_predicted;
    
    print("Creating contour plot...");

    xA = df_alloys["xA[A=%s]"%(A)];
    xB = df_alloys["xB[B=%s]"%(B)];
    xC = df_alloys["xC[C=%s]"%(C)];
    Y = HV_predicted;
    
    plot_title = "%s-%s-%s [HV_Predicted]" % (A, B, C);
    fig = ff.create_ternary_contour([xA, xB, xC], np.array(Y),
                                    pole_labels=[A, B, C],
                                    width=500,
                                    height=500,
                                    interp_mode="cartesian",
                                    ncontours=20,
                                    colorscale=colorscale,
                                    showscale=True,
                                    title=plot_title);

    fig.show();
    print("Contour plot ready.");
    

    return (fig, df_alloys);



# -----------------------------------------------
def fPhase_ternary(A, B, C, dc=0.01, colorscale="Viridis", mod_key="M2"):

    """maps ML predicted phase fractions for FCC, BCC & Intermetallic phases
     to composition variations in a ternary system

    Parameters
    ----------
    A : str
        component A e.g. "Al" or "Al0.5Ti"
    B : str
        component B e.g. "Al" or "Al0.5Ti"
    C : str
        component C e.g. "Al" or "Al0.5Ti"
    dc : float (optional; default = 0.01; range (0,1))
        concentration step size (in atomic fraction)
    colorscale : str (optional; default = "Viridis)
        colorscale used for feature contours (for options, refer to: https://plotly.com/python/builtin-colorscales/)
    mod_key : str (optional, default="M2")
        model key to be used (currently only "M2" available for hardness prediction)

    Returns
    ----------
    figs_dict : dict (contains plotly figure objects)
        dictionary with ternary contour plots of predicted phase fractions (keys: 'f_FCC', 'f_BCC', 'f_IM')
    df_alloys : pandas dataframe
        dataframe with all alloys and corresponding phase fraction prediction
    """

    df_alloys = create_alloys.ternary(A, B, C, dc=dc);
        
    df_phaseFrac_pred = preTrained_ML_mods.predict(mod_key, df_alloys, input_contains_concentration=True);
    df_alloys["f_FCC"] = df_phaseFrac_pred["f_FCC"];
    df_alloys["f_BCC"] = df_phaseFrac_pred["f_BCC"];
    df_alloys["f_IM"] = df_phaseFrac_pred["f_IM"];
    

    xA = df_alloys["xA[A=%s]"%(A)];
    xB = df_alloys["xB[B=%s]"%(B)];
    xC = df_alloys["xC[C=%s]"%(C)];

    phases = ["f_FCC", "f_BCC", "f_IM"];
    figs_dict = {};

    for phase in phases:
        print("Creating contour plot for '%s'..." % (phase));
        Y = df_alloys[phase];
        plot_title = "%s-%s-%s [%s]" % (A, B, C, phase);
        fig = ff.create_ternary_contour([xA, xB, xC], np.array(Y),
                                        pole_labels=[A, B, C],
                                        width=500,
                                        height=500,
                                        interp_mode="cartesian",
                                        ncontours=20,
                                        colorscale=colorscale,
                                        showscale=True,
                                        title=plot_title);

        fig.show();
        figs_dict[phase] = fig;
        print("Contour plot for '%s' ready." % (phase));
    

    return (figs_dict, df_alloys);



# -----------------------------------------------
def HV_ternary1Cfixed(A, B, C, Cfix, dc=0.01, cAmin=0, cAmax="auto", mod_key="M1"):

    """maps ML predicted hardness to composition variations in a ternary system where concentration of C component is fixed

    Parameters
    ----------
    A : str
        component A e.g. "Al" or "Al0.5Ti"
    B : str
        component B e.g. "Al" or "Al0.5Ti"
    C : str
        component C e.g. "Al" or "Al0.5Ti"
    Cfix : float
        fixed concentration (atomic fraction) of component C
    dc : float (optional; default = 0.01; range (0,1))
        concentration step size (in atomic fraction)
    cAmin : float (optional; default = 0.0; range (0,1))
        min concentration of component A
    cAmax : float (optional; default = (1-Cfix); range (0,1))
        max concentration of component A; if not specified, it is set to max possible value i.e. (1-Cfix)
    mod_key : str (optional, default="M1")
        model key to be used (currently only "M1" available)

    Returns
    ----------
    fig : matplotlib figure object
        figure with predicted hardness plot
    df_alloys : pandas dataframe
        dataframe with all alloys and corresponding hardness prediction
    """

    df_alloys = create_alloys.ternary_1Cfixed(A, B, C, Cfix, dc=dc, cAmin=cAmin, cAmax=cAmax);
    alloyName_list = df_alloys["alloy_name"].to_list();
    
    HV_predicted = preTrained_ML_mods.predict(mod_key, df_alloys, input_contains_concentration=True);
    df_alloys["HV_predicted"] = HV_predicted;
    
    fig_size = (10,8);
    fs = 28; #fontsize
    s_size = 70;
    fig = plt.figure(figsize=(fig_size));

    Y = HV_predicted;        
    x = df_alloys["xA[A=%s]"%(A)];        
    plot_title = "$(%s)_{x}(%s)_{1-x}(%s)_{%.2f}$" % (A, B, C, Cfix);
    y_label = "HV_Predicted";
    x_label = "x [%s at. fraction]" % (A);

    plt.title(plot_title, fontsize=fs+10);
    plt.scatter(x, Y, s=s_size, alpha=0.7, label=y_label);
    plt.xlabel(x_label, fontsize=fs+5);
    plt.ylabel(y_label, fontsize=fs+5);
    plt.xlim(cAmin, np.amax(x));
    plt.xticks(fontsize=fs-5); plt.yticks(fontsize=fs-5);
    plt.legend(fontsize=fs-5, frameon=False);

    plt.show();


    return (fig, df_alloys);



# -----------------------------------------------
def fPhase_ternary1Cfixed(A, B, C, Cfix, dc=0.01, cAmin=0, cAmax="auto", mod_key="M2"):

    """maps ML predicted phase fractions for FCC, BCC & Intermetallic phases
     to composition variations in a ternary system where concentration of C component is fixed

    Parameters
    ----------
    A : str
        component A e.g. "Al" or "Al0.5Ti"
    B : str
        component B e.g. "Al" or "Al0.5Ti"
    C : str
        component C e.g. "Al" or "Al0.5Ti"
    Cfix : float
        fixed concentration (atomic fraction) of component C
    dc : float (optional; default = 0.01; range (0,1))
        concentration step size (in atomic fraction)
    cAmin : float (optional; default = 0.0; range (0,1))
        min concentration of component A
    cAmax : float (optional; default = (1-Cfix); range (0,1))
        max concentration of component A; if not specified, it is set to max possible value i.e. (1-Cfix)
    mod_key : str (optional, default="M2")
        model key to be used (currently only "M2" available for phase fraction predictions)

    Returns
    ----------
    fig : matplotlib figure object
        figure with predicted phase fraction plot
    df_alloys : pandas dataframe
        dataframe with all alloys and corresponding phase fraction prediction
    """

    df_alloys = create_alloys.ternary_1Cfixed(A, B, C, Cfix, dc=dc, cAmin=cAmin, cAmax=cAmax);
    
    df_phaseFrac_pred = preTrained_ML_mods.predict(mod_key, df_alloys, input_contains_concentration=True);
    df_alloys["f_FCC"] = df_phaseFrac_pred["f_FCC"];
    df_alloys["f_BCC"] = df_phaseFrac_pred["f_BCC"];
    df_alloys["f_IM"] = df_phaseFrac_pred["f_IM"];
    
    fig_size = (10,8);
    fs = 28; #fontsize
    s_size = 70;
    fig = plt.figure(figsize=(fig_size));

    x = df_alloys["xA[A=%s]"%(A)];        
    plot_title = "$(%s)_{x}(%s)_{1-x}(%s)_{%.2f}$" % (A, B, C, Cfix);
    x_label = "x [%s at. fraction]" % (A);
    y_label = "Predicted Phase Fraction";

    colors = ["limegreen", "deepskyblue", "hotpink"];
    phases = ["f_FCC", "f_BCC", "f_IM"];

    plt.title(plot_title, fontsize=fs+10);

    for (phase, col) in zip(phases, colors):
        Y = df_alloys[phase];
        plt.scatter(x, Y, s=s_size, c=col, alpha=0.7, label=phase);

    plt.xlabel(x_label, fontsize=fs+5);
    plt.ylabel(y_label, fontsize=fs+5);
    plt.xlim(np.amin(x), np.amax(x));
    plt.xticks(fontsize=fs-5); plt.yticks(fontsize=fs-5);
    plt.legend(fontsize=fs-5, frameon=False);

    plt.show();


    return (fig, df_alloys);