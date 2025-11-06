import re
import numpy as np
from sympy import Matrix
from collections import defaultdict
import math
from typing import Dict, List, Any, Tuple, Optional
from itertools import combinations
import sys 

# --- Global Constants ---
STANDARD_TEMPERATURE_K = 298.15 # 25°C in Kelvin
R_GAS_CONSTANT = 8.314 / 1000.0  # Gas Constant (kJ/mol·K)
F_FARADAY_CONSTANT = 96.485  # Faraday's Constant (kJ/V·mol)
TOLERANCE = 1e-4 # Numerical tolerance for balancing and comparison

# -----------------------------------------------------------------------------
# 1. CORE DATASET: Elements (Z=1 to Z=118 - COMPLETE SET)
# -----------------------------------------------------------------------------
ELEMENTS = {
    # Period 1
    "H":{"Z":1,"name":"Hydrogen","mass":1.008,"EN":2.20,"type":"nonmetal","oxidation":[1,-1], "S":130.7},
    "He":{"Z":2,"name":"Helium","mass":4.003,"EN":0.00,"type":"noble gas","oxidation":[], "S":126.2},
    # Period 2
    "Li":{"Z":3,"name":"Lithium","mass":6.94,"EN":0.98,"type":"metal","oxidation":[1], "S":29.1},
    "Be":{"Z":4,"name":"Beryllium","mass":9.012,"EN":1.57,"type":"metal","oxidation":[2], "S":9.5},
    "B":{"Z":5,"name":"Boron","mass":10.81,"EN":2.04,"type":"metalloid","oxidation":[3], "S":5.9},
    "C":{"Z":6,"name":"Carbon","mass":12.011,"EN":2.55,"type":"nonmetal","oxidation":[4,-4], "S":5.7},
    "N":{"Z":7,"name":"Nitrogen","mass":14.007,"EN":3.04,"type":"nonmetal","oxidation":[-3,5,3], "S":191.6},
    "O":{"Z":8,"name":"Oxygen","mass":15.999,"EN":3.44,"type":"nonmetal","oxidation":[-2], "S":205.1},
    "F":{"Z":9,"name":"Fluorine","mass":18.998,"EN":3.98,"type":"nonmetal","oxidation":[-1], "S":202.8},
    "Ne":{"Z":10,"name":"Neon","mass":20.180,"EN":0.00,"type":"noble gas","oxidation":[], "S":146.3},
    # Period 3
    "Na":{"Z":11,"name":"Sodium","mass":22.990,"EN":0.93,"type":"metal","oxidation":[1], "S":51.3},
    "Mg":{"Z":12,"name":"Magnesium","mass":24.305,"EN":1.31,"type":"metal","oxidation":[2], "S":32.7},
    "Al":{"Z":13,"name":"Aluminium","mass":26.982,"EN":1.61,"type":"metal","oxidation":[3], "S":28.3},
    "Si":{"Z":14,"name":"Silicon","mass":28.085,"EN":1.90,"type":"metalloid","oxidation":[4], "S":18.8},
    "P":{"Z":15,"name":"Phosphorus","mass":30.974,"EN":2.19,"type":"nonmetal","oxidation":[-3,5,3], "S":41.1},
    "S":{"Z":16,"name":"Sulfur","mass":32.06,"EN":2.58,"type":"nonmetal","oxidation":[-2,6,4], "S":32.1},
    "Cl":{"Z":17,"name":"Chlorine","mass":35.45,"EN":3.16,"type":"nonmetal","oxidation":[-1,7,5,3,1], "S":223.1},
    "Ar":{"Z":18,"name":"Argon","mass":39.948,"EN":0.00,"type":"noble gas","oxidation":[], "S":154.8},
    # Period 4
    "K":{"Z":19,"name":"Potassium","mass":39.098,"EN":0.82,"type":"metal","oxidation":[1], "S":64.7},
    "Ca":{"Z":20,"name":"Calcium","mass":40.078,"EN":1.00,"type":"metal","oxidation":[2], "S":41.4},
    "Sc":{"Z":21,"name":"Scandium","mass":44.956,"EN":1.36,"type":"metal","oxidation":[3], "S":34.6},
    "Ti":{"Z":22,"name":"Titanium","mass":47.867,"EN":1.54,"type":"metal","oxidation":[4,3], "S":30.7},
    "V":{"Z":23,"name":"Vanadium","mass":50.942,"EN":1.63,"type":"metal","oxidation":[5,4,3,2], "S":28.9},
    "Cr":{"Z":24,"name":"Chromium","mass":51.996,"EN":1.66,"type":"metal","oxidation":[3,6,2], "S":23.8},
    "Mn":{"Z":25,"name":"Manganese","mass":54.938,"EN":1.55,"type":"metal","oxidation":[2,4,7], "S":32.0},
    "Fe":{"Z":26,"name":"Iron","mass":55.845,"EN":1.83,"type":"metal","oxidation":[3,2], "S":27.3},
    "Co":{"Z":27,"name":"Cobalt","mass":58.933,"EN":1.88,"type":"metal","oxidation":[2,3], "S":30.0},
    "Ni":{"Z":28,"name":"Nickel","mass":58.693,"EN":1.91,"type":"metal","oxidation":[2,3], "S":29.9},
    "Cu":{"Z":29,"name":"Copper","mass":63.546,"EN":1.90,"type":"metal","oxidation":[2,1], "S":33.1},
    "Zn":{"Z":30,"name":"Zinc","mass":65.38,"EN":1.65,"type":"metal","oxidation":[2], "S":41.6},
    "Ga":{"Z":31,"name":"Gallium","mass":69.723,"EN":1.81,"type":"metal","oxidation":[3], "S":41.6},
    "Ge":{"Z":32,"name":"Germanium","mass":72.63,"EN":2.01,"type":"metalloid","oxidation":[4,2], "S":31.1},
    "As":{"Z":33,"name":"Arsenic","mass":74.922,"EN":2.18,"type":"metalloid","oxidation":[3,5,-3], "S":35.1},
    "Se":{"Z":34,"name":"Selenium","mass":78.971,"EN":2.55,"type":"nonmetal","oxidation":[-2,4,6], "S":42.3},
    "Br":{"Z":35,"name":"Bromine","mass":79.904,"EN":2.96,"type":"nonmetal","oxidation":[-1,1,3,5,7], "S":152.2},
    "Kr":{"Z":36,"name":"Krypton","mass":83.798,"EN":0.00,"type":"noble gas","oxidation":[], "S":164.1},
    # Period 5
    "Rb":{"Z":37,"name":"Rubidium","mass":85.468,"EN":0.82,"type":"metal","oxidation":[1], "S":76.8},
    "Sr":{"Z":38,"name":"Strontium","mass":87.62,"EN":0.95,"type":"metal","oxidation":[2], "S":52.9},
    "Y":{"Z":39,"name":"Yttrium","mass":88.906,"EN":1.22,"type":"metal","oxidation":[3], "S":48.9},
    "Zr":{"Z":40,"name":"Zirconium","mass":91.224,"EN":1.33,"type":"metal","oxidation":[4], "S":39.4},
    "Nb":{"Z":41,"name":"Niobium","mass":92.906,"EN":1.6,"type":"metal","oxidation":[5,3], "S":36.4},
    "Mo":{"Z":42,"name":"Molybdenum","mass":95.96,"EN":2.16,"type":"metal","oxidation":[6,4,3], "S":28.7},
    "Tc":{"Z":43,"name":"Technetium","mass":98.0,"EN":1.9,"type":"metal","oxidation":[7,4], "S":0.0},
    "Ru":{"Z":44,"name":"Ruthenium","mass":101.07,"EN":2.2,"type":"metal","oxidation":[4,3], "S":28.9},
    "Rh":{"Z":45,"name":"Rhodium","mass":102.91,"EN":2.28,"type":"metal","oxidation":[3,4], "S":31.8},
    "Pd":{"Z":46,"name":"Palladium","mass":106.42,"EN":2.20,"type":"metal","oxidation":[2,4], "S":39.4},
    "Ag":{"Z":47,"name":"Silver","mass":107.87,"EN":1.93,"type":"metal","oxidation":[1], "S":42.6},
    "Cd":{"Z":48,"name":"Cadmium","mass":112.41,"EN":1.69,"type":"metal","oxidation":[2], "S":51.8},
    "In":{"Z":49,"name":"Indium","mass":114.82,"EN":1.78,"type":"metal","oxidation":[3,1], "S":57.8},
    "Sn":{"Z":50,"name":"Tin","mass":118.71,"EN":1.96,"type":"metal","oxidation":[4,2], "S":51.2},
    "Sb":{"Z":51,"name":"Antimony","mass":121.76,"EN":2.05,"type":"metalloid","oxidation":[3,5], "S":45.7},
    "Te":{"Z":52,"name":"Tellurium","mass":127.60,"EN":2.1,"type":"metalloid","oxidation":[4,6], "S":49.8},
    "I":{"Z":53,"name":"Iodine","mass":126.90,"EN":2.66,"type":"nonmetal","oxidation":[-1,1,3,5,7], "S":116.1},
    "Xe":{"Z":54,"name":"Xenon","mass":131.29,"EN":0.00,"type":"noble gas","oxidation":[2,4,6], "S":169.7},
    # Period 6 (Full set including Lanthanides)
    "Cs":{"Z":55,"name":"Cesium","mass":132.91,"EN":0.79,"type":"metal","oxidation":[1], "S":85.2},
    "Ba":{"Z":56,"name":"Barium","mass":137.33,"EN":0.89,"type":"metal","oxidation":[2], "S":69.4},
    "La":{"Z":57,"name":"Lanthanum","mass":138.91,"EN":1.1,"type":"metal","oxidation":[3], "S":56.9},
    "Ce":{"Z":58,"name":"Cerium","mass":140.12,"EN":1.12,"type":"metal","oxidation":[3,4], "S":56.9},
    "Pr":{"Z":59,"name":"Praseodymium","mass":140.91,"EN":1.13,"type":"metal","oxidation":[3], "S":66.9},
    "Nd":{"Z":60,"name":"Neodymium","mass":144.24,"EN":1.14,"type":"metal","oxidation":[3], "S":71.5},
    "Pm":{"Z":61,"name":"Promethium","mass":145.0,"EN":1.13,"type":"metal","oxidation":[3], "S":0.0},
    "Sm":{"Z":62,"name":"Samarium","mass":150.36,"EN":1.17,"type":"metal","oxidation":[3,2], "S":70.9},
    "Eu":{"Z":63,"name":"Europium","mass":151.96,"EN":1.2,"type":"metal","oxidation":[3,2], "S":70.3},
    "Gd":{"Z":64,"name":"Gadolinium","mass":157.25,"EN":1.2,"type":"metal","oxidation":[3], "S":66.5},
    "Tb":{"Z":65,"name":"Terbium","mass":158.93,"EN":1.2,"type":"metal","oxidation":[3], "S":73.2},
    "Dy":{"Z":66,"name":"Dysprosium","mass":162.50,"EN":1.22,"type":"metal","oxidation":[3], "S":73.0},
    "Ho":{"Z":67,"name":"Holmium","mass":164.93,"EN":1.23,"type":"metal","oxidation":[3], "S":71.5},
    "Er":{"Z":68,"name":"Erbium","mass":167.26,"EN":1.24,"type":"metal","oxidation":[3], "S":74.6},
    "Tm":{"Z":69,"name":"Thulium","mass":168.93,"EN":1.25,"type":"metal","oxidation":[3,2], "S":74.0},
    "Yb":{"Z":70,"name":"Ytterbium","mass":173.05,"EN":1.27,"type":"metal","oxidation":[3,2], "S":74.0},
    "Lu":{"Z":71,"name":"Lutetium","mass":174.97,"EN":1.27,"type":"metal","oxidation":[3], "S":51.5},
    "Hf":{"Z":72,"name":"Hafnium","mass":178.49,"EN":1.3,"type":"metal","oxidation":[4], "S":43.9},
    "Ta":{"Z":73,"name":"Tantalum","mass":180.95,"EN":1.5,"type":"metal","oxidation":[5], "S":41.4},
    "W":{"Z":74,"name":"Tungsten","mass":183.84,"EN":2.36,"type":"metal","oxidation":[6,4], "S":33.2},
    "Re":{"Z":75,"name":"Rhenium","mass":186.21,"EN":1.9,"type":"metal","oxidation":[7,4], "S":31.7},
    "Os":{"Z":76,"name":"Osmium","mass":190.23,"EN":2.2,"type":"metal","oxidation":[4,8], "S":31.5},
    "Ir":{"Z":77,"name":"Iridium","mass":192.22,"EN":2.20,"type":"metal","oxidation":[3,4], "S":35.2},
    "Pt":{"Z":78,"name":"Platinum","mass":195.08,"EN":2.28,"type":"metal","oxidation":[2,4], "S":41.6},
    "Au":{"Z":79,"name":"Gold","mass":196.97,"EN":2.54,"type":"metal","oxidation":[1,3], "S":47.4},
    "Hg":{"Z":80,"name":"Mercury","mass":200.59,"EN":2.00,"type":"metal","oxidation":[1,2], "S":75.9},
    "Tl":{"Z":81,"name":"Thallium","mass":204.38,"EN":1.62,"type":"metal","oxidation":[1,3], "S":64.1},
    "Pb":{"Z":82,"name":"Lead","mass":207.2,"EN":1.87,"type":"metal","oxidation":[2,4], "S":64.8},
    "Bi":{"Z":83,"name":"Bismuth","mass":208.98,"EN":2.02,"type":"metal","oxidation":[3,5], "S":53.4},
    "Po":{"Z":84,"name":"Polonium","mass":209.0,"EN":2.0,"type":"metalloid","oxidation":[2,4], "S":0.0},
    "At":{"Z":85,"name":"Astatine","mass":210.0,"EN":2.2,"type":"nonmetal","oxidation":[-1,1], "S":0.0},
    "Rn":{"Z":86,"name":"Radon","mass":222.0,"EN":0.00,"type":"noble gas","oxidation":[], "S":176.2},
    # Period 7 (Full set including Actinides and Superheavies)
    "Fr":{"Z":87,"name":"Francium","mass":223.0,"EN":0.7,"type":"metal","oxidation":[1], "S":0.0},
    "Ra":{"Z":88,"name":"Radium","mass":226.0,"EN":0.9,"type":"metal","oxidation":[2], "S":0.0},
    "Ac":{"Z":89,"name":"Actinium","mass":227.0,"EN":1.1,"type":"metal","oxidation":[3], "S":0.0},
    "Th":{"Z":90,"name":"Thorium","mass":232.04,"EN":1.3,"type":"metal","oxidation":[4], "S":51.8},
    "Pa":{"Z":91,"name":"Protactinium","mass":231.04,"EN":1.5,"type":"metal","oxidation":[5,4], "S":0.0},
    "U":{"Z":92,"name":"Uranium","mass":238.03,"EN":1.38,"type":"metal","oxidation":[3,4,6], "S":50.3},
    "Np":{"Z":93,"name":"Neptunium","mass":237.0,"EN":1.36,"type":"metal","oxidation":[5,4,6], "S":0.0},
    "Pu":{"Z":94,"name":"Plutonium","mass":244.0,"EN":1.28,"type":"metal","oxidation":[4,3,6], "S":0.0},
    "Am":{"Z":95,"name":"Americium","mass":243.0,"EN":1.3,"type":"metal","oxidation":[3], "S":0.0},
    "Cm":{"Z":96,"name":"Curium","mass":247.0,"EN":1.3,"type":"metal","oxidation":[3], "S":0.0},
    "Bk":{"Z":97,"name":"Berkelium","mass":247.0,"EN":1.3,"type":"metal","oxidation":[3,4], "S":0.0},
    "Cf":{"Z":98,"name":"Californium","mass":251.0,"EN":1.3,"type":"metal","oxidation":[3], "S":0.0},
    "Es":{"Z":99,"name":"Einsteinium","mass":252.0,"EN":1.3,"type":"metal","oxidation":[3], "S":0.0},
    "Fm":{"Z":100,"name":"Fermium","mass":257.0,"EN":1.3,"type":"metal","oxidation":[3,2], "S":0.0},
    "Md":{"Z":101,"name":"Mendelevium","mass":258.0,"EN":1.3,"type":"metal","oxidation":[3,2], "S":0.0},
    "No":{"Z":102,"name":"Nobelium","mass":259.0,"EN":1.3,"type":"metal","oxidation":[2,3], "S":0.0},
    "Lr":{"Z":103,"name":"Lawrencium","mass":262.0,"EN":1.3,"type":"metal","oxidation":[3], "S":0.0},
    "Rf":{"Z":104,"name":"Rutherfordium","mass":267.0,"EN":0.0,"type":"metal","oxidation":[4], "S":0.0},
    "Db":{"Z":105,"name":"Dubnium","mass":268.0,"EN":0.0,"type":"metal","oxidation":[5], "S":0.0},
    "Sg":{"Z":106,"name":"Seaborgium","mass":271.0,"EN":0.0,"type":"metal","oxidation":[6], "S":0.0},
    "Bh":{"Z":107,"name":"Bohrium","mass":272.0,"EN":0.0,"type":"metal","oxidation":[7], "S":0.0},
    "Hs":{"Z":108,"name":"Hassium","mass":270.0,"EN":0.0,"type":"metal","oxidation":[8], "S":0.0},
    "Mt":{"Z":109,"name":"Meitnerium","mass":276.0,"EN":0.0,"type":"metal","oxidation":[3], "S":0.0},
    "Ds":{"Z":110,"name":"Darmstadtium","mass":281.0,"EN":0.0,"type":"metal","oxidation":[2], "S":0.0},
    "Rg":{"Z":111,"name":"Roentgenium","mass":280.0,"EN":0.0,"type":"metal","oxidation":[1,3], "S":0.0},
    "Cn":{"Z":112,"name":"Copernicium","mass":285.0,"EN":0.0,"type":"metal","oxidation":[2], "S":0.0},
    "Nh":{"Z":113,"name":"Nihonium","mass":286.0,"EN":0.0,"type":"metal","oxidation":[1], "S":0.0},
    "Fl":{"Z":114,"name":"Flerovium","mass":289.0,"EN":0.0,"type":"metal","oxidation":[4,2], "S":0.0},
    "Mc":{"Z":115,"name":"Moscovium","mass":290.0,"EN":0.0,"type":"metal","oxidation":[3,1], "S":0.0},
    "Lv":{"Z":116,"name":"Livermorium","mass":293.0,"EN":0.0,"type":"nonmetal","oxidation":[4,2], "S":0.0},
    "Ts":{"Z":117,"name":"Tennessine","mass":294.0,"EN":0.0,"type":"nonmetal","oxidation":[1,3,5], "S":0.0},
    "Og":{"Z":118,"name":"Oganesson","mass":294.21,"EN":0.00,"type":"noble gas","oxidation":[], "S":0.0},
}

# -----------------------------------------------------------------------------
# 2. RULESETS (Polyatomic Ions, Solubility, Reactivity)
# -----------------------------------------------------------------------------
POLYATOMIC_IONS = {
    "hydroxide": ("OH", -1), "nitrate": ("NO3", -1), "sulfate": ("SO4", -2), 
    "carbonate": ("CO3", -2), "phosphate": ("PO4", -3), "ammonium": ("NH4", 1),
    "chlorate": ("ClO3", -1), "permanganate": ("MnO4", -1), "chromate": ("CrO4", -2),
    "bicarbonate": ("HCO3", -1), "bisulfate": ("HSO4", -1), "acetate": ("CH3COO", -1),
    "dichromate": ("Cr2O7", -2), "cyanide": ("CN", -1),
}
SOLUBILITY_RULES = {
    "always_soluble_cations": ["Na", "K", "NH4", "Li", "Rb"],
    "always_soluble_anions": ["NO3", "CH3COO", "ClO4"],
    "mostly_soluble_anions": {"Cl": ["Ag", "Pb", "Hg"], "SO4": ["Ba", "Sr", "Pb", "Ca"]},
    "mostly_insoluble_anions": ["CO3", "PO4", "S", "OH", "CrO4"],
    "hydroxides": ["Ca", "Sr", "Ba"],
}
REACTIVITY_SERIES = {
    "highly_reactive_metals": ["K", "Na", "Li", "Ba", "Ca"], 
    "moderately_reactive_metals": ["Mg", "Al", "Zn", "Fe"],
    "low_reactive_metals": ["Cu", "Ag", "Hg"],
    "inert_metals": ["Ir", "Pt", "Au"], 
}

# -----------------------------------------------------------------------------
# 3. THERMODYNAMIC DATASET 
# -----------------------------------------------------------------------------
THERMO_DATA = {
    # Compounds relevant to core examples
    "H2O(l)": {"ΔHf": -285.8, "ΔGf": -237.1, "S": 69.9},
    "H2O(g)": {"ΔHf": -241.8, "ΔGf": -228.6, "S": 188.8},
    "CO2(g)": {"ΔHf": -393.5, "ΔGf": -394.4, "S": 213.7},
    "CO(g)": {"ΔHf": -110.5, "ΔGf": -137.2, "S": 197.6},
    "CaCO3(s)": {"ΔHf": -1207.6, "ΔGf": -1128.8, "S": 92.9},
    "CaO(s)": {"ΔHf": -635.1, "ΔGf": -604.0, "S": 39.8},
    "C2H5OH(l)": {"ΔHf": -277.6, "ΔGf": -174.8, "S": 160.7}, # Ethanol
    "AgNO3(aq)": {"ΔHf": -124.4, "ΔGf": -33.7, "S": 140.9},
    "NaCl(aq)": {"ΔHf": -407.3, "ΔGf": -393.1, "S": 115.5},
    "NaNO3(aq)": {"ΔHf": -446.2, "ΔGf": -367.0, "S": 205.0},
    "AgCl(s)": {"ΔHf": -127.1, "ΔGf": -109.8, "S": 96.2},
    "HI(g)": {"ΔHf": 26.5, "ΔGf": 1.7, "S": 206.6},
    "NOCl(g)": {"ΔHf": 51.7, "ΔGf": 66.3, "S": 261.6},
    "NO(g)": {"ΔHf": 90.3, "ΔGf": 86.6, "S": 210.8},
    # Other common substances
    "NH3(g)": {"ΔHf": -46.1, "ΔGf": -16.5, "S": 192.8},
    "CH4(g)": {"ΔHf": -74.8, "ΔGf": -50.8, "S": 186.3}, 
    "Fe2O3(s)": {"ΔHf": -824.2, "ΔGf": -742.2, "S": 87.4},
    "HCl(aq)": {"ΔHf": -167.2, "ΔGf": -131.2, "S": 56.5},
    "NaOH(aq)": {"ΔHf": -470.1, "ΔGf": -419.2, "S": 48.2},
    "FeCl3(aq)": {"ΔHf": -400.0, "ΔGf": -310.0, "S": 280.0},
    "H2(g)": {"ΔHf": 0.0, "ΔGf": 0.0, "S": 130.7}, # Standard State Elements
    "I2(s)": {"ΔHf": 0.0, "ΔGf": 0.0, "S": 116.1},
    "Cl2(g)": {"ΔHf": 0.0, "ΔGf": 0.0, "S": 223.1},
    "O2(g)": {"ΔHf": 0.0, "ΔGf": 0.0, "S": 205.1},
}

# -----------------------------------------------------------------------------
# 4. KINETIC & EQUILIBRIA DATASET
# -----------------------------------------------------------------------------
REACTION_KINETICS = {
    "CaCO3+heat": {"Ea": 178.3, "A": 1e12, "order": 1, "note": "Decomposition: High barrier."},
    "C2H5OH+O2": {"Ea": 120.0, "A": 1e15, "order": 3, "note": "Combustion: Moderately high barrier, high pre-exponential factor."},
    "AgNO3+NaCl": {"Ea": 1.0, "A": 1e18, "order": 2, "note": "Precipitation: Near zero activation energy (instantaneous)."},
    "2HI->H2+I2": {"Ea": 186.0, "A": 3.98e-1, "order": 2, "note": "Gas phase decomposition."},
    "2NOCl->2NO+Cl2": {"Ea": 98.0, "A": 1.2e13, "order": 2, "note": "Gas phase decomposition (moderate barrier)."},
}
ACID_PKA = {
    "HCl": -7.0, "H2SO4": -3.0, "HNO3": -1.3,
    "CH3COOH": 4.76, "HCN": 9.21, 
    "NH4+": 9.25, 
    "H2O": 15.7, 
    "HF": 3.17, 
}
REDOX_POTENTIALS = {
    "MnO4- + 8H+ + 5e- -> Mn2+ + 4H2O": 1.51,
    "Cl2 + 2e- -> 2Cl-": 1.36,
    "Cr2O7-2 + 14H+ + 6e- -> 2Cr3+ + 7H2O": 1.33,
    "Ag+ + e- -> Ag": 0.80,
    "Fe3+ + e- -> Fe2+": 0.77,
    "Cu2+ + 2e- -> Cu": 0.34,
    "2H+ + 2e- -> H2": 0.00,
    "Fe2+ + 2e- -> Fe": -0.44,
    "Zn2+ + 2e- -> Zn": -0.76,
    "Al3+ + 3e- -> Al": -1.66,
    "Na+ + e- -> Na": -2.71,
}

# -----------------------------------------------------------------------------
# 5. CORE CLASS IMPLEMENTATION (ChemicalAnalysisUtility - The 'chi' module)
# -----------------------------------------------------------------------------

class chi:
    """
    A comprehensive utility for chemical mass balance, dynamic thermodynamics, 
    kinetics, pH simulation, and redox potential analysis. Fully self-contained 
    with a complete 118 element dataset and all necessary compound data.
    
    This class requires 'numpy' and 'sympy' to be installed.
    """
    def __init__(self, T_K: float = STANDARD_TEMPERATURE_K, verbose: bool = True):
        self.ELEMENTS = ELEMENTS
        self.THERMO_DATA = THERMO_DATA
        self.KINETIC_DATA = REACTION_KINETICS
        self.ACID_PKA = ACID_PKA
        self.REDOX_POTENTIALS = REDOX_POTENTIALS
        self.VERBOSE = verbose
        self.T = T_K
        self.R = R_GAS_CONSTANT
        self.F = F_FARADAY_CONSTANT
        self.TOLERANCE = TOLERANCE

    def _vprint(self, *args, **kwargs):
        """Prints output only if verbosity is enabled."""
        if self.VERBOSE:
            print(*args, **kwargs)

    # --- Utility Methods ---
    def _parse_formula(self, formula: str) -> Dict[str, int]:
        """Parses a chemical formula and returns a dictionary of element counts."""
        comp = defaultdict(int)
        formula = formula.replace('[', '(').replace(']', ')')
        formula = formula.replace('·', '.')
        formula_no_state = re.sub(r'\(([s l g a q)]+\)', '', formula)
        
        # Handle Hydrates
        hydrate_match = re.search(r'\.(\d+)(H2O)', formula_no_state)
        if hydrate_match:
            h2o_count = int(hydrate_match.group(1))
            comp["H"] += 2 * h2o_count
            comp["O"] += 1 * h2o_count
            formula_no_state = formula_no_state[:hydrate_match.start()]

        formula_stack = [(formula_no_state, 1)] 
        element_pattern = re.compile(r'([A-Z][a-z]?)(\d*)')
        
        while formula_stack:
            segment, multiplier = formula_stack.pop()
            if not segment: continue

            # Handle Polyatomic Groups
            group_match = re.search(r'\(([A-Z][a-z0-9]+)\)(\d*)', segment)
            
            if group_match:
                group_content = group_match.group(1)
                subscript = int(group_match.group(2) or 1)
                formula_stack.append((group_content, multiplier * subscript))
                formula_stack.append((segment[:group_match.start()], multiplier))
                formula_stack.append((segment[group_match.end():], multiplier))
            else:
                # Handle simple elements
                for (el, num) in element_pattern.findall(segment):
                    if el not in self.ELEMENTS:
                        raise ValueError(f"Unknown element symbol '{el}' in formula '{formula}'.")
                    count = int(num) if num else 1
                    comp[el] += count * multiplier
        
        if not comp:
             raise ValueError(f"Could not parse any elements from formula '{formula}'.")
             
        return dict(comp)

    def _get_species_state(self, formula: str) -> str:
        """Determines physical state using solubility rules and compound type."""
        formula_no_state = re.sub(r'\(([s l g a q)]+\)', '', formula)
        
        # Known states check
        if formula_no_state in ["H2O", "C6H6", "C2H5OH"]: return "(l)"
        if formula_no_state in ["H2", "O2", "N2", "CO2", "CH4", "C2H6", "C3H8"]: return "(g)"
        
        try:
            parsed = self._parse_formula(formula)
            elements = list(parsed.keys())
            
            # Cation detection (Metal or N for Ammonium)
            cation_el = next((el for el in elements if self.ELEMENTS.get(el, {}).get("type") == "metal" or el == "N"), None)
            
            if not cation_el: return "(s)"

            # Check general solubility rules
            if cation_el in SOLUBILITY_RULES["always_soluble_cations"] or any(anion in formula_no_state for anion in SOLUBILITY_RULES["always_soluble_anions"]): 
                return "(aq)"
                
            # Check exceptions for mostly soluble anions (Cl, SO4)
            if "Cl" in parsed and cation_el in SOLUBILITY_RULES["mostly_soluble_anions"]["Cl"]: return "(s)"
            
            # Check exceptions for mostly insoluble anions (CO3, PO4, S, OH)
            if any(anion in formula_no_state for anion in SOLUBILITY_RULES["mostly_insoluble_anions"]):
                if cation_el not in SOLUBILITY_RULES["always_soluble_cations"]:
                    return "(s)"
            
        except:
             return "(s)"

        return "(aq)"

    def _calculate_thermodynamic_value(self, balanced_equation: str, thermo_type: str) -> float:
        """Calculates $\Delta H$, $\Delta G$, or $\Delta S$ of reaction using Hess's Law."""
        try:
            left, right = balanced_equation.split("->")
        except ValueError:
            raise ValueError("Invalid equation format. Must use '->' to separate reactants and products.")
            
        # Pattern to capture Coefficient, Formula, and State
        pattern = r'(\d*)(\w+)\((s|l|g|aq)\)'
        reactants = re.findall(pattern, left)
        products = re.findall(pattern, right)

        total_reactants = 0.0
        total_products = 0.0

        for part, sign in [(reactants, -1), (products, 1)]:
            for coeff_str, formula, state in part:
                coeff = int(coeff_str or 1)
                key = f"{formula}({state})"
                
                # Fetch data from THERMO_DATA
                value = self.THERMO_DATA.get(key, {}).get(thermo_type, 0.0)
                
                # Use elemental standard entropy if compound data is missing and it's an element
                if thermo_type == 'S' and formula in self.ELEMENTS and value == 0.0 and coeff == 1:
                    value = self.ELEMENTS[formula].get("S", 0.0)
                
                # Standard state elements: $\Delta H_f^{\circ} = 0$, $\Delta G_f^{\circ} = 0$
                is_elemental_standard_state = (formula in self.ELEMENTS) and (thermo_type in ['ΔHf', 'ΔGf'])
                
                if value == 0.0 and not is_elemental_standard_state and self.VERBOSE:
                    self._vprint(f"Warning: Missing data for '{key}' ({thermo_type}). Assuming 0.0.")

                contribution = coeff * value
                
                if sign == -1: total_reactants += contribution
                else: total_products += contribution

        return total_products - total_reactants

    def _calculate_thermodynamics(self, balanced_equation: str, T_K: Optional[float] = None) -> Dict[str, Any]:
        """Calculates $\Delta H$, $\Delta S$, and T-dependent $\Delta G$."""
        T = T_K if T_K is not None else self.T
        
        delta_h = self._calculate_thermodynamic_value(balanced_equation, 'ΔHf')
        delta_s_J = self._calculate_thermodynamic_value(balanced_equation, 'S')
        delta_s_kJ = delta_s_J / 1000.0
        
        # Gibbs-Helmholtz: $\Delta G = \Delta H - T \Delta S$
        delta_g_calc = delta_h - (T * delta_s_kJ)
        
        spontaneity = "Spontaneous (Favorable)" if delta_g_calc < -self.TOLERANCE else "Non-spontaneous (Unfavorable)"
        if abs(delta_g_calc) < self.TOLERANCE:
             spontaneity = "Equilibrium or Near-Equilibrium"
             
        return {
            "Delta_H_kJ/mol": round(delta_h, 2),
            "Delta_S_J/molK": round(delta_s_J, 2),
            "Delta_G_kJ/mol": round(delta_g_calc, 2),
            "Spontaneity": spontaneity,
            "T_K": T,
        }

    # --- Core Public Methods ---
    
    def balance(self, equation: str, T_K: Optional[float] = None) -> None:
        """Balances equation, adds states, and prints full T-dependent thermodynamic report."""
        current_T = T_K if T_K is not None else self.T
        self._vprint(f"\n--- Running Mass Balance and T-Dependent Thermodynamic Analysis (T={current_T} K) ---")
        
        try:
            left, right = equation.replace(" ", "").split("->")
            reactants = left.split("+")
            products = right.split("+")
            species = reactants + products
            
            parsed_species = [self._parse_formula(s) for s in species]
            all_elements = {el for p in parsed_species for el in p}
            elems = sorted(list(all_elements))
            
            # Construct the stoichiometric matrix A (Elements x Species)
            A = np.zeros((len(elems), len(species)), dtype=int)
            for i, el in enumerate(elems):
                for j, parsed in enumerate(parsed_species):
                    count = parsed.get(el, 0)
                    A[i, j] = count if j < len(reactants) else -count

            A_matrix = Matrix(A)
            nullspace = A_matrix.nullspace()
            
            if not nullspace: 
                raise ValueError("Equation cannot be balanced (no non-trivial solution). Check input format.")
                
            x = nullspace[0]
            
            # Convert coefficients to smallest integers (Clear fractions)
            denominators = [v.q for v in x]
            lcm = 1
            for d in denominators:
                lcm = abs(lcm * d) // math.gcd(lcm, d)

            coeffs = [int(abs(v) * lcm) for v in x]
            
            # Ensure proper sign convention (Reactants positive)
            first_nonzero_index = next((i for i, c in enumerate(coeffs) if c != 0), -1)
            # The coefficients for reactants must be the same sign in the nullspace vector
            # We assume the first species is a reactant and enforce its coefficient to be positive
            if first_nonzero_index < len(reactants) and x[first_nonzero_index] < 0:
                coeffs = [-c for c in coeffs]
            
            # Simplify coefficients by dividing by GCD
            gcd_val = coeffs[0]
            for c in coeffs[1:]:
                gcd_val = math.gcd(gcd_val, c)
            
            if gcd_val > 1:
                coeffs = [c // gcd_val for c in coeffs]
            
            # Add States and Format Equation
            def format_species(species_list: List[str], coeffs_list: List[int]) -> str:
                parts = []
                for coeff, spec in zip(coeffs_list, species_list):
                    c_str = "" if coeff == 1 else str(coeff)
                    state = self._get_species_state(spec)
                    parts.append(f"{c_str}{spec}{state}")
                return " + ".join(parts)
            
            lhs = format_species(reactants, coeffs[:len(reactants)])
            rhs = format_species(products, coeffs[len(reactants):])
            balanced_eqn = f"{lhs} -> {rhs}"
            
            # Calculate Thermodynamics
            delta_results = self._calculate_thermodynamics(balanced_eqn, T_K=current_T)

            # Print Comprehensive Report
            print("\n--- STOICHIOMETRIC & T-DEPENDENT THERMODYNAMIC REPORT ---")
            print(f"**Input Equation:** {equation}")
            print(f"**Balanced Equation (with States):** {balanced_eqn}")
            print(f"**Stoichiometric Coefficients:** Reactants ({coeffs[:len(reactants)]}) : Products ({coeffs[len(reactants):]})")
            print("--- Thermodynamic Analysis ---")
            print(f"**Temperature (T):** {current_T} K")
            print(f"**Enthalpy ($\Delta H^{\circ}$):** {delta_results['Delta_H_kJ/mol']} kJ/mol ({'Exothermic' if delta_results['Delta_H_kJ/mol'] < 0 else 'Endothermic'})")
            print(f"**Entropy ($\Delta S^{\circ}$):** {delta_results['Delta_S_J/molK']} J/mol·K")
            print(f"**Gibbs Free Energy ($\Delta G$ at T):** {delta_results['Delta_G_kJ/mol']} kJ/mol")
            print(f"**Spontaneity:** {delta_results['Spontaneity']} (Reaction is { 'Product-Favored' if delta_results['Delta_G_kJ/mol'] < 0 else 'Reactant-Favored'} at {current_T} K)")
            print("-----------------------------------------------------------\n")

        except ValueError as ve:
            print(f"❌ **Error (Balance/Parsing):** {ve}")
        except Exception as e:
            print(f"❌ **Error (System Failure):** An unexpected error occurred during balancing: {e}")

    def predict(self, *symbols) -> None:
        """Analyzes and prints all possible simple compound formations, bond types, and properties."""
        sym_list = [s for s in symbols if s in self.ELEMENTS]
        
        if len(sym_list) < 2:
            print("--- Compound Prediction Report ---")
            print("Error: Need at least two valid elements for compound formation analysis.")
            return

        print("\n" + "="*75)
        print(f"       COMPREHENSIVE COMPOUND PREDICTION REPORT for {', '.join(sym_list)}       ")
        print("="*75)
        
        results = []
        element_data = {s: self.ELEMENTS[s] for s in sym_list}
        
        for el1, el2 in combinations(sym_list, 2):
            data1, data2 = element_data[el1], element_data[el2]
            
            if data1["EN"] == data2["EN"]: continue

            # Electronegativity determines cation/anion roles
            cation_el, anion_el = (el1, el2) if data1["EN"] < data2["EN"] else (el2, el1)
            cation_data, anion_data = (data1, data2) if data1["EN"] < data2["EN"] else (data2, data1)

            delta_en = abs(data1["EN"] - data2["EN"])
            
            # 1. Determine Bond Type
            is_metal = cation_data["type"] in ["metal", "metalloid"]
            is_nonmetal = anion_data["type"] in ["nonmetal", "metalloid", "noble gas"] 
            
            if is_metal and is_nonmetal and delta_en > 1.7:
                bond_type = "Ionic"
            elif delta_en > 1.7:
                bond_type = "Highly Polar Covalent (Approaching Ionic)"
            elif delta_en > 0.4:
                bond_type = "Polar Covalent"
            else:
                bond_type = "Nonpolar Covalent"
                
            # 2. Formula Generation (Criss-Cross Rule using primary oxidation states)
            ox1 = abs(cation_data.get("oxidation", [1])[0])
            ox2 = abs(anion_data.get("oxidation", [1])[0])
            
            if ox1 == 0 or ox2 == 0: 
                formula = f"{cation_el}{anion_el}"
                sub1, sub2 = 1, 1
            else:
                gcd_ox = math.gcd(ox1, ox2)
                sub1 = ox2 // gcd_ox
                sub2 = ox1 // gcd_ox
                
                # Format formula string
                f1_str = str(sub1) if sub1 > 1 else ""
                f2_str = str(sub2) if sub2 > 1 else ""
                formula = f"{cation_el}{f1_str}{anion_el}{f2_str}"
            
            # 3. Calculate Molar Mass
            try:
                parsed_formula = self._parse_formula(formula)
                molar_mass = sum(self.ELEMENTS[el]["mass"] * count for el, count in parsed_formula.items())
            except:
                molar_mass = "N/A"
                
            results.append({
                "Elements": f"{el1} + {el2}",
                "Formula": formula,
                "Molar Mass (g/mol)": round(molar_mass, 3) if isinstance(molar_mass, (int, float)) else molar_mass,
                "Bond Type": bond_type,
                "Electronegativity Difference": round(delta_en, 2)
            })

        if not results:
            print("No simple two-element compounds could be predicted from the provided elements.")
            return

        # Print results in a neat format
        print(f"{'Elements':<15} {'Formula':<15} {'Molar Mass (g/mol)':<25} {'Bond Type':<35} {'ΔEN':<5}")
        print("-" * 15 + " " + "-" * 15 + " " + "-" * 25 + " " + "-" * 35 + " " + "-" * 5)
        for res in results:
            print(f"{res['Elements']:<15} {res['Formula']:<15} {res['Molar Mass (g/mol)']:<25} {res['Bond Type']:<35} {res['Electronegativity Difference']:<5}")
            
        print("="*75 + "\n")

    def analyze_reaction_kinetics(self, reaction_key: str, T_C: float, reactant_M: float) -> None:
        """Calculates kinetic parameters (k and Rate) using Arrhenius and Rate Law."""
        self._vprint(f"\n--- Running Kinetic Analysis for Reaction: '{reaction_key}' ---")
        
        data = self.KINETIC_DATA.get(reaction_key)
        if not data:
            print(f"❌ **Error (Kinetics):** Reaction key '{reaction_key}' not found in KINETIC_DATA.")
            return

        T_K = T_C + 273.15
        Ea = data['Ea'] # kJ/mol
        A = data['A']
        order = data['order']
        
        try:
            # 1. Calculate Rate Constant (k) using Arrhenius Equation: k = A * exp(-Ea / RT)
            # R_GAS_CONSTANT is 8.314/1000 = 0.008314 kJ/mol·K
            exponent = -Ea / (self.R * T_K)
            k = A * math.exp(exponent)
            
            # 2. Calculate Reaction Rate: Rate = k [Reactant]^order
            rate = k * (reactant_M ** order)
            
            # Determine units for k
            k_unit = f"(L/mol)^{order - 1} / s" if order > 1 else ("1/s" if order == 1 else "mol/L·s")
            
            print("\n--- KINETIC REPORT ---")
            print(f"**Reaction:** {reaction_key} ({data['note']})")
            print(f"**Temperature:** {T_C}°C ({T_K:.2f} K)")
            print(f"**Activation Energy ($E_a$):** {Ea} kJ/mol")
            print(f"**Reaction Order ($n$):** {order}")
            print(f"**Reactant Concentration ([M]):** {reactant_M} mol/L")
            print("--- Results ---")
            print(f"**Rate Constant ($k$):** {k:.2e} {k_unit}")
            print(f"**Reaction Rate:** {rate:.2e} mol/L·s")
            print("------------------------\n")

        except Exception as e:
            print(f"❌ **Error (Kinetics Calculation):** {e}")

    def simulate_pH(self, acid_base_name: str, concentration: float) -> None:
        """Calculates pH for strong and weak acids/bases."""
        self._vprint(f"\n--- Running pH Simulation for {acid_base_name} at {concentration} M ---")
        
        is_acid = acid_base_name in self.ACID_PKA
        is_strong_base = "OH" in acid_base_name
        
        try:
            if is_acid:
                pKa = self.ACID_PKA.get(acid_base_name)
                
                if pKa is None or pKa < 0: # Strong Acid (e.g., HCl)
                    h_plus = concentration
                    acid_type = "Strong Acid"
                else: # Weak Acid
                    Ka = 10**(-pKa)
                    # Approximation: [H+] = sqrt(Ka * C)
                    h_plus = math.sqrt(Ka * concentration)
                    acid_type = f"Weak Acid (pKa={pKa})"
                    
                pH = -math.log10(h_plus)
                pOH = 14.0 - pH
                
                print("\n--- pH SIMULATION REPORT (ACID) ---")
                print(f"**Substance:** {acid_base_name} ({acid_type})")
                print(f"**Concentration:** {concentration} M")
                print("--- Results ---")
                print(f"**[$H^+$]:** {h_plus:.2e} M")
                print(f"**pH:** {pH:.2f}")
                print(f"**pOH:** {pOH:.2f}")
                print("-----------------------------------\n")

            elif is_strong_base: # Simple check for strong base (e.g., NaOH)
                oh_minus = concentration * 1 # Assuming 1 OH- per mole
                pOH = -math.log10(oh_minus)
                pH = 14.0 - pOH
                
                print("\n--- pH SIMULATION REPORT (BASE) ---")
                print(f"**Substance:** {acid_base_name} (Strong Base approximation)")
                print(f"**Concentration:** {concentration} M")
                print("--- Results ---")
                print(f"**[$OH^-$]:** {oh_minus:.2e} M")
                print(f"**pOH:** {pOH:.2f}")
                print(f"**pH:** {pH:.2f}")
                print("----------------------------------\n")
                
            else:
                print(f"❌ **Error (pH):** Substance '{acid_base_name}' not recognized as a defined acid or strong base.")
                
        except ValueError:
            print(f"❌ **Error (pH Calculation):** Concentration must be positive.")
        except Exception as e:
             print(f"❌ **Error (pH System Failure):** {e}")

    def analyze_redox(self, half_reaction_1: str, half_reaction_2: str) -> None:
        """Calculates cell potential and spontaneity for a standard cell."""
        self._vprint(f"\n--- Running Redox Analysis ---")
        
        potential_1 = self.REDOX_POTENTIALS.get(half_reaction_1)
        potential_2 = self.REDOX_POTENTIALS.get(half_reaction_2)
        
        if potential_1 is None or potential_2 is None:
            print("❌ **Error (Redox):** One or both half-reactions not found in REDOX_POTENTIALS.")
            return
            
        # Determine Anode (Oxidation) and Cathode (Reduction)
        # Higher reduction potential (E) is the Cathode (Reduction)
        if potential_1 >= potential_2:
            E_red = potential_1
            E_ox = potential_2
            reduction_rxn = half_reaction_1
            oxidation_rxn = half_reaction_2
        else:
            E_red = potential_2
            E_ox = potential_1
            reduction_rxn = half_reaction_2
            oxidation_rxn = half_reaction_1

        # Calculate Cell Potential (E°cell)
        E_cell = E_red - E_ox

        # Function to safely extract number of electrons
        def get_n(rxn):
             match = re.search(r'(\d+)e-', rxn)
             return int(match.group(1)) if match else 1

        n_red = get_n(reduction_rxn)
        n_ox = get_n(oxidation_rxn)
        
        # Determine transferred electrons (n) as the smallest for a simple demo
        n = min(n_red, n_ox)
        
        # $\Delta G^{\circ} = -n F E^{\circ}_{\text{cell}}$ (F is 96.485 kJ/V·mol)
        delta_g_standard = -n * self.F * E_cell
        
        spontaneity = "Spontaneous (Favorable)" if E_cell > self.TOLERANCE else "Non-spontaneous (Unfavorable)"
        if abs(E_cell) < self.TOLERANCE:
             spontaneity = "Equilibrium or Near-Equilibrium"

        print("\n--- REDOX ANALYSIS REPORT ---")
        print(f"**Reduction Half-Reaction (Cathode):** {reduction_rxn} ($E^{\circ}$ = {E_red} V)")
        print(f"**Oxidation Half-Reaction (Anode):** {oxidation_rxn} ($E^{\circ}$ = {E_ox} V)")
        print("--- Results ---")
        print(f"**Net Standard Cell Potential ($E^{\circ}_{\text{cell}}$):** {E_cell:.3f} V")
        print(f"**Number of Electrons Transferred ($n$):** (Approximation) {n}")
        print(f"**Standard Gibbs Free Energy ($\Delta G^{\circ}$):** {delta_g_standard:.2f} kJ/mol")
        print(f"**Spontaneity:** {spontaneity} (Reaction is { 'Product-Favored' if E_cell > 0 else 'Reactant-Favored'} under standard conditions)")
        print("-----------------------------\n")
        
# -----------------------------------------------------------------------------
# 6. DEMONSTRATION SCRIPT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    
    print("=========================================================")
    print("       CHI MODULE COMPREHENSIVE DEMONSTRATION SCRIPT       ")
    print("=========================================================")
    
    # Import ready-to-use chi object from the sia package
    from sia import chi

    
    # -------------------------------------------------------------------------
    # USE CASE 1: Mass Balance and Thermodynamics (balance method)
    # -------------------------------------------------------------------------
    print("\n\n#########################################################")
    print("DEMO 1: CHEMICAL BALANCE & THERMODYNAMICS ($\Delta G$)")
    print("#########################################################")
    
    # Example 1: Simple combustion
    chi.balance("C2H5OH + O2 -> CO2 + H2O")
    
    # Example 2: Double displacement (precipitation) at non-standard T (350 K)
    chi.balance("AgNO3 + NaCl -> AgCl + NaNO3", T_K=350.0)
    
    # Example 3: Thermal decomposition (Endothermic)
    chi.balance("CaCO3 -> CaO + CO2")
    
    
    # -------------------------------------------------------------------------
    # USE CASE 2: Compound Prediction and Bond Analysis (predict method)
    # -------------------------------------------------------------------------
    print("\n\n#########################################################")
    print("DEMO 2: COMPOUND PREDICTION (Formula, Molar Mass, Bond Type)")
    print("#########################################################")
    
    # Analyze Lithium, Oxygen, and Carbon
    chi.predict("Li", "O", "C")
    
    
    # -------------------------------------------------------------------------
    # USE CASE 3: Reaction Kinetics (analyze_reaction_kinetics method)
    # -------------------------------------------------------------------------
    print("\n\n#########################################################")
    print("DEMO 3: REACTION KINETICS (Arrhenius & Rate Law)")
    print("#########################################################")
    
    # Example: Decomposition of NOCl at 50°C with 0.5 M concentration
    chi.analyze_reaction_kinetics("2NOCl->2NO+Cl2", T_C=50.0, reactant_M=0.5)

    
    # -------------------------------------------------------------------------
    # USE CASE 4: pH Simulation (simulate_pH method)
    # -------------------------------------------------------------------------
    print("\n\n#########################################################")
    print("DEMO 4: pH SIMULATION (Strong/Weak Acids & Bases)")
    print("#########################################################")
    
    # Example 1: Strong Acid (HCl)
    chi.simulate_pH("HCl", 0.01)
    
    # Example 2: Weak Acid (Acetic Acid - CH3COOH)
    chi.simulate_pH("CH3COOH", 0.1)
    
    # Example 3: Strong Base (NaOH)
    chi.simulate_pH("NaOH", 0.005")


    # -------------------------------------------------------------------------
    # USE CASE 5: Redox Analysis (analyze_redox method)
    # -------------------------------------------------------------------------
    print("\n\n#########################################################")
    print("DEMO 5: REDOX ANALYSIS (Cell Potential & $\Delta G^{\circ}$)")
    print("#########################################################")
    
    # Example: Zinc/Copper Cell (Spontaneous: Cu is reduced, Zn is oxidized)
    # Cu2+ + 2e- -> Cu (0.34 V)
    # Zn2+ + 2e- -> Zn (-0.76 V)
    chi.analyze_redox("Cu2+ + 2e- -> Cu", "Zn2+ + 2e- -> Zn")
    
    # Example: Fe3+ reducing Ag (Non-spontaneous)
    # Fe3+ + e- -> Fe2+ (0.77 V)
    # Ag+ + e- -> Ag (0.80 V)
    chi.analyze_redox("Fe3+ + e- -> Fe2+", "Ag+ + e- -> Ag")


    print("=========================================================")
    print("DEMONSTRATION COMPLETE.")
    # Prevents immediate closing after all output is generated
    input("Press Enter to exit...")
