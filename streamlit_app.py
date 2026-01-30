import streamlit as st
import json
import os
import math

st.set_page_config(page_title="B&B Preventivi", layout="centered")

# Stile "Riepilogo Ordine" - Pulito e Professionale
st.markdown("""
    <style>
    .report-text { 
        font-family: 'Segoe UI', sans-serif; 
        background-color: #ffffff; 
        padding: 25px; 
        border-radius: 5px; 
        border: 1px solid #eeeeee;
    }
    .stRadio > div { flex-direction: row; gap: 20px; }
    hr { border: 0; border-top: 1px solid #dddddd; margin: 15px 0; }
    .totale-box { font-size: 1.3em; font-weight: bold; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 B&B Preventivi Pro v6.7.8")

BASE_FOLDER = "Listini_BB"
categorie = ["Mattoni", "Pietra", "Legno"]

mondo = st.sidebar.selectbox("Mondo", categorie)
path_cat = os.path.join(BASE_FOLDER, mondo)

if os.path.exists(path_cat):
    listini = sorted([f.replace(".json", "") for f in os.listdir(path_cat) if f.endswith(".json")])
    gamma = st.sidebar.selectbox("Linea Prodotto", listini) if listini else None
else:
    st.error("Database non trovato."); st.stop()

if gamma:
    with open(os.path.join(path_cat, f"{gamma}.json"), 'r') as f:
        prodotti = json.load(f)
    
    modello = st.selectbox("Seleziona Modello", sorted(prodotti.keys()))
    info = prodotti[modello]

    # --- Logica Posa Fortis (Senza "Standard") ---
    resa_finale = float(info.get("pz_m2", 1.0))
    if mondo == "Mattoni" and "Fortis" in gamma:
        st.write("### Configurazione Posa Fortis")
        scelta_posa = st.radio("Seleziona Posa:", ["Di Piatto (62 pz/m2)", "Di Coltello (100 pz/m2)"])
        resa_finale = 62.0 if "Piatto" in scelta_posa else 100.0

    # --- Area Input ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        qty_in = st.number_input("Quantità", min_value=0.0, step=0.1, format="%.2f")
        unit_var = st.radio("Unità inserita", ["m2", "Pezzi"])
    with c2:
        sconto_man = st.number_input("Sconto % (0=Auto)", min_value=0, max_value=100)
        iva_check = st.checkbox("IVA 22% (Privato)")

    trasp = st.number_input("Trasporto (€)", min_value=0.0)
    plus = st.number_input("Extra (+)", min_value=0.0)

    if st.button("GENERA PREVENTIVO", use_container_width=True):
        valore_conf = float(info.get("pz_scatola", 1.0))
        
        # Calcolo base
        qty_lavoro = qty_in
        qty_base_pz = (qty_in * resa_finale) if unit_var == "m2" else qty_in
        
        # Logica Arrotondamento
        if mondo == "Legno":
            qty_eff_pz = qty_base_pz + plus
            num_colli = "N/A"
        else:
            num_colli = math.ceil(round(qty_base_pz / valore_conf, 4))
            qty_eff_pz = (num_colli * valore_conf) + plus

        # Calcolo Metri Quadri per riepilogo
        mq_risultanti = qty_eff_pz / resa_finale

        # Sconto e Prezzi
        sconto_f = (sconto_man / 100) if sconto_man > 0 else (0.50 if qty_eff_pz >= info["pz_bancale"] else 0.45)
        netto = info["prezzo"] * (1 - sconto_f)
        imponibile = (netto * qty_eff_pz) + trasp
        totale_finale = imponibile * 1.22 if iva_check else imponibile

        # --- OUTPUT IN STILE "RIEPILOGO ORDINE" ---
        st.markdown(f"""
        <div class="report-text">
            <h2 style='margin-top:0;'>RIEPILOGO ORDINE</h2>
            <strong>Articolo:</strong> {modello}
            <hr>
            <strong>Quantità Finale:</strong> {qty_eff_pz if unit_var == "Pezzi" else mq_risultanti:.2f} {unit_var}<br>
            {f"<em>(Equivalenti a: {mq_risultanti:.2f} m2)</em><br>" if unit_var == "Pezzi" else ""}
            <strong>N. Colli:</strong> {num_colli}<br>
            <strong>Resa:</strong> {resa_finale} pz/m2
            <hr>
            <strong>Prezzo Netto:</strong> {netto:.3f} €<br>
            <strong>Sconto:</strong> {sconto_f*100:.0f}%
            <hr>
            <div class="totale-box">
                {"TOTALE IVATO" if iva_check else "TOTALE IMPONIBILE"}: {totale_finale:.2f} €
            </div>
        </div>
        """, unsafe_allow_html=True)
        
