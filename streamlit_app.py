import streamlit as st
import json
import os
import math

st.set_page_config(page_title="B&B Preventivi Pro", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 B&B Preventivi Pro v6.7.5")

BASE_FOLDER = "Listini_BB"
categorie = ["Mattoni", "Pietra", "Legno"]

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

if gamma:
    with open(os.path.join(path_cat, f"{gamma}.json"), 'r') as f:
        prodotti = json.load(f)
    
    modello = st.selectbox("Seleziona Modello", sorted(prodotti.keys()))
    info = prodotti[modello]

    # --- LOGICA POSA FORTIS (RIMOSSO STANDARD) ---
    resa_finale = float(info.get("pz_m2", 1.0))
    if mondo == "Mattoni" and "Fortis" in gamma:
        st.subheader("Configurazione Posa Fortis")
        # Ora la scelta è obbligata tra le due pose reali
        scelta_posa = st.radio(
            "Seleziona Tipo di Posa:", 
            ["Di Piatto (62 pz/m2)", "Di Coltello (100 pz/m2)"], 
            horizontal=True
        )
        resa_finale = 62.0 if "Piatto" in scelta_posa else 100.0

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        qty_in = st.number_input("Quantità Richiesta", min_value=0.0, step=0.1, format="%.2f")
        unit_var = st.radio("Unità", ["m2", "Pezzi"], horizontal=True)
        sconto_man = st.number_input("Sconto Manuale % (0=Auto)", min_value=0, max_value=100, value=0)
    
    with col2:
        trasp = st.number_input("Trasporto (€)", min_value=0.0, step=10.0)
        plus = st.number_input("Aggiungi Unità Extra", min_value=0.0, step=0.1)
        iva_check = st.checkbox("Privato (IVA 22%)")

    magg_pietra = 0
    if mondo == "Pietra":
        magg_pietra = st.slider("% Maggiorazione Posa a Secco", 0, 30, 0)

    if st.button("GENERA PREVENTIVO", use_container_width=True):
        if qty_in <= 0 and plus <= 0:
            st.warning("Inserisci una quantità.")
        else:
            valore_conf = float(info.get("pz_scatola", 1.0))
            qty_lavoro = qty_in * (1 + (magg_pietra / 100)) if (mondo == "Pietra" and magg_pietra > 0) else qty_in
            qty_base = qty_lavoro * resa_finale if unit_var == "m2" else qty_lavoro
            
            if mondo == "Legno":
                qty_eff = qty_base + plus
                num_colli = "N/A"
            else:
                num_colli = math.ceil(round(qty_base / valore_conf, 4))
                qty_eff = (num_colli * valore_conf) + plus

            sconto_finale = (sconto_man / 100) if sconto_man > 0 else (0.50 if qty_eff >= info["pz_bancale"] else 0.45)
            netto = info["prezzo"] * (1 - sconto_finale)
            imponibile = (netto * qty_eff) + trasp

            st.divider()
            res1, res2 = st.columns(2)
            with res1:
                st.metric("Quantità Finale", f"{qty_eff:.2f} {unit_var}")
                st.write(f"Sconto applicato: {sconto_finale*100:.0f}%")
            with res2:
                st.metric("Prezzo Netto", f"{netto:.3f} €")
                val_finale = imponibile * 1.22 if iva_check else imponibile
                st.metric("TOTALE" + (" (IVA INCLUSA)" if iva_check else " IMPONIBILE"), f"{val_finale:.2f} €")
            
            st.caption(f"Articolo: {modello} | Resa: {resa_finale} pz/m2 | Colli: {num_colli}")
