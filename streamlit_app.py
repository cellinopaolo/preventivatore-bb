import streamlit as st
import json
import os
import math

st.set_page_config(page_title="B&B Preventivi Pro", layout="centered")

# CSS per pulizia interfaccia
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 B&B Preventivi Pro v6.7.4")

BASE_FOLDER = "Listini_BB"
categorie = ["Mattoni", "Pietra", "Legno"]

# --- SIDEBAR DI CONFIGURAZIONE ---
st.sidebar.header("Impostazioni Listino")
mondo = st.sidebar.selectbox("Categoria", categorie)

path_cat = os.path.join(BASE_FOLDER, mondo)
if os.path.exists(path_cat):
    listini = sorted([f.replace(".json", "") for f in os.listdir(path_cat) if f.endswith(".json")])
    if listini:
        gamma = st.sidebar.selectbox("Linea Prodotto", listini)
    else:
        st.error(f"Nessun listino trovato in {mondo}"); st.stop()
else:
    st.error(f"Database {mondo} non trovato."); st.stop()

# --- CARICAMENTO DATI ---
if gamma:
    with open(os.path.join(path_cat, f"{gamma}.json"), 'r') as f:
        prodotti = json.load(f)
    
    modello = st.selectbox("Seleziona Modello", sorted(prodotti.keys()))
    info = prodotti[modello]

    # --- LOGICA POSA (SOLO FORTIS) ---
    resa_finale = float(info.get("pz_m2", 1.0))
    if mondo == "Mattoni" and "Fortis" in gamma:
        st.subheader("Configurazione Posa Fortis")
        scelta_posa = st.radio("Seleziona Posa:", ["Standard", "Di Piatto (62 pz/m2)", "Di Coltello (100 pz/m2)"], horizontal=True)
        if "Piatto" in scelta_posa: resa_finale = 62.0
        elif "Coltello" in scelta_posa: resa_finale = 100.0

    # --- INPUT QUANTITÀ E EXTRA ---
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        qty_in = st.number_input("Quantità Richiesta", min_value=0.0, step=0.1, format="%.2f")
        unit_var = st.radio("Unità", ["m2", "Pezzi"], horizontal=True)
        sconto_man = st.number_input("Sconto Manuale % (0=Auto)", min_value=0, max_value=100, value=0)
    
    with col2:
        trasp = st.number_input("Trasporto (€)", min_value=0.0, step=10.0)
        plus = st.number_input("Unità Extra (+)", min_value=0.0, step=0.1)
        iva_check = st.checkbox("Privato (IVA 22%)")

    # --- LOGICA PIETRA ---
    magg_pietra = 0
    if mondo == "Pietra":
        magg_pietra = st.slider("% Maggiorazione Posa a Secco", 0, 30, 0)

    # --- MOTORE DI CALCOLO INTEGRALE ---
    if st.button("GENERA PREVENTIVO", use_container_width=True):
        if qty_in <= 0 and plus <= 0:
            st.warning("Inserisci una quantità.")
        else:
            valore_conf = float(info.get("pz_scatola", 1.0))
            
            # 1. Applica Maggiorazione Pietra
            qty_lavoro = qty_in
            if mondo == "Pietra" and magg_pietra > 0:
                qty_lavoro *= (1 + (magg_pietra / 100))

            # 2. Trasformazione in Base (mq -> pz o mq utile -> mq comm)
            qty_base = qty_lavoro * resa_finale if unit_var == "m2" else qty_lavoro
            
            # 3. Arrotondamento (Escluso per Legno)
            if mondo == "Legno":
                qty_eff = qty_base + plus
                num_colli = "N/A"
            else:
                num_colli = math.ceil(round(qty_base / valore_conf, 4))
                qty_eff = (num_colli * valore_conf) + plus

            # 4. Calcolo Sconto (Soglia Bancale dal CSV)
            sconto_finale = (sconto_man / 100) if sconto_man > 0 else (0.50 if qty_eff >= info["pz_bancale"] else 0.45)
            
            # 5. Totali
            prezzo_list = info["prezzo"]
            netto = prezzo_list * (1 - sconto_finale)
            tot_merce = netto * qty_eff
            imponibile = tot_merce + trasp

            # --- OUTPUT ---
            st.divider()
            res1, res2 = st.columns(2)
            with res1:
                st.metric("Quantità Finale", f"{qty_eff:.2f} {unit_var}")
                st.write(f"Prezzo Listino: {prezzo_list:.2f} €")
                st.write(f"Sconto applicato: {sconto_finale*100:.0f}%")
            with res2:
                st.metric("Prezzo Netto", f"{netto:.3f} €")
                if iva_check:
                    st.metric("TOTALE IVATO", f"{imponibile * 1.22:.2f} €")
                else:
                    st.metric("TOTALE IMPONIBILE", f"{imponibile:.2f} €")
            
            st.caption(f"Dettaglio: {modello} | Resa: {resa_finale} | Colli: {num_colli}")
