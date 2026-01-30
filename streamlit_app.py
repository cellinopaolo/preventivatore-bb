import streamlit as st
import json
import os
import math

# Configurazione Pagina
st.set_page_config(page_title="B&B Preventivi Pro", layout="centered")

# Stile CSS per rendere l'interfaccia pulita
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_value=True)

st.title("💎 B&B Preventivi Pro v6.7.1")
st.subheader("Web Edition")

# Percorso database
BASE_FOLDER = "Listini_BB"
categorie = ["Mattoni", "Pietra", "Legno"]

# --- SIDEBAR PER SELEZIONE ---
st.sidebar.header("Configurazione")
mondo = st.sidebar.selectbox("Mondo", categorie)

# Caricamento dinamico listini
path_cat = os.path.join(BASE_FOLDER, mondo)
if os.path.exists(path_cat):
    listini = sorted([f.replace(".json", "") for f in os.listdir(path_cat) if f.endswith(".json")])
    gamma = st.sidebar.selectbox("Linea Prodotto", listini)
else:
    st.error(f"Cartella {mondo} non trovata nel database.")
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
        qty_in = st.number_input("Quantità (m2 o Pezzi)", min_value=0.0, step=0.1, format="%.2f")
        unit_var = st.radio("Unità di misura", ["m2", "Pezzi"], horizontal=True)
        sconto_extra = st.number_input("Sconto Manuale % (0 = Auto)", min_value=0, max_value=100, value=0)
    
    with col2:
        trasp = st.number_input("Trasporto Totale (€)", min_value=0.0, step=10.0)
        plus = st.number_input("Aggiungi Unità Extra", min_value=0.0, step=0.1)
        iva_check = st.checkbox("Applica IVA 22% (Privato)")

    # Maggiorazione specifica per la Pietra
    magg_pietra = 0
    if mondo == "Pietra":
        magg_pietra = st.slider("% Maggiorazione Posa a Secco", 0, 30, 0)

    # --- LOGICA DI CALCOLO COMPLETA (v6.7.1) ---
    if st.button("CALCOLA PREVENTIVO", use_container_width=True):
        if qty_in <= 0:
            st.warning("Inserisci una quantità valida.")
        else:
            # 1. Moltiplicatore Resa/Coefficiente
            resa = info["pz_m2"]
            valore_conf = info["pz_scatola"]
            
            # Calcolo base
            temp_qty = qty_in
            if mondo == "Pietra" and magg_pietra > 0:
                temp_qty *= (1 + (magg_pietra / 100))

            qty_base = temp_qty * resa if unit_var == "m2" else temp_qty
            
            # 2. Logica Arrotondamento Differenziata
            if mondo == "Legno":
                qty_eff = qty_base + plus  # Nessun arrotondamento per il legno
                num_colli = "N/A"
            else:
                num_colli = math.ceil(round(qty_base / valore_conf, 4))
                qty_eff = (num_colli * valore_conf) + plus

            # 3. Sconto Automatico o Manuale
            sconto_applicato = (sconto_extra / 100) if sconto_extra > 0 else (0.50 if qty_eff >= info["pz_bancale"] else 0.45)
            
            # 4. Calcolo Finali
            prezzo_listino = info["prezzo"]
            netto = prezzo_listino * (1 - sconto_applicato)
            totale_merce = netto * qty_eff
            imponibile = totale_merce + trasp

            # --- DISPLAY RISULTATI ---
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Quantità Finale", f"{qty_eff:.2f} {unit_var}")
            c2.metric("N. Colli/Scatole", f"{num_colli}")
            c3.metric("Sconto", f"{sconto_applicato*100:.0f}%")

            st.subheader(f"Dettaglio Economico: {modello}")
            st.write(f"Prezzo Listino: {prezzo_listino:.2f} € | Prezzo Netto: **{netto:.3f} €**")
            
            if iva_check:
                st.metric("TOTALE IVATO (22%)", f"{imponibile * 1.22:.2f} €")
                st.caption(f"Imponibile: {imponibile:.2f} € + IVA: {imponibile*0.22:.2f} €")
            else:
                st.metric("TOTALE IMPONIBILE", f"{imponibile:.2f} €")
            
            st.success("Preventivo generato correttamente.")



---

### Perché questo è quello giusto:
* **Gestione Legno:** Ho inserito il blocco `if mondo == "Legno"` che annulla l'arrotondamento al pacco/bancale come richiesto.
* **Coefficiente PzM2:** Funziona sia per i mattoni (pezzi al mq) sia per il legno (coefficiente commerciale).
* **Pietra:** Include lo slider per la maggiorazione posa a secco.
* **Database:** Cerca i file esattamente nella struttura di cartelle che hai caricato su GitHub.

### 🛠️ Il tuo comando per aggiornare l'app (Desktop)
Ogni volta che modifichi il codice `app.py` sul tuo Mac, usa questo:

```bash
python3 -m PyInstaller --onefile --windowed --name "BB_PREVENTIVI_WEB" app.py