import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import csv
import math

class PreventivatoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("B&B Preventivi - Pro Edition v6.7.1")
        self.root.geometry("1200x950")
        
        self.base_folder = os.path.expanduser("~/Documents/Listini_BB")
        self.categorie = ["Mattoni", "Pietra", "Legno"]
        
        for cat in self.categorie:
            path = os.path.join(self.base_folder, cat)
            if not os.path.exists(path):
                os.makedirs(path)
            
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.prodotti = {}
        self.tab_control = ttk.Notebook(root)
        
        self.tab_calc = tk.Frame(self.tab_control, bg="white", padx=30, pady=30)
        self.tab_listino = tk.Frame(self.tab_control, bg="#1a1a1a", padx=30, pady=30) 
        self.tab_view = tk.Frame(self.tab_control, bg="#f5f5dc", padx=30, pady=30)    
        
        self.tab_control.add(self.tab_calc, text=' 💎 GENERATORE PREVENTIVI ')
        self.tab_control.add(self.tab_listino, text=' ⚙️ GESTIONE DATABASE ')
        self.tab_control.add(self.tab_view, text=' 📋 VISUALIZZA LISTINI ')
        self.tab_control.pack(expand=1, fill="both")

        self.setup_tab_calc()
        self.setup_tab_listino()
        self.setup_tab_view()
        self.aggiorna_menu_gamme()

    def setup_tab_calc(self):
        header = tk.Label(self.tab_calc, text="NUOVO PREVENTIVO B&B", font=("Segoe UI", 24, "bold"), bg="white", fg="#1a202c")
        header.pack(pady=(0, 20))
        main_container = tk.Frame(self.tab_calc, bg="white")
        main_container.pack(fill="both", expand=True)
        left_col = tk.Frame(main_container, bg="white", padx=20)
        left_col.pack(side="left", fill="both", expand=True)
        f_lbl, f_ent = ("Segoe UI", 12, "bold"), ("Segoe UI", 16)

        tk.Label(left_col, text="CATEGORIA (MONDO)", font=f_lbl, bg="white", fg="#3182ce").pack(anchor="w")
        self.combo_mondo = ttk.Combobox(left_col, font=f_ent, state="readonly", values=self.categorie)
        self.combo_mondo.current(0); self.combo_mondo.pack(fill="x", pady=(5, 15))
        self.combo_mondo.bind("<<ComboboxSelected>>", self.gestisci_cambio_mondo)

        tk.Label(left_col, text="LINEA PRODOTTO", font=f_lbl, bg="white", fg="#4a5568").pack(anchor="w")
        self.combo_gamma = ttk.Combobox(left_col, font=f_ent, state="readonly")
        self.combo_gamma.pack(fill="x", pady=(5, 15))
        self.combo_gamma.bind("<<ComboboxSelected>>", lambda e: self.carica_gamma(e, "calc"))

        self.frame_posa = tk.Frame(left_col, bg="#2d3748", padx=15, pady=15)
        tk.Label(self.frame_posa, text="MODALITÀ POSA (FORTIS)", font=("Segoe UI", 12, "bold"), bg="#2d3748", fg="white").pack(anchor="w")
        self.combo_posa = ttk.Combobox(self.frame_posa, font=f_ent, state="readonly")
        self.combo_posa['values'] = ("Di Piatto (62 pz/m2)", "Di Coltello (100 pz/m2)")
        self.combo_posa.current(0); self.combo_posa.pack(fill="x", pady=(5, 0))

        tk.Label(left_col, text="SELEZIONA MODELLO", font=f_lbl, bg="white", fg="#4a5568").pack(anchor="w", pady=(10,0))
        self.combo_prodotti = ttk.Combobox(left_col, font=f_ent, state="readonly")
        self.combo_prodotti.pack(fill="x", pady=(5, 15))

        tk.Label(left_col, text="QUANTITÀ", font=f_lbl, bg="white", fg="#4a5568").pack(anchor="w")
        qty_frame = tk.Frame(left_col, bg="white"); qty_frame.pack(fill="x", pady=(5, 15))
        self.ent_qty = tk.Entry(qty_frame, font=f_ent, width=10, relief="solid", bd=1); self.ent_qty.pack(side="left", padx=(0, 10))
        self.unit_var = tk.StringVar(value="m2")
        self.combo_unit = ttk.Combobox(qty_frame, textvariable=self.unit_var, font=f_ent, width=8, state="readonly")
        self.combo_unit['values'] = ("m2", "Pezzi"); self.combo_unit.pack(side="left")

        self.frame_pietra_box = tk.Frame(left_col, bg="white")
        tk.Label(self.frame_pietra_box, text="% MAGGIORAZIONE POSA A SECCO", font=f_lbl, bg="white", fg="#3182ce").pack(anchor="w")
        self.ent_pietra_perc = tk.Entry(self.frame_pietra_box, font=f_ent, relief="solid", bd=1, fg="#3182ce")
        self.ent_pietra_perc.insert(0, "0"); self.ent_pietra_perc.pack(fill="x", pady=(5, 15))
        self.frame_pietra_box.pack_forget()

        tk.Label(left_col, text="SCONTO PERSONALE % (0 = Auto)", font=f_lbl, bg="white", fg="#2d2d2d").pack(anchor="w")
        self.ent_extra = tk.Entry(left_col, font=f_ent, relief="solid", bd=1); self.ent_extra.insert(0, "0"); self.ent_extra.pack(fill="x", pady=(5, 15))

        tk.Label(left_col, text="COSTO TRASPORTO (€)", font=f_lbl, bg="white", fg="#4a5568").pack(anchor="w")
        self.ent_transp = tk.Entry(left_col, font=f_ent, relief="solid", bd=1); self.ent_transp.insert(0, "0"); self.ent_transp.pack(fill="x", pady=(5, 15))

        tk.Label(left_col, text="+ AGGIUNGI UNITÀ EXTRA", font=f_lbl, bg="white", fg="#3182ce").pack(anchor="w")
        self.ent_plus = tk.Entry(left_col, font=f_ent, relief="solid", bd=1, fg="#3182ce"); self.ent_plus.insert(0, "0"); self.ent_plus.pack(fill="x", pady=(5, 15))

        self.var_privato = tk.BooleanVar()
        tk.Checkbutton(left_col, text=" IVA 22% (PRIVATO)", variable=self.var_privato, font=("Segoe UI", 12), bg="white").pack(anchor="w", pady=10)

        btn_frame = tk.Frame(left_col, bg="white"); btn_frame.pack(fill="x", pady=20)
        tk.Button(btn_frame, text="GENERA PREVENTIVO", command=self.calcola, bg="#10b981", fg="black", font=("Segoe UI", 14, "bold"), pady=15).pack(fill="x", pady=5)
        tk.Button(btn_frame, text="PULISCI", command=self.pulisci_campi, bg="#e2e8f0", font=("Segoe UI", 11)).pack(fill="x")

        right_col = tk.Frame(main_container, bg="#1e293b", padx=20, pady=20)
        right_col.pack(side="right", fill="both", expand=True)
        self.txt_risultato = tk.Text(right_col, font=("Consolas", 16), bg="#1e293b", fg="#f8fafc", relief="flat", padx=15, pady=15)
        self.txt_risultato.pack(fill="both", expand=True)

    def calcola(self):
        try:
            cod = self.combo_prodotti.get(); info = self.prodotti[cod]
            moltiplicatore_resa = float(info.get("pz_m2", 1.0))
            valore_confezione = float(info.get("pz_scatola", 1.0))
            
            qty_richiesta = float(self.ent_qty.get().replace(',', '.') or 0)
            input_sconto = float(self.ent_extra.get().replace(',', '.') or 0) / 100
            trasp = float(self.ent_transp.get().replace(',', '.') or 0)
            plus = float(self.ent_plus.get().replace(',', '.') or 0)
            
            if self.combo_mondo.get() == "Pietra":
                perc_magg = float(self.ent_pietra_perc.get().replace(',', '.') or 0) / 100
                qty_richiesta *= (1 + perc_magg)

            qty_base = qty_richiesta * moltiplicatore_resa
            
            if self.combo_mondo.get() == "Legno":
                qty_eff = qty_base + plus
            else:
                num_confezioni = math.ceil(round(qty_base / valore_confezione, 4))
                qty_eff = (num_confezioni * valore_confezione) + plus

            sconto = input_sconto if input_sconto > 0 else (0.50 if qty_eff >= info["pz_bancale"] else 0.45)
            netto = info["prezzo"] * (1 - sconto)
            tot_merce = netto * qty_eff
            tot_final = tot_merce + trasp

            self.txt_risultato.delete(1.0, tk.END)
            res = f"CATEGORIA: {self.combo_mondo.get()}\nArticolo: {cod}\n{'─'*30}\n"
            res += f"Q.tà Finale: {qty_eff:.2f} {self.unit_var.get()}\n"
            if self.combo_mondo.get() != "Legno":
                res += f"N. Colli: {math.ceil(qty_base/valore_confezione)}\n"
            res += f"Prezzo Netto: {netto:.3f} €\n{'─'*30}\n"
            
            if self.var_privato.get():
                iva = tot_final * 0.22
                res += f"Imponibile: {tot_final:.2f} €\nIVA 22%: {iva:.2f} €\nTOTALE: {tot_final+iva:.2f} €"
            else:
                res += f"TOT. IMPONIBILE: {tot_final:.2f} €"
            self.txt_risultato.insert(tk.END, res)
        except Exception as e: messagebox.showerror("Errore", "Verifica i dati")

    def gestisci_cambio_mondo(self, event=None):
        mondo = self.combo_mondo.get()
        if mondo == "Pietra": self.frame_pietra_box.pack(after=self.ent_qty.master, fill="x")
        else: self.frame_pietra_box.pack_forget()
        self.aggiorna_menu_gamme()

    def setup_tab_listino(self):
        tk.Label(self.tab_listino, text="GESTIONE DATABASE", font=("Segoe UI", 18, "bold"), bg="#1a1a1a", fg="white").pack(pady=20)
        self.combo_mondo_import = ttk.Combobox(self.tab_listino, font=("Segoe UI", 12), state="readonly", values=self.categorie)
        self.combo_mondo_import.current(0); self.combo_mondo_import.pack(pady=5)
        tk.Button(self.tab_listino, text="➕ IMPORTA CSV", command=self.importa_csv, bg="#3182ce", fg="white", padx=20, pady=10).pack(pady=20)
        frame_del = tk.LabelFrame(self.tab_listino, text=" ELIMINA GAMMA ", bg="#2d2d2d", fg="white", padx=20, pady=20)
        frame_del.pack(fill="x", pady=20)
        self.combo_rimuovi_gamma = ttk.Combobox(frame_del, font=("Segoe UI", 12), state="readonly"); self.combo_rimuovi_gamma.pack(fill="x", pady=5)
        tk.Button(frame_del, text="ELIMINA", command=self.cancella_gamma, bg="#e53e3e", fg="white").pack(fill="x")

    def setup_tab_view(self):
        f_top = tk.Frame(self.tab_view, bg="#f5f5dc"); f_top.pack(fill="x", pady=10)
        self.combo_mondo_view = ttk.Combobox(f_top, state="readonly", values=self.categorie)
        self.combo_mondo_view.current(0); self.combo_mondo_view.pack(side="left", padx=5)
        self.combo_mondo_view.bind("<<ComboboxSelected>>", lambda e: self.aggiorna_menu_gamme())
        self.combo_view_gamma = ttk.Combobox(f_top, state="readonly"); self.combo_view_gamma.pack(side="left", padx=10)
        self.combo_view_gamma.bind("<<ComboboxSelected>>", lambda e: self.carica_gamma(e, "view"))
        container = tk.Frame(self.tab_view); container.pack(expand=1, fill="both")
        self.tree = ttk.Treeview(container, columns=("Codice", "Prezzo", "Bancale", "PzM2", "PzScatola"), show='headings')
        for col in ("Codice", "Prezzo", "Bancale", "PzM2", "PzScatola"): 
            self.tree.heading(col, text=col); self.tree.column(col, width=120, anchor="center")
        self.tree.pack(expand=1, fill="both")

    def aggiorna_menu_gamme(self, event=None):
        idx = self.tab_control.index("current"); mondo = self.combo_mondo.get() if idx == 0 else self.combo_mondo_view.get()
        path = os.path.join(self.base_folder, mondo); file_presenti = sorted([f.replace(".json", "") for f in os.listdir(path) if f.endswith(".json")])
        self.combo_gamma['values'] = file_presenti; self.combo_view_gamma['values'] = file_presenti; self.combo_rimuovi_gamma['values'] = file_presenti

    def carica_gamma(self, event=None, source="calc"):
        mondo = self.combo_mondo.get() if source == "calc" else self.combo_mondo_view.get()
        nome_gamma = self.combo_gamma.get() if source == "calc" else self.combo_view_gamma.get()
        path = os.path.join(self.base_folder, mondo, f"{nome_gamma}.json")
        if os.path.exists(path):
            with open(path, 'r') as f: self.prodotti = json.load(f)
            self.combo_prodotti['values'] = sorted(list(self.prodotti.keys()))
            self.aggiorna_tabella()

    def importa_csv(self):
        mondo = self.combo_mondo_import.get(); nome_gamma = simpledialog.askstring("Nuova Gamma", f"Nome listino in {mondo}:")
        if not nome_gamma: return
        path_csv = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path_csv: return
        try:
            with open(path_csv, mode='r', encoding='utf-8-sig') as f:
                content = f.read(); sep = ';' if ';' in content else ','
                f.seek(0); reader = csv.DictReader(f, delimiter=sep)
                nuovi = {}
                for row in reader:
                    r = {k.strip().lower(): v for k, v in row.items() if k}
                    cod = r.get('codice', '').strip()
                    if not cod: continue
                    def pul(v):
                        try: return float(str(v).replace(',','.'))
                        except: return 0.0
                    nuovi[cod] = {"prezzo": pul(r.get('prezzo','0')), "pz_bancale": pul(r.get('bancale','1')), "pz_m2": pul(r.get('pzm2','1')), "pz_scatola": pul(r.get('pzscatola','1'))}
                with open(os.path.join(self.base_folder, mondo, f"{nome_gamma}.json"), 'w') as f: json.dump(nuovi, f)
                self.aggiorna_menu_gamme(); messagebox.showinfo("OK", "Importato!")
        except Exception as e: messagebox.showerror("Errore", str(e))

    def pulisci_campi(self):
        self.ent_qty.delete(0, tk.END); self.ent_extra.delete(0, tk.END); self.ent_extra.insert(0, "0")
        self.ent_pietra_perc.delete(0, tk.END); self.ent_pietra_perc.insert(0, "0"); self.txt_risultato.delete(1.0, tk.END)

    def aggiorna_tabella(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for cod, info in sorted(self.prodotti.items()): self.tree.insert("", tk.END, values=(cod, f"{info['prezzo']:.3f} €", info['pz_bancale'], info['pz_m2'], info['pz_scatola']))

    def cancella_gamma(self):
        idx = self.tab_control.index("current"); mondo = self.combo_mondo.get() if idx == 0 else self.combo_mondo_view.get()
        g = self.combo_rimuovi_gamma.get()
        if g and messagebox.askyesno("Alt", f"Elimino {g}?"): 
            os.remove(os.path.join(self.base_folder, mondo, f"{g}.json")); self.aggiorna_menu_gamme()

if __name__ == "__main__":
    root = tk.Tk(); app = PreventivatoreApp(root); root.mainloop()
