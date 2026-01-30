import streamlit as st
import json
import os
import math

# Configurazione Pagina
st.set_page_config(page_title="B&B Preventivi Pro", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 B&B Preventivi Pro v6.7.3")
st.subheader("Web Edition")

BASE_FOLDER = "Listini_BB"
categorie = ["Mattoni", "Pietra", "Legno"]

# --- SIDEBAR ---
st.sidebar.header("Configurazione")
mondo = st.sidebar.selectbox("Mondo", categorie)

path_cat = os.path.join(BASE_FOLDER, mondo)
if os.path.exists(path_cat):
    listini = sorted([f.replace(".json", "") for f in os.listdir(path_cat) if f.endswith(".json")])
    if listini:
        gamma = st.sidebar.selectbox("Linea Prodotto", listini)
    else:
        st.error(f"Nessun file JSON in {path_cat}"); st.stop()
else:
    st.error(f"Cartella '{mondo}' non trovata."); st.stop()

# --- CARICAMENTO E INTERFACCIA ---
if gamma:
    with open(os.path.join(path_cat, f"{gamma}.json"), 'r') as f:
        prodotti = json.load(f)
    
    modello = st.selectbox("Seleziona Modello", sorted(prodotti.keys()))
    info = prodotti[modello]

    # --- LOGICA POSA MATTONI (FORTIS) ---
    resa_finale = float(info.get("pz_m2", 1.0))
    
    if mondo == "Mattoni":
        st.info("Configurazione Posa Mattoni")
        scelta_posa = st.radio(
            "Tipo di Posa:",
            ["Standard (da listino)", "Di Piatto (62 pz/m2)", "Di Coltello (100 pz/m2)"],
            horizontal=True
        )
        if "Piatto" in scelta_posa:
            resa_finale = 62.0
        elif "Coltello" in scelta_posa:
            resa_finale = 100.0

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

    # --- CALCOLO ---
    if st.button("CALCOLA PREVENTIVO", use_container_width=True):
        if qty_in <= 0 and plus <= 0:
            st.warning("Inserisci una quantità.")
        else:
            valore_conf = float(info.get("pz_scatola", 1.0))
            
            temp_qty = qty_in
            if mondo == "Pietra" and magg_pietra > 0:
                temp_qty *= (1 + (magg_pietra / 100))

            # Applichiamo la resa (che ora tiene conto della posa scelta)
            qty_base = temp_qty * resa_finale if unit_var == "m2" else temp_qty
            
            if mondo == "Legno":
                qty_eff = qty_base + plus
                num_colli = "N/A"
            else:
                num_colli = math.ceil(round(qty_base / valore_conf, 4))
                qty_eff = (num_confezioni * valore_conf) if 'num_confezioni' in locals() else (num_colli * valore_conf)
                qty_eff += plus

            sconto_applicato = (sconto_extra / 100) if sconto_extra > 0 else (0.50 if qty_eff >= info["pz_bancale"] else 0.45)
            netto = info["prezzo"] * (1 - sconto_applicato)
            totale_merce = netto * qty_eff
            imponibile = totale_merce + trasp

            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Quantità Finale", f"{qty_eff:.2f} {unit_var}")
            c2.metric("N. Colli", f"{num_colli}")
            c3.metric("Resa applicata", f"{resa_finale} pz/m2")

            st.write(f"### Dettaglio: {modello}")
            if iva_check:
                st.metric("TOTALE IVATO (22%)", f"{imponibile * 1.22:.2f} €")
            else:
                st.metric("TOTALE IMPONIBILE", f"{imponibile:.2f} €")
