"""
mapal
---------------------------------------
MAPping ALloys :
A Python library for mapping features and properties of alloys over compositional spaces.

List of packages :
---------------------------------------
element_data : package to access element properties from in-built element database
create_alloys : package to create alloys over user-defined compositional spaces including (binary), 
                (ternary) and (ternary with 1 component fixed)
alloy_features : create features derived from elemental properties for a given list of alloys
miedema_calc : use miedema calculator to get chemical and elastic mixing enthalpies based on miedema's framework
preTrained_ML_mods : use pre-trained models available in the package to predict properties of alloys
interpret_ML_mods : use interpretation framework to get exact feature contributions over compositional pathways
map_features : map alloy features over continuous compositional spaces in binary, ternary and multicomponent systems
map_ML_predictions : map predictions from pre-trained machine learning models over continuous compositional spaces in binary, ternary and multicomponent systems
"""


# --- Import mapal packages ---
from mapal import (
    create_alloys,
    alloy_features,
    element_data,
    miedema_calc,
    preTrained_ML_mods,
    map_features,
    map_ML_predictions
)