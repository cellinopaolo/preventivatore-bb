import streamlit as st
import json
import os
import pandas as pd
import math

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="B&B Preventivi Cloud", layout="wide")

# --- LOGICA CARTELLA DATI ---
# Su Web usiamo una cartella locale o un database. Per ora manteniamo la logica file.
FOLDER_DATI = "."
if not os.path.exists(FOLDER_DATI):
    os.makedirs(FOLDER_DATI)

def carica_prodotti(nome_gamma):
    path = os.path.join(FOLDER_DATI, f"{nome_gamma}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def salva_gamma(nome, dati):
    with open(os.path.join(FOLDER_DATI, f"{nome}.json"), 'w') as f:
        json.dump(dati, f)

# --- INTERFACCIA ---
st.title("💎 B&B Preventivatore Cloud v1.0")

menu = ["Generatore Preventivi", "Gestione Database", "Visualizza Listini"]
scelta = st.sidebar.selectbox("Menu Navigazione", menu)

# --- 1. GENERATORE PREVENTIVI ---
if scelta == "Generatore Preventivi":
    st.header("Nuovo Preventivo")
    
    file_presenti = sorted([f.replace(".json", "") for f in os.listdir(FOLDER_DATI) if f.endswith(".json")])
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        gamma = st.selectbox("Linea Prodotto", file_presenti)
        prodotti = carica_prodotti(gamma) if gamma else {}
        
        # Gestione Posa Fortis
        resa_m2_override = None
        if gamma and "Fortis" in gamma:
            posa = st.radio("Modalità Posa", ["Di Piatto (62 pz/m2)", "Di Coltello (100 pz/m2)"])
            resa_m2_override = 100.0 if "Coltello" in posa else 62.0
        
        codice = st.selectbox("Seleziona Modello", list(prodotti.keys()))
        
        c_qty1, c_qty2 = st.columns([2, 1])
        qty_in = c_qty1.number_input("Quantità", min_value=0.0, step=1.0)
        unita = c_qty2.selectbox("Unità", ["m2", "Pezzi"])
        
        sconto_in = st.number_input("Sconto Personale % (0 = Auto)", min_value=0, max_value=100, value=0)
        trasp = st.number_input("Costo Trasporto (€)", min_value=0.0)
        plus_val = st.number_input("+ Aggiungi Unità Extra (Bancali/Scatole)", min_value=0)
        
        iva_check = st.checkbox("Applica IVA 22% (Cliente Privato)")

    with col2:
        st.subheader("Risultato")
        if st.button("CALCOLA PREVENTIVO", use_container_width=True):
            if codice:
                info = prodotti[codice]
                resa_m2 = resa_m2_override if resa_m2_override else info["pz_m2"]
                
                qty_pz_base = qty_in * resa_m2 if unita == "m2" else qty_in
                
                # Logica packaging
                is_futura = "Futura" in gamma or "Futura" in codice
                is_speciale = any(x in codice for x in ["LS", "AG"])
                
                if is_futura or (("Croma" in gamma) and is_speciale):
                    qty_eff = qty_pz_base + plus_val
                    lab = "Unità Sfuse"
                elif any(x in gamma for x in ["Genesis", "Croma", "Fortis", "Cotto"]) and not is_speciale:
                    num_bancali = math.ceil(qty_pz_base / info["pz_bancale"]) + plus_val
                    qty_eff = num_bancali * info["pz_bancale"]
                    lab = f"{int(num_bancali)} Bancali"
                else:
                    ps = info.get("pz_scatola", 1)
                    num_scat = math.ceil(qty_pz_base / ps) + plus_val
                    qty_eff = num_scat * ps
                    lab = f"{int(num_scat)} Scatole"

                sconto_eff = (sconto_in / 100) if sconto_in > 0 else (0.50 if qty_eff >= info["pz_bancale"] else 0.45)
                n_pz = info["prezzo"] * (1 - sconto_eff)
                imp_merce = n_pz * qty_eff
                tot_imp = imp_merce + trasp
                
                # Box Risultato
                with st.container(border=True):
                    st.code(f"""
Gamma:  {gamma}
Art:    {codice}
------------------------------
Q.tà:   {qty_eff:.0f} pz ({qty_eff/resa_m2:.2f} {unita})
Pack:   {lab}
Sconto: {sconto_eff*100:.0f}%
Netto:  {n_pz:.3f} €/pz
------------------------------
Merce:  {imp_merce:.2f} €
Trasp:  {trasp:.2f} €
""")
                    if iva_check:
                        st.metric("TOTALE (IVA Inc.)", f"{(totale_iva := tot_imp * 1.22):.2f} €")
                    else:
                        st.metric("TOTALE IMPONIBILE", f"{tot_imp:.2f} €")

# --- 2. GESTIONE DATABASE ---
elif scelta == "Gestione Database":
    st.header("Configurazione Dati")
    
    nome_nuova_gamma = st.text_input("Nome della nuova Gamma")
    file_csv = st.file_uploader("Carica File CSV", type="csv")
    
    if st.button("IMPORTA LISTINO"):
        if nome_nuova_gamma and file_csv:
            df = pd.read_csv(file_csv)
            # Normalizza colonne
            df.columns = [c.strip().lower() for c in df.columns]
            nuovi = {}
            for _, row in df.iterrows():
                cod = str(row['codice']).strip()
                nuovi[cod] = {
                    "prezzo": float(str(row.get('prezzo', 0)).replace(',','.')),
                    "pz_bancale": int(row.get('bancale', 0)),
                    "pz_m2": float(str(row.get('pzm2', 1)).replace(',','.')),
                    "pz_scatola": int(row.get('pzscatola', 1))
                }
            salva_gamma(nome_nuova_gamma, nuovi)
            st.success(f"Gamma {nome_nuova_gamma} importata correttamente!")

# --- 3. VISUALIZZA LISTINI ---
elif scelta == "Visualizza Listini":
    st.header("Consultazione Listini")
    file_presenti = sorted([f.replace(".json", "") for f in os.listdir(FOLDER_DATI) if f.endswith(".json")])
    gamma_view = st.selectbox("Seleziona Gamma", file_presenti)
    
    if gamma_view:
        dati = carica_prodotti(gamma_view)
        df_display = pd.DataFrame.from_dict(dati, orient='index')
        st.dataframe(df_display, use_container_width=True)