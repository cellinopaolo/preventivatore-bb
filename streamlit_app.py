import streamlit as st
import json
import os
import math

st.set_page_config(page_title="B&B Preventivi", layout="centered")

# Stile personalizzato per tornare alla vecchia interfaccia compatta
st.markdown("""
    <style>
    .report-text { font-family: 'Courier New', Courier, monospace; background-color: #f1f1f1; padding: 20px; border-radius: 5px; border-left: 5px solid #333; }
    .stRadio > div { flex-direction: row; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 B&B Preventivi Pro v6.7.6")

BASE_FOLDER = "Listini_BB"
categorie = ["Mattoni", "Pietra", "Legno"]

# --- Selezione rapida laterale ---
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

    # --- Logica Posa (SOLO Fortis, NO Standard) ---
    resa_finale = float(info.get("pz_m2", 1.0))
    if mondo == "Mattoni" and "Fortis" in gamma:
        scelta_posa = st.radio("Configurazione Posa:", ["Di Piatto (62 pz/m2)", "Di Coltello (100 pz/m2)"])
        resa_finale = 62.0 if "Piatto" in scelta_posa else 100.0

    # --- Input Dati ---
    col1, col2 = st.columns(2)
    with col1:
        qty_in = st.number_input("Quantità", min_value=0.0, step=0.1)
        unit_var = st.radio("Unità", ["m2", "Pezzi"])
    with col2:
        sconto_man = st.number_input("Sconto % (0=Auto)", min_value=0, max_value=100)
        iva_check = st.checkbox("IVA 22% (Privato)")

    trasp = st.number_input("Trasporto (€)", min_value=0.0)
    plus = st.number_input("Extra (+)", min_value=0.0)

    if st.button("GENERA PREVENTIVO", use_container_width=True):
        valore_conf = float(info.get("pz_scatola", 1.0))
        qty_base = (qty_in * resa_finale) if unit_var == "m2" else qty_in
        
        if mondo == "Legno":
            qty_eff = qty_base + plus
            num_colli = "N/A"
        else:
            num_colli = math.ceil(round(qty_base / valore_conf, 4))
            qty_eff = (num_colli * valore_conf) + plus

        sconto_f = (sconto_man / 100) if sconto_man > 0 else (0.50 if qty_eff >= info["pz_bancale"] else 0.45)
        netto = info["prezzo"] * (1 - sconto_f)
        imponibile = (netto * qty_eff) + trasp

        # --- RISULTATO STILE VECCHIA APP ---
        st.markdown(f"""
        <div class="report-text">
        <strong>RIEPILOGO PREVENTIVO</strong><br>
        Articolo: {modello}<br>
        ──────────────────────────────<br>
        Quantità Finale: {qty_eff:.2f} {unit_var if unit_var == "Pezzi" else "pz/mq"}<br>
        N. Colli: {num_colli}<br>
        Resa: {resa_finale} pz/m2<br>
        ──────────────────────────────<br>
        Prezzo Netto: {netto:.3f} €<br>
        Sconto: {sconto_f*100:.0f}%<br>
        ──────────────────────────────<br>
        <strong>{"TOTALE IVATO" if iva_check else "TOTALE IMPONIBILE"}: {(imponibile*1.22 if iva_check else imponibile):.2f} €</strong>
        </div>
        """, unsafe_allow_html=True)
