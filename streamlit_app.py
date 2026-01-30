import streamlit as st
import json
import os
import math

# 1. Configurazione Pagina
st.set_page_config(page_title="B&B Preventivi", layout="centered")

# 2. CSS per lo stile "Scontrino Pulito"
st.markdown("""
    <style>
    .report-container {
        background-color: #ffffff;
        padding: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        line-height: 1.6;
        color: #333333;
    }
    .linea-divisione {
        border-top: 1px solid #eeeeee;
        margin: 15px 0;
    }
    .totale-evidenziato {
        font-size: 1.25em;
        font-weight: bold;
        margin-top: 10px;
        color: #000000;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 B&B Preventivi Pro")

BASE_FOLDER = "Listini_BB"
categorie = ["Mattoni", "Pietra", "Legno"]

# --- Selezione ---
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

    # --- Posa Fortis ---
    resa_finale = float(info.get("pz_m2", 1.0))
    if mondo == "Mattoni" and "Fortis" in gamma:
        scelta_posa = st.radio("Configurazione Posa:", ["Di Piatto (62 pz/m2)", "Di Coltello (100 pz/m2)"], horizontal=True)
        resa_finale = 62.0 if "Piatto" in scelta_posa else 100.0

    # --- Input ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        qty_in = st.number_input("Quantità", min_value=0.0, step=0.1, format="%.2f")
        unit_var = st.radio("Unità inserita", ["m2", "Pezzi"], horizontal=True)
    with c2:
        sconto_man = st.number_input("Sconto % (0=Auto)", min_value=0, max_value=100)
        iva_check = st.checkbox("IVA 22% (Privato)")

    trasp = st.number_input("Trasporto (€)", min_value=0.0)
    plus = st.number_input("Extra (+)", min_value=0.0)

    # --- Calcolo e Output ---
    if st.button("GENERA PREVENTIVO", use_container_width=True):
        valore_conf = float(info.get("pz_scatola", 1.0))
        qty_base_pz = (qty_in * resa_finale) if unit_var == "m2" else qty_in
        
        if mondo == "Legno":
            qty_eff_pz = qty_base_pz + plus
            num_colli = "N/A"
        else:
            num_colli = math.ceil(round(qty_base_pz / valore_conf, 4))
            qty_eff_pz = (num_colli * valore_conf) + plus

        mq_risultanti = qty_eff_pz / resa_finale
        sconto_f = (sconto_man / 100) if sconto_man > 0 else (0.50 if qty_eff_pz >= info["pz_bancale"] else 0.45)
        netto = info["prezzo"] * (1 - sconto_f)
        imponibile = (netto * qty_eff_pz) + trasp
        totale_v = imponibile * 1.22 if iva_check else imponibile

        # --- Visualizzazione ---
        # Costruisco la stringa HTML separatamente per evitare errori di rendering
        label_totale = "TOTALE IVATO" if iva_check else "TOTALE IMPONIBILE"
        riga_mq = f"<i>(Equivalenti a: {mq_risultanti:.2f} m2)</i><br>" if unit_var == "Pezzi" else ""
        
        output_html = f"""
        <div class="report-container">
            <h2 style='margin:0 0 10px 0; color:#333;'>RIEPILOGO ORDINE</h2>
            <strong>Articolo:</strong> {modello}
            <div class="linea-divisione"></div>
            <strong>Quantità Finale:</strong> {qty_in if unit_var == "m2" else qty_eff_pz:.2f} {unit_var}<br>
            {riga_mq}
            <strong>N. Colli:</strong> {num_colli}<br>
            <strong>Resa:</strong> {resa_finale} pz/m2
            <div class="linea-divisione"></div>
            <strong>Prezzo Netto:</strong> {netto:.3f} €<br>
            <strong>Sconto:</strong> {sconto_f*100:.0f}%
            <div class="linea-divisione"></div>
            <div class="totale-evidenziato">
                {label_totale}: {totale_v:.2f} €
            </div>
        </div>
        """
        st.markdown(output_html, unsafe_allow_html=True)
