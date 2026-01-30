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

st.title("💎 B&B Preventivi Pro v6.8.6")

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
        st.write("### Configurazione Posa Fortis")
        scelta_posa = st.radio("Configurazione Posa:", ["Di Piatto (62 pz/m2)", "Di Coltello (100 pz/m2)"])
        resa_finale = 62.0 if "Piatto" in scelta_posa else 100.0

    # --- Input Dati ---
    col1, col2 = st.columns(2)
    with col1:
        qty_in = st.number_input("Quantità Richiesta", min_value=0.0, step=0.1, format="%.2f")
        unit_var = st.radio("Unità inserita", ["m2", "Pezzi"])
    with col2:
        sconto_man = st.number_input("Sconto % (0=Auto)", min_value=0, max_value=100)
        iva_check = st.checkbox("IVA 22% (Privato)")

    trasp = st.number_input("Trasporto (€)", min_value=0.0)
    plus = st.number_input("Extra (+)", min_value=0.0)

    if st.button("GENERA PREVENTIVO", use_container_width=True):
        valore_conf = float(info.get("pz_scatola", 1.0))
        valore_bancale = float(info.get("pz_bancale", 1.0))
        
        # 1. Calcolo Base Pezzi
        qty_base = (qty_in * resa_finale) if unit_var == "m2" else qty_in
        
        # 2. LOGICA ARROTONDAMENTO REVISIONATA
        gamme_potenziali_bancali = ["Genesis", "Cotto", "Fortis", "Croma"]
        
        # Verifica se è una gamma a bancali MA esclude listelli (LS) e angolari (AG)
        is_bancale_gamma = any(g in gamma for g in gamme_potenziali_bancali)
        is_pezzo_speciale = any(x in modello for x in ["LS", "AG"])
        
        arrotonda_bancale = is_bancale_gamma and not is_pezzo_speciale

        if mondo == "Legno":
            qty_eff_finale = qty_base + plus
            num_mostra = None
            tipo_collo = ""
        elif arrotonda_bancale:
            # Arrotondamento al BANCALE INTERO
            num_bancali = math.ceil(round(qty_base / valore_bancale, 4))
            qty_eff_finale = (num_bancali * valore_bancale) + plus
            num_mostra = num_bancali
            tipo_collo = "Bancali"
        else:
            # Arrotondamento standard alla SCATOLA (anche per Genesis LS/AG)
            num_colli = math.ceil(round(qty_base / valore_conf, 4))
            qty_eff_finale = (num_colli * valore_conf) + plus
            num_mostra = num_colli
            tipo_collo = "Colli/Scatole"

        mq_risultanti = qty_eff_finale / resa_finale
        sconto_f = (sconto_man / 100) if sconto_man > 0 else (0.50 if qty_eff_finale >= valore_bancale else 0.45)
        netto = info["prezzo"] * (1 - sconto_f)
        imponibile = (netto * qty_eff_finale) + trasp

        # --- Visualizzazione ---
        st.markdown(f"""
        <div class="report-text">
        <h3 style='margin-top:0;'>RIEPILOGO ORDINE</h3>
        <strong>Articolo:</strong> {modello}<br>
        <hr>
        <strong>Quantità Finale:</strong> {qty_eff_finale:.2f} {"m2" if mondo == "Legno" else "Pezzi"}<br>
        {f"<em>(Equivalenti a: {mq_risultanti:.2f} m2)</em><br>" if mondo != "Legno" else ""}
        {f"<strong>N. {tipo_collo}:</strong> {num_mostra}<br>" if num_mostra is not None else ""}
        <strong>Resa:</strong> {resa_finale} pz/m2<br>
        <hr>
        <strong>Prezzo Netto:</strong> {netto:.3f} €<br>
        <strong>Sconto:</strong> {sconto_f*100:.0f}%<br>
        <hr>
        <span style='font-size: 1.2em;'><strong>{"TOTALE IVATO" if iva_check else "TOTALE IMPONIBILE"}: 
        {(imponibile*1.22 if iva_check else imponibile):.2f} €</strong></span>
        </div>
        """, unsafe_allow_html=True)
