"""
mapal.map_features
---------------------------------------
Package to map alloy features over continuous compositional spaces in binary, ternary and multicomponent systems

List of functions:
---------------------------------------
binary : maps features to composition variations in binary system
ternary : maps alloy feature variations over a ternary system
ternary1Cfixed : maps alloy feature variations over a ternary system where concentration of C component is fixed
"""

# --- Import Python built-in libraries ---
import math;

# --- Import Python add-on libraries ---
from matplotlib import pyplot as plt;
import numpy as np;
import plotly.figure_factory as ff;

# --- Import mapal packages ---
from mapal import alloy_features as af;
from mapal import create_alloys as ca;



# -----------------------------------------------
def binary(feats, A, B, dc=0.01, cAmin=0, cAmax=1, nCols=4):

    """maps features to composition variations in binary system

    Parameters
    ----------
    feats : list
        list of features to be mapped
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
    nCols : int
        max no. of columns in final figure

    Returns
    ----------
    fig : matplotlib figure object
        figure with plots of all features
    df_alloys : pandas dataframe
        dataframe with all alloys and corresponding feature values
    """

    df_alloys = ca.binary(A, B, dc=dc, cAmin=cAmin, cAmax=cAmax);
    alloyName_list = df_alloys["alloy_name"].to_list();
    
    if type(feats) != list:
        x = feats;
        feats = [];
        feats.append(x);
    
    nPlots = len(feats);
    if nPlots < nCols:
        nCols = nPlots;

    nRows = math.ceil(nPlots/nCols);
    
    fig_size = (10,8);
    fs = 28; #fontsize
    line_width = 10;
    fig = plt.figure(figsize=(fig_size[0]*nCols, fig_size[1]*nRows));
    
    for (feat, i_plot) in zip(feats, range(1, nPlots+1)):
        
        feat_name = (("%s_%s" % (feat[0], feat[1])) if type(feat) == tuple else feat);
        Y = af.get_feat_value(alloyName_list, feat);
        x = df_alloys["xA[A=%s]"%(A)];
        df_alloys[feat_name] = Y;
        
        plt.subplot(nRows, nCols, i_plot);
        
        plot_title = "$(%s)_{x}(%s)_{1-x}$" % (A, B);
        y_label = feat_name;
        x_label = "x [%s at. fraction]" % (A);
        
        plt.title(plot_title, fontsize=fs+10);
        plt.plot(x, Y, lw=line_width, alpha=0.7, label=y_label);
        plt.xlabel(x_label, fontsize=fs+5);
        plt.ylabel(y_label, fontsize=fs+5);
        plt.xlim(cAmin, cAmax);
        plt.xticks(fontsize=fs-5); plt.yticks(fontsize=fs-5);
        plt.legend(fontsize=fs-5, frameon=False);
        plt.tight_layout(h_pad=5, w_pad=5);

    plt.show();
    

    return (fig, df_alloys);



# -----------------------------------------------
def ternary(feats, A, B, C, dc=0.01, colorscale="Viridis"):

    """maps features to composition variations in a ternary system

    Parameters
    ----------
    feats : list
        list of features to be mapped
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

    Returns
    ----------
    figs : list of matplotlib figure objects
        list containing ternary contour figures of all features
    df_alloys : pandas dataframe
        dataframe with all alloys and corresponding feature values
    """

    df_alloys = ca.ternary(A, B, C, dc=dc);
    alloyName_list = df_alloys["alloy_name"].to_list();
    
    if type(feats) != list:
        x = feats;
        feats = [];
        feats.append(x);

    figs = [];
    for feat in feats:
        
        feat_name = (("%s_%s" % (feat[0], feat[1])) if type(feat) == tuple else feat);
        feat_val_list = af.get_feat_value(alloyName_list, feat);
        df_alloys[feat_name] = feat_val_list;
        print("Creating contour plot...");

        xA = df_alloys["xA[A=%s]"%(A)];
        xB = df_alloys["xB[B=%s]"%(B)];
        xC = df_alloys["xC[C=%s]"%(C)];
        
        plot_title = "%s-%s-%s [%s]" % (A, B, C, feat_name);
        fig = ff.create_ternary_contour([xA, xB, xC], np.array(feat_val_list),
                                        pole_labels=[A, B, C],
                                        width=500,
                                        height=500,
                                        interp_mode="cartesian",
                                        ncontours=20,
                                        colorscale=colorscale,
                                        showscale=True,
                                        title=plot_title);

        fig.show();
        print("Contour plot for %s ready." % (feat_name));
        figs.append(fig);
    

    return (figs, df_alloys);



# -----------------------------------------------
def ternary1Cfixed(feats, A, B, C, Cfix, dc=0.01, cAmin=0, cAmax="auto", nCols=4):

    """maps features to composition variations in a ternary system where concentration of C component is fixed

    Parameters
    ----------
    feats : list
        list of features to be mapped
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
    nCols : int
        max no. of columns in final figure

    Returns
    ----------
    fig : matplotlib figure object
        figure with plots of all features
    df_alloys : pandas dataframe
        dataframe with all alloys and corresponding feature values
    """

    df_alloys = ca.ternary_1Cfixed(A, B, C, Cfix=Cfix, dc=dc, cAmin=cAmin, cAmax=cAmax);
    alloyName_list = df_alloys["alloy_name"].to_list();
    
    if type(feats) != list:
        x = feats;
        feats = [];
        feats.append(x);
    
    nPlots = len(feats);
    if nPlots < nCols:
        nCols = nPlots;

    nRows = math.ceil(nPlots/nCols);
    
    fig_size = (10,8);
    fs = 28; #fontsize
    line_width = 10;
    fig = plt.figure(figsize=(fig_size[0]*nCols, fig_size[1]*nRows));
    
    for (feat, i_plot) in zip(feats, range(1, nPlots+1)):
        
        feat_name = (("%s_%s" % (feat[0], feat[1])) if type(feat) == tuple else feat);
        Y = af.get_feat_value(alloyName_list, feat);
        x = df_alloys["xA[A=%s]"%(A)];
        df_alloys[feat_name] = Y;
        
        plt.subplot(nRows, nCols, i_plot);
        
        plot_title = "$(%s)_{x}(%s)_{1-x}(%s)_{%.2f}$" % (A, B, C, Cfix);
        y_label = feat_name;
        x_label = "x [%s at. fraction]" % (A);
        
        plt.title(plot_title, fontsize=fs+5);
        plt.plot(x, Y, lw=line_width, alpha=0.7, label=y_label);
        plt.xlabel(x_label, fontsize=fs+5);
        plt.ylabel(y_label, fontsize=fs+5);
        plt.xlim(np.amin(x), np.amax(x));
        plt.xticks(fontsize=fs-5); plt.yticks(fontsize=fs-5);
        plt.legend(fontsize=fs-5, frameon=False);
        plt.tight_layout(h_pad=5, w_pad=5);

    plt.show();


    return (fig, df_alloys);