import streamlit as st
import json
import os
import math

# Configurazione Pagina
st.set_page_config(page_title="B&B Preventivi Pro", layout="centered")

# Stile CSS Corretto
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 B&B Preventivi Pro v6.7.2")
st.subheader("Web Edition")

# Percorso database (Assicurati che la cartella sia caricata su GitHub)
BASE_FOLDER = "Listini_BB"
categorie = ["Mattoni", "Pietra", "Legno"]

# --- SIDEBAR PER SELEZIONE ---
st.sidebar.header("Configurazione")
mondo = st.sidebar.selectbox("Mondo", categorie)

# Caricamento dinamico listini
path_cat = os.path.join(BASE_FOLDER, mondo)

if os.path.exists(path_cat):
    listini = sorted([f.replace(".json", "") for f in os.listdir(path_cat) if f.endswith(".json")])
    if listini:
        gamma = st.sidebar.selectbox("Linea Prodotto", listini)
    else:
        st.error(f"Nessun file JSON trovato in {path_cat}")
        st.stop()
else:
    st.error(f"Cartella '{mondo}' non trovata. Verifica di aver caricato la cartella '{BASE_FOLDER}' su GitHub.")
    st.stop()

# --- CARICAMENTO DATI PRODOTTO ---
if gamma:
    with open(os.path.join(path_cat, f"{gamma}.json"), 'r') as f:
        prodotti = json.load(f)
    
    modello = st.selectbox("Seleziona Modello", sorted(prodotti.keys()))
    info = prodotti[modello]

    # --- INPUT UTENTE ---
    col1, col2 = st.columns(2)
    with col1:
        qty_in = st.number_input("Quantità Richiesta", min_value=0.0, step=0.1, format="%.2f")
        unit_var = st.radio("Unità inserita", ["m2", "Pezzi"], horizontal=True)
        sconto_extra = st.number_input("Sconto Manuale % (0 = Auto)", min_value=0, max_value=100, value=0)
    
    with col2:
        trasp = st.number_input("Trasporto Totale (€)", min_value=0.0, step=10.0)
        plus = st.number_input("Aggiungi Unità Extra", min_value=0.0, step=0.1)
        iva_check = st.checkbox("Applica IVA 22% (Privato)")

    magg_pietra = 0
    if mondo == "Pietra":
        magg_pietra = st.slider("% Maggiorazione Posa a Secco", 0, 30, 0)

    # --- LOGICA DI CALCOLO ---
    if st.button("CALCOLA PREVENTIVO", use_container_width=True):
        if qty_in <= 0 and plus <= 0:
            st.warning("Inserisci una quantità per procedere.")
        else:
            # 1. Recupero parametri tecnici
            resa = float(info.get("pz_m2", 1.0))
            valore_conf = float(info.get("pz_scatola", 1.0))
            
            # 2. Calcolo Base
            temp_qty = qty_in
            if mondo == "Pietra" and magg_pietra > 0:
                temp_qty *= (1 + (magg_pietra / 100))

            qty_base = temp_qty * resa if unit_var == "m2" else temp_qty
            
            # 3. Logica Arrotondamento Differenziata (v6.7.1)
            if mondo == "Legno":
                qty_eff = qty_base + plus
                num_colli = "N/A"
            else:
                num_colli = math.ceil(round(qty_base / valore_conf, 4))
                qty_eff = (num_colli * valore_conf) + plus

            # 4. Sconto
            sconto_applicato = (sconto_extra / 100) if sconto_extra > 0 else (0.50 if qty_eff >= info["pz_bancale"] else 0.45)
            
            # 5. Totali
            prezzo_listino = info["prezzo"]
            netto = prezzo_listino * (1 - sconto_applicato)
            totale_merce = netto * qty_eff
            imponibile = totale_merce + trasp

            # --- OUTPUT ---
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Quantità Finale", f"{qty_eff:.2f} {unit_var}")
            c2.metric("N. Colli", f"{num_colli}")
            c3.metric("Sconto", f"{sconto_applicato*100:.0f}%")

            st.write(f"### Dettaglio: {modello}")
            st.write(f"Prezzo Listino: {prezzo_listino:.2f} € | **Prezzo Netto: {netto:.3f} €**")
            
            if iva_check:
                st.metric("TOTALE IVATO (22%)", f"{imponibile * 1.22:.2f} €")
            else:
                st.metric("TOTALE IMPONIBILE", f"{imponibile:.2f} €")
