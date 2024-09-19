                            # if reaction_name == "Carbon Dioxide Reduction":
                            #     if key == "Main product":
                            #         CO2RR_main_product = st.selectbox(' ', ('Acetate', 'Carbon monoxide(CO)',"Methanal(CH2O)",
                            #                                                 'Formate', 'Ethylene(C2H4)', 'Ethanol(CH3CH2OH)','Ethanal',
                            #                                                 'Methanol', "Methane(CH4)", "Hydrogen(H2)", "Ethane (C2H6)", "C3 products",
                            #                                                 ), label_visibility="collapsed")
                            #         results = CO2RR_main_product
                            #     elif key == "Other product (FE > 10%)":
                            #         CO2RR_other_product = st.multiselect(' ', ('Acetate', 'Carbon monoxide(CO)',"Methanal(CH2O)",
                            #                                                 'Formate', 'Ethylene(C2H4)', 'Ethanol(CH3CH2OH)','Ethanal',
                            #                                                 'Methanol', "Methane(CH4)", "Hydrogen(H2)","Ethane (C2H6)","C3 products","NA",
                            #                                                 ), label_visibility="collapsed")
                            #         results = ";".join(CO2RR_other_product)
                            # elif reaction_name == "Carbon Dioxide Reduction":
                            #     if key == "Main product":
                            #         CORR_main_product = st.selectbox(' ', ('Acetate', 'Carbon monoxide(CO)', "Methanal(CH2O)",
                            #                                                 'Formate', 'Ethylene(C2H4)', 'Ethanol(CH3CH2OH)','Ethanal',
                            #                                                 'Methanol', "Methane(CH4)", "Hydrogen(H2)", "Ethane (C2H6)", "C3 products",
                            #                                                 ), label_visibility="collapsed")
                            #         results = CORR_main_product
                            #     elif key == "Other product (FE > 10%)":
                            #         CORR_other_product = st.multiselect(' ', ('Acetate', 'Carbon monoxide(CO)',"Methanal(CH2O)",
                            #                                                 'Formate', 'Ethylene(C2H4)', 'Ethanol(CH3CH2OH)','Ethanal',
                            #                                                 'Methanol', "Methane(CH4)", "Hydrogen(H2)","Ethane (C2H6)","C3 products","NA",
                            #                                                 ), label_visibility="collapsed")
                            #         results = ";".join(CORR_other_product)
                            # elif reaction_name == "Ammonia Synthesis":
                            #     if key == "Isotope labeling":
                            #         results = st.radio(
                            #             "Are isotope labelling experiments performed?",
                            #             ["yes", "no"],)
                            #     elif key == "Reactant":
                            #         results = st.selectbox(' ', ('N2', 'NO/NO2/NO3', "NO3-/NO2-/NO-"
                            #                             ), label_visibility="collapsed")
                            # elif reaction_name == "Epoxide Production":
                            #     if key == "Main product":
                            #         results = st.selectbox(' ', ('cyclooctene oxide',
                            #                                      'propylene oxide',
                            #                                      "ethylene oxide",
                            #                                      'acrolein',
                            #                                      'acrylic acid',
                            #                                      'allyl alcohol',
                            #                                      'propyiene glycol',
                            #                                      'acetone',
                            #
                            #                            ), label_visibility="collapsed")
                            # elif reaction_name == "Nitrogen Oxidation Reaction":
                            #     if key == "Main product":
                            #         results = st.selectbox(' ', ('NO3-', 'NO2-', 'NO-'
                            #                             ), label_visibility="collapsed")
                            #         st.write()
                            # elif reaction_name == "NH3 Oxidation Reaction":
                            #     if key == "Main product":
                            #         results = st.selectbox(' ', ('N2', 'N2O',
                            #                             ), label_visibility="collapsed")
                            #         st.write()
                            # elif reaction_name =="Urea Oxidation Reaction":
                            #     if key == "Main product":
                            #         urea_product = st.multiselect(' ', ('N2', 'NO-',
                            #                                                 'NO2-', 'NO3-', 'CO2',
                            #                                                 'CO'
                            #                                                 ), label_visibility="collapsed")
                            #         results = ";".join(urea_product)


# Define the dictionary with reaction names as keys
reaction_options = {
    "Carbon Dioxide Reduction": {
        "Main product": [
            'Acetate', 'Carbon monoxide(CO)', "Methanal(CH2O)", 'Formate', 'Ethylene(C2H4)',
            'Ethanol(CH3CH2OH)', 'Ethanal', 'Methanol', "Methane(CH4)", "Hydrogen(H2)",
            "Ethane (C2H6)", "C3 products"
        ],
        "Other product (FE > 10%)": [
            'Acetate', 'Carbon monoxide(CO)', "Methanal(CH2O)", 'Formate', 'Ethylene(C2H4)',
            'Ethanol(CH3CH2OH)', 'Ethanal', 'Methanol', "Methane(CH4)", "Hydrogen(H2)",
            "Ethane (C2H6)", "C3 products", "NA"
        ]
    },
    "CORR": {
        "Main product": [
            'Acetate', 'Carbon monoxide(CO)', "Methanal(CH2O)", 'Formate', 'Ethylene(C2H4)',
            'Ethanol(CH3CH2OH)', 'Ethanal', 'Methanol', "Methane(CH4)", "Hydrogen(H2)",
            "Ethane (C2H6)", "C3 products"
        ],
        "Other product (FE > 10%)": [
            'Acetate', 'Carbon monoxide(CO)', "Methanal(CH2O)", 'Formate', 'Ethylene(C2H4)',
            'Ethanol(CH3CH2OH)', 'Ethanal', 'Methanol', "Methane(CH4)", "Hydrogen(H2)",
            "Ethane (C2H6)", "C3 products", "NA"
        ]
    },
    "Ammonia Synthesis": {
        "Isotope labeling": [
            "yes", "no"
        ],
        "Reactant": [
            'N2', 'NO/NO2/NO3', "NO3-/NO2-/NO-"
        ]
    },
    "Epoxide Production": {
        "Main product": [
            'cyclooctene oxide', 'propylene oxide', "ethylene oxide", 'acrolein', 'acrylic acid',
            'allyl alcohol', 'propyiene glycol', 'acetone'
        ]
    },
    "Nitrogen Oxidation Reaction": {
        "Main product": [
            'NO3-', 'NO2-', 'NO-'
        ]
    },
    "NH3 Oxidation Reaction": {
        "Main product": [
            'N2', 'N2O'
        ]
    },
    "Urea Oxidation Reaction": {
        "Main product": [
            'N2', 'NO-', 'NO2-', 'NO3-', 'CO2', 'CO'
        ]
    }
}
