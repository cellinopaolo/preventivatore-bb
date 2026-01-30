import streamlit as st
import json
import os
import math

st.set_page_config(page_title="B&B Preventivi", layout="centered")

st.markdown("""
    <style>
    .report-text { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #d1d5db; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .stRadio > div { flex-direction: row; }
    hr { margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 B&B Preventivi Pro v6.7.7")

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

    # --- Logica Posa Fortis ---
    resa_finale = float(info.get("pz_m2", 1.0))
    if mondo == "Mattoni" and "Fortis" in gamma:
        scelta_posa = st.radio("Configurazione Posa:", ["Di Piatto (62 pz/m2)", "Di Coltello (100 pz/m2)"])
        resa_finale = 62.0 if "Piatto" in scelta_posa else 100.0

    # --- Input Dati ---
    col1, col2 = st.columns(2)
    with col1:
        qty_in = st.number_input("Quantità da ordinare", min_value=0.0, step=0.1, format="%.2f")
        unit_var = st.radio("Unità di misura inserita", ["m2", "Pezzi"])
    with col2:
        sconto_man = st.number_input("Sconto % (0=Auto)", min_value=0, max_value=100)
        iva_check = st.checkbox("IVA 22% (Privato)")

    trasp = st.number_input("Trasporto (€)", min_value=0.0)
    plus = st.number_input("Extra (+)", min_value=0.0)

    if st.button("GENERA PREVENTIVO", use_container_width=True):
        valore_conf = float(info.get("pz_scatola", 1.0))
        
        # Logica di calcolo
        if unit_var == "m2":
            qty_base = qty_in * resa_finale
            unita_risultato = "m2"
        else:
            qty_base = qty_in
            unita_risultato = "Pezzi"
        
        # Arrotondamento colli (escluso Legno)
        if mondo == "Legno":
            qty_eff_pz = qty_base + plus
            num_colli = "N/A"
        else:
            num_colli = math.ceil(round(qty_base / valore_conf, 4))
            qty_eff_pz = (num_colli * valore_conf) + plus

        # Calcolo MQ equivalenti per la visualizzazione
        mq_equivalenti = qty_eff_pz / resa_finale

        sconto_f = (sconto_man / 100) if sconto_man > 0 else (0.50 if qty_eff_pz >= info["pz_bancale"] else 0.45)
        netto = info["prezzo"] * (1 - sconto_f)
        imponibile = (netto * qty_eff_pz) + trasp

        # --- Visualizzazione ---
        st.markdown(f"""
        <div class="report-text">
        <h3 style='margin-top:0;'>RIEPILOGO ORDINE</h3>
        <strong>Articolo:</strong> {modello}<br>
        <hr>
        <strong>Quantità Finale:</strong> {qty_in if unit_var == "m2" else qty_eff_pz:.2f} {unit_var}<br>
        {f"<em>(Equivalenti a: {mq_equivalenti:.2f} m2)</em><br>" if unit_var == "Pezzi" else ""}
        <strong>N. Colli:</strong> {num_colli}<br>
        <strong>Resa:</strong> {resa_finale} pz/m2<br>
        <hr>
        <strong>Prezzo Netto:</strong> {netto:.3f} €<br>
        <strong>Sconto:</strong> {sconto_f*100:.0f}%<br>
        <hr>
        <span style='font-size: 1.2em;'><strong>{"TOTALE IVATO" if iva_check else "TOTALE IMPONIBILE"}: 
        {(imponibile*1.22 if iva_check else imponibile):.2f} €</strong></span>
        </div>
        """, unsafe_allow_html=True)
