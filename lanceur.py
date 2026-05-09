"""
Lanceur GUI — Scraper signal-arnaques.com
==========================================
Double-cliquez sur ce fichier ou lancez : python lanceur.py
"""

import collections
import io
import json
import re
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk

# ── Liste des tags connus ──────────────────────────────────────────────────────
TAGS = {
    "Sites d'annonces": [
        "vinted", "leboncoin", "facebook-marketplace", "seloger",
        "pap", "vivastreet", "lacentrale", "la-centrale",
    ],
    "E-commerce": [
        "amazon", "cdiscount", "fnac", "darty", "ebay",
        "aliexpress", "shein", "temu", "wish",
    ],
    "Paiement / Banque": [
        "paypal", "paylib", "lydia", "sumeria",
        "credit-agricole", "bnp", "societe-generale",
        "caisse-epargne", "lcl", "boursorama", "orange-bank",
        "revolut", "wise",
    ],
    "Livraison / Colis": [
        "chronopost", "colissimo", "laposte", "mondial-relay",
        "ups", "dhl", "fedex", "dpd", "gls",
    ],
    "Réseaux sociaux": [
        "facebook", "instagram", "whatsapp", "telegram",
        "snapchat", "twitter", "tiktok", "linkedin",
    ],
    "Streaming / Abonnements": [
        "netflix", "spotify", "disney", "canal", "prime",
        "deezer", "molotov",
    ],
    "Administrations / Services publics": [
        "impots", "ameli", "cpam", "caf", "urssaf",
        "retraite", "assurance-maladie", "antai", "prefecture",
        "service-public",
    ],
    "Énergie / Télécom": [
        "edf", "enedis", "engie", "sfr", "orange",
        "free", "bouygues", "sosh",
    ],
    "Divers": [
        "sms", "email", "telephone", "phishing",
        "arnaque", "escroquerie", "crypto", "bitcoin",
        "investissement", "emploi", "loterie", "cagnotte",
    ],
}

# ── Stop words français ────────────────────────────────────────────────────────
STOP_FR = {
    "le","la","les","un","une","des","de","du","en","et","est","au","aux",
    "ce","se","sa","son","ses","mon","ma","mes","ton","ta","tes","leur","leurs",
    "je","tu","il","elle","nous","vous","ils","elles","on",
    "que","qui","quoi","dont","ou","où","si","car","mais","donc","or","ni",
    "par","pour","sur","sous","dans","avec","sans","entre","vers","chez",
    "plus","très","bien","tout","tous","toute","toutes","même","aussi","puis",
    "pas","ne","plus","rien","jamais","avoir","être","fait","cette","cet",
    "ils","elles","comme","alors","après","avant","lors","depuis",
    "http","https","www","com","fr","net","org","php","html",
    "nan","none","null","vos","votre","notre","nos",
}

# ── Champs texte à analyser ────────────────────────────────────────────────────
TEXT_FIELDS = ["titre", "apercu", "contenu", "commentaire",
               "statut", "categorie", "themes", "pseudonyme"]

# ── Couleurs ───────────────────────────────────────────────────────────────────
BG      = "#1e1e2e"
BG2     = "#2a2a3e"
BG3     = "#12121e"
ACCENT  = "#7c6ff7"
ACCENT2 = "#5bc0eb"
SUCCESS = "#4caf50"
WARNING = "#ff9800"
DANGER  = "#f44336"
FG      = "#e0e0f0"
FG2     = "#a0a0c0"
FONT_M  = ("Segoe UI", 10)
FONT_B  = ("Segoe UI", 10, "bold")
FONT_S  = ("Segoe UI", 9)
MONO    = ("Consolas", 9)

HERE = Path(__file__).parent


# ══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lanceur — Scraper signal-arnaques.com")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(960, 660)

        self._proc: subprocess.Popen | None = None
        self._all_records: list[dict] = []

        self._style_ttk()
        self._build_ui()
        self._refresh_ids_status()

    # ── Styles ttk ────────────────────────────────────────────────────────────

    def _style_ttk(self):
        s = ttk.Style()
        s.theme_use("clam")
        # Notebook
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab",
                    background=BG2, foreground=FG2,
                    font=("Segoe UI", 10, "bold"),
                    padding=[14, 6])
        s.map("TNotebook.Tab",
              background=[("selected", ACCENT)],
              foreground=[("selected", "white")])
        # Treeview
        for name in ("Tags", "Words", "Results"):
            s.configure(f"{name}.Treeview",
                        background=BG2, fieldbackground=BG2,
                        foreground=FG, font=FONT_S,
                        rowheight=22, borderwidth=0)
            s.configure(f"{name}.Treeview.Heading",
                        background=BG, foreground=FG2,
                        font=FONT_S, relief="flat")
            s.map(f"{name}.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])
        # Scrollbar
        s.configure("Vertical.TScrollbar",
                    background=BG2, troughcolor=BG3,
                    arrowcolor=FG2, borderwidth=0)

    # ── UI principale ─────────────────────────────────────────────────────────

    def _build_ui(self):
        header = tk.Frame(self, bg=ACCENT, padx=16, pady=8)
        header.pack(fill="x")
        tk.Label(header, text="Scraper signal-arnaques.com",
                 bg=ACCENT, fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(header, text="Formation anti-arnaques seniors",
                 bg=ACCENT, fg="#d0cff8", font=FONT_S).pack(side="right", padx=4)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=6)

        tab1 = tk.Frame(nb, bg=BG)
        tab2 = tk.Frame(nb, bg=BG)
        nb.add(tab1, text="  ▶  Lanceur  ")
        nb.add(tab2, text="  📊  Stats & Recherche  ")
        nb.bind("<<NotebookTabChanged>>",
                lambda e: self._on_tab_change(nb.index(nb.select())))

        self._build_launcher(tab1)
        self._build_stats(tab2)

    def _on_tab_change(self, idx):
        if idx == 1:
            self._load_all_data()

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 1 — Lanceur
    # ══════════════════════════════════════════════════════════════════════════

    def _build_launcher(self, parent):
        body = tk.Frame(parent, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        left = tk.Frame(body, bg=BG, width=340)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_console(right)

    def _build_left(self, parent):
        self._section(parent, "Tag à scraper")

        sf = tk.Frame(parent, bg=BG)
        sf.pack(fill="x", pady=(0, 4))
        tk.Label(sf, text="Recherche :", bg=BG, fg=FG2, font=FONT_S).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._filter_tags)
        tk.Entry(sf, textvariable=self._search_var,
                 bg=BG2, fg=FG, insertbackground=FG,
                 relief="flat", font=FONT_M, width=18).pack(side="left", padx=4)

        tf = tk.Frame(parent, bg=BG)
        tf.pack(fill="both", expand=True)
        self._tree = ttk.Treeview(tf, style="Tags.Treeview",
                                  selectmode="browse", show="tree headings")
        self._tree["columns"] = ("tag",)
        self._tree.heading("#0", text="Catégorie")
        self._tree.heading("tag", text="Tag")
        self._tree.column("#0", width=140, minwidth=100)
        self._tree.column("tag", width=140, minwidth=80)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_tag_select)
        self._populate_tree(TAGS)

        cf = tk.Frame(parent, bg=BG)
        cf.pack(fill="x", pady=4)
        tk.Label(cf, text="Tag personnalisé :", bg=BG, fg=FG2, font=FONT_S).pack(side="left")
        self._tag_var = tk.StringVar(value="vinted")
        tk.Entry(cf, textvariable=self._tag_var,
                 bg=BG2, fg=ACCENT2, insertbackground=FG,
                 relief="flat", font=FONT_B, width=16).pack(side="left", padx=4)

        self._section(parent, "Options")
        self._mode_var = tk.StringVar(value="detail")
        for txt, val in [("Rapide (top 10 seulement)", "rapide"),
                         ("Complet (toutes les arnaques)", "detail")]:
            tk.Radiobutton(parent, text=txt, variable=self._mode_var, value=val,
                           bg=BG, fg=FG, selectcolor=ACCENT,
                           activebackground=BG, activeforeground=FG,
                           font=FONT_S).pack(anchor="w", padx=8)

        mf = tk.Frame(parent, bg=BG)
        mf.pack(fill="x", padx=8, pady=2)
        tk.Label(mf, text="Limite (0 = tout) :", bg=BG, fg=FG2, font=FONT_S).pack(side="left")
        self._max_var = tk.StringVar(value="0")
        tk.Entry(mf, textvariable=self._max_var,
                 bg=BG2, fg=FG, insertbackground=FG,
                 relief="flat", font=FONT_M, width=6).pack(side="left", padx=4)

        # Délai entre requêtes
        df = tk.Frame(parent, bg=BG)
        df.pack(fill="x", padx=8, pady=2)
        tk.Label(df, text="Délai entre requêtes (s) :", bg=BG, fg=FG2, font=FONT_S).pack(side="left")
        self._delay_lo_var = tk.StringVar(value="10")
        self._delay_hi_var = tk.StringVar(value="25")
        tk.Entry(df, textvariable=self._delay_lo_var,
                 bg=BG2, fg=FG, insertbackground=FG,
                 relief="flat", font=FONT_M, width=4).pack(side="left", padx=2)
        tk.Label(df, text="–", bg=BG, fg=FG2, font=FONT_S).pack(side="left")
        tk.Entry(df, textvariable=self._delay_hi_var,
                 bg=BG2, fg=FG, insertbackground=FG,
                 relief="flat", font=FONT_M, width=4).pack(side="left", padx=2)

        # Presets délai
        pf = tk.Frame(parent, bg=BG)
        pf.pack(fill="x", padx=8, pady=0)
        tk.Label(pf, text="Preset :", bg=BG, fg=FG2, font=FONT_S).pack(side="left")
        for label, lo, hi in [("Normal", "10", "25"), ("Lent", "20", "45"), ("Très lent", "40", "90")]:
            lo_, hi_ = lo, hi
            tk.Button(pf, text=label, bg=BG2, fg=FG2, relief="flat",
                      font=FONT_S, cursor="hand2", padx=5,
                      command=lambda l=lo_, h=hi_: (
                          self._delay_lo_var.set(l),
                          self._delay_hi_var.set(h)
                      )).pack(side="left", padx=2)

        # Options debug / reprise
        opt_frame = tk.Frame(parent, bg=BG)
        opt_frame.pack(fill="x", padx=8, pady=2)
        self._debug_var  = tk.BooleanVar(value=True)
        self._resume_var = tk.BooleanVar(value=False)
        self._proxy_var  = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_frame, text="Debug (logs fichier)",
                       variable=self._debug_var,
                       bg=BG, fg=FG2, selectcolor=ACCENT,
                       activebackground=BG, font=FONT_S).pack(side="left")
        tk.Checkbutton(opt_frame, text="Reprendre (--resume)",
                       variable=self._resume_var,
                       bg=BG, fg=FG2, selectcolor=ACCENT,
                       activebackground=BG, font=FONT_S).pack(side="left", padx=8)
        tk.Checkbutton(opt_frame, text="Proxy FR (--proxy)",
                       variable=self._proxy_var,
                       bg=BG, fg=FG2, selectcolor=ACCENT,
                       activebackground=BG, font=FONT_S).pack(side="left")

        self._section(parent, "Actions")
        self._ids_status = tk.Label(parent, text="", bg=BG, fg=FG2, font=FONT_S,
                                    wraplength=310, justify="left")
        self._ids_status.pack(anchor="w", padx=8, pady=2)

        self._checkpoint_status = tk.Label(parent, text="", bg=BG, fg=FG2,
                                           font=FONT_S, wraplength=310, justify="left")
        self._checkpoint_status.pack(anchor="w", padx=8, pady=0)

        btn = dict(relief="flat", cursor="hand2", padx=10, pady=6, font=FONT_B, bd=0)
        tk.Button(parent, text="① Collecter les IDs  (PowerShell requis)",
                  bg="#3a3a5e", fg=ACCENT2,
                  command=self._cmd_collect_ids, **btn).pack(fill="x", padx=8, pady=2)
        tk.Button(parent, text="② Lancer le scraper",
                  bg=ACCENT, fg="white",
                  command=self._cmd_scrape, **btn).pack(fill="x", padx=8, pady=2)

        # Bannière ban + bouton retry VPN
        self._ban_frame = tk.Frame(parent, bg="#3a1a1a")
        self._ban_frame.pack(fill="x", padx=8, pady=2)
        self._ban_frame.pack_forget()  # caché par défaut
        tk.Label(self._ban_frame,
                 text="  IP bannie par Cloudflare — changez d'IP (VPN) puis :",
                 bg="#3a1a1a", fg="#ff8a80", font=FONT_S,
                 wraplength=300, justify="left").pack(anchor="w", padx=4, pady=2)
        tk.Button(self._ban_frame,
                  text="⟳  J'ai changé d'IP — Reprendre le scrape",
                  bg="#6a1a1a", fg="#ff8a80",
                  relief="flat", cursor="hand2", font=FONT_B, padx=8, pady=5,
                  command=self._cmd_resume_after_ban).pack(fill="x", padx=4, pady=4)

        # Séparateur
        tk.Frame(parent, bg=ACCENT, height=1).pack(fill="x", padx=8, pady=6)

        # Scraper tout le site
        tk.Label(parent, text="Scraper tous les tags en séquence :",
                 bg=BG, fg=FG2, font=FONT_S).pack(anchor="w", padx=8)

        # Sélection des tags à inclure
        sel_frame = tk.Frame(parent, bg=BG)
        sel_frame.pack(fill="x", padx=8, pady=2)
        self._all_tags_list = [t for tags in TAGS.values() for t in tags]
        self._tag_check_vars: dict[str, tk.BooleanVar] = {}

        chk_win = tk.Frame(sel_frame, bg=BG2, relief="flat")
        chk_win.pack(fill="x")

        # Boutons sélectionner/désélectionner tout
        row_sel = tk.Frame(chk_win, bg=BG2)
        row_sel.pack(fill="x", padx=4, pady=2)
        tk.Button(row_sel, text="Tout cocher", bg=BG, fg=FG2, relief="flat",
                  font=FONT_S, cursor="hand2", padx=4,
                  command=lambda: self._check_all_tags(True)).pack(side="left")
        tk.Button(row_sel, text="Tout décocher", bg=BG, fg=FG2, relief="flat",
                  font=FONT_S, cursor="hand2", padx=4,
                  command=lambda: self._check_all_tags(False)).pack(side="left", padx=4)

        # Canvas scrollable pour les checkboxes
        canvas = tk.Canvas(chk_win, bg=BG2, height=90,
                           highlightthickness=0, bd=0)
        vsb_chk = ttk.Scrollbar(chk_win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb_chk.set)
        vsb_chk.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=BG2)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for i, tag in enumerate(self._all_tags_list):
            var = tk.BooleanVar(value=True)
            self._tag_check_vars[tag] = var
            col, row = divmod(i, 12)
            tk.Checkbutton(inner, text=tag, variable=var,
                           bg=BG2, fg=FG, selectcolor=ACCENT,
                           activebackground=BG2, font=FONT_S,
                           anchor="w").grid(row=row, column=col,
                                            sticky="w", padx=6, pady=0)

        self._all_progress = tk.Label(parent, text="", bg=BG, fg=FG2, font=FONT_S)
        self._all_progress.pack(anchor="w", padx=8, pady=2)

        tk.Button(parent, text="▶▶ Scraper TOUT le site",
                  bg="#2d5a27", fg="#a5d6a7",
                  command=self._cmd_scrape_all, **btn).pack(fill="x", padx=8, pady=2)

        # Séparateur
        tk.Frame(parent, bg=ACCENT, height=1).pack(fill="x", padx=8, pady=6)

        tk.Button(parent, text="⏹  Arrêter",
                  bg="#3a2a2a", fg=DANGER,
                  command=self._cmd_stop, **btn).pack(fill="x", padx=8, pady=2)
        tk.Button(parent, text="Vider la console",
                  bg=BG2, fg=FG2,
                  command=self._clear_console, **btn).pack(fill="x", padx=8, pady=(8, 2))

    def _build_console(self, parent):
        self._section(parent, "Console")
        self._console = tk.Text(parent, bg=BG3, fg="#c8ffc8",
                                font=MONO, relief="flat",
                                state="disabled", wrap="word")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self._console.yview)
        self._console.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._console.pack(fill="both", expand=True)
        self._console.tag_config("info",    foreground="#c8ffc8")
        self._console.tag_config("warn",    foreground="#ffe082")
        self._console.tag_config("error",   foreground="#ef9a9a")
        self._console.tag_config("accent",  foreground="#80deea")
        self._console.tag_config("success", foreground="#a5d6a7")
        self._statusbar = tk.Label(parent, text="Prêt.",
                                   bg=BG2, fg=FG2, font=FONT_S,
                                   anchor="w", padx=8, pady=3)
        self._statusbar.pack(fill="x")

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 2 — Stats & Recherche
    # ══════════════════════════════════════════════════════════════════════════

    def _build_stats(self, parent):
        # ── Barre supérieure ──────────────────────────────────────────────────
        top = tk.Frame(parent, bg=BG2, padx=8, pady=6)
        top.pack(fill="x")

        tk.Label(top, text="Fichiers chargés :", bg=BG2, fg=FG2, font=FONT_S).pack(side="left")
        self._data_info = tk.Label(top, text="—", bg=BG2, fg=ACCENT2, font=FONT_B)
        self._data_info.pack(side="left", padx=8)

        tk.Button(top, text="⟳ Recharger", bg=BG, fg=FG2, relief="flat",
                  font=FONT_S, cursor="hand2", padx=6,
                  command=self._load_all_data).pack(side="left", padx=4)

        tk.Label(top, text="Stop words :", bg=BG2, fg=FG2, font=FONT_S).pack(side="left", padx=(20, 4))
        self._stopwords_var = tk.BooleanVar(value=True)
        tk.Checkbutton(top, text="Activer", variable=self._stopwords_var,
                       bg=BG2, fg=FG, selectcolor=ACCENT,
                       activebackground=BG2, font=FONT_S,
                       command=self._refresh_words).pack(side="left")

        tk.Label(top, text="Min. occurrences :", bg=BG2, fg=FG2, font=FONT_S).pack(side="left", padx=(16, 4))
        self._min_occ_var = tk.StringVar(value="2")
        tk.Entry(top, textvariable=self._min_occ_var, width=4,
                 bg=BG, fg=FG, insertbackground=FG, relief="flat",
                 font=FONT_M).pack(side="left")
        tk.Button(top, text="Appliquer", bg=BG, fg=FG2, relief="flat",
                  font=FONT_S, cursor="hand2", padx=6,
                  command=self._refresh_words).pack(side="left", padx=4)

        # ── Corps principal ───────────────────────────────────────────────────
        body = tk.Frame(parent, bg=BG)
        body.pack(fill="both", expand=True, padx=8, pady=6)

        # Colonne gauche — fréquence des mots
        left = tk.Frame(body, bg=BG, width=320)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        self._section(left, "Fréquence des mots")

        wf = tk.Frame(left, bg=BG)
        wf.pack(fill="both", expand=True)
        self._words_tree = ttk.Treeview(wf, style="Words.Treeview",
                                        columns=("mot", "nb"), show="headings",
                                        selectmode="browse")
        self._words_tree.heading("mot", text="Mot",
                                 command=lambda: self._sort_words("mot"))
        self._words_tree.heading("nb",  text="Occurrences",
                                 command=lambda: self._sort_words("nb"))
        self._words_tree.column("mot", width=170, minwidth=100)
        self._words_tree.column("nb",  width=90,  minwidth=60, anchor="center")
        vsb = ttk.Scrollbar(wf, orient="vertical", command=self._words_tree.yview)
        self._words_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._words_tree.pack(fill="both", expand=True)
        self._words_tree.bind("<<TreeviewSelect>>", self._on_word_select)
        self._words_sort_col = "nb"
        self._words_sort_rev = True

        # Colonne droite — recherche + résultats
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._section(right, "Recherche dans les arnaques")

        search_row = tk.Frame(right, bg=BG)
        search_row.pack(fill="x", pady=4)
        tk.Label(search_row, text="Mot-clé :", bg=BG, fg=FG2, font=FONT_S).pack(side="left")
        self._kw_var = tk.StringVar()
        kw_entry = tk.Entry(search_row, textvariable=self._kw_var,
                            bg=BG2, fg=FG, insertbackground=FG,
                            relief="flat", font=FONT_M, width=28)
        kw_entry.pack(side="left", padx=6)
        kw_entry.bind("<Return>", lambda e: self._do_search())
        tk.Button(search_row, text="Rechercher", bg=ACCENT, fg="white",
                  relief="flat", font=FONT_B, cursor="hand2", padx=8,
                  command=self._do_search).pack(side="left")
        tk.Button(search_row, text="✕", bg=BG2, fg=FG2,
                  relief="flat", font=FONT_S, cursor="hand2", padx=4,
                  command=self._clear_search).pack(side="left", padx=2)
        self._result_count = tk.Label(search_row, text="", bg=BG, fg=FG2, font=FONT_S)
        self._result_count.pack(side="left", padx=8)

        # Treeview résultats
        rf = tk.Frame(right, bg=BG)
        rf.pack(fill="both", expand=True)

        res_cols = ("tag", "id", "date", "categorie", "apercu")
        self._res_tree = ttk.Treeview(rf, style="Results.Treeview",
                                      columns=res_cols, show="headings",
                                      selectmode="browse")
        self._res_tree.heading("tag",       text="Tag")
        self._res_tree.heading("id",        text="ID")
        self._res_tree.heading("date",      text="Date")
        self._res_tree.heading("categorie", text="Catégorie")
        self._res_tree.heading("apercu",    text="Aperçu")
        self._res_tree.column("tag",       width=80,  minwidth=60)
        self._res_tree.column("id",        width=70,  minwidth=50, anchor="center")
        self._res_tree.column("date",      width=80,  minwidth=60, anchor="center")
        self._res_tree.column("categorie", width=130, minwidth=80)
        self._res_tree.column("apercu",    width=300, minwidth=150)
        vsb2 = ttk.Scrollbar(rf, orient="vertical", command=self._res_tree.yview)
        self._res_tree.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right", fill="y")
        self._res_tree.pack(fill="both", expand=True)
        self._res_tree.bind("<<TreeviewSelect>>", self._on_result_select)

        # Détail du résultat sélectionné
        self._section(right, "Détail")
        self._detail_text = tk.Text(right, bg=BG3, fg=FG, font=FONT_S,
                                    height=7, relief="flat",
                                    state="disabled", wrap="word")
        self._detail_text.pack(fill="x")

        # Stockage des résultats affichés
        self._displayed_records: list[dict] = []

    # ── Chargement des données ─────────────────────────────────────────────────

    def _load_all_data(self):
        records = []
        files = sorted(HERE.glob("arnaques_*.json"))
        # Exclure les fichiers _listing et _partial
        files = [f for f in files
                 if "_listing" not in f.stem and "_partial" not in f.stem]
        for fp in files:
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                tag  = fp.stem.replace("arnaques_", "")
                for rec in data:
                    rec["_tag"]  = tag
                    rec["_file"] = fp.name
                records.extend(data)
            except Exception:
                pass

        # Fallback : aussi charger les listing
        if not records:
            for fp in sorted(HERE.glob("arnaques_*_listing.json")):
                try:
                    data = json.loads(fp.read_text(encoding="utf-8"))
                    tag  = fp.stem.replace("arnaques_", "").replace("_listing", "")
                    for rec in data:
                        rec["_tag"]  = tag
                        rec["_file"] = fp.name
                    records.extend(data)
                except Exception:
                    pass

        self._all_records = records
        nb    = len(records)
        tags  = sorted({r.get("_tag", "?") for r in records})
        label = f"{nb} arnaques  |  {len(tags)} tag(s) : {', '.join(tags)}"
        self._data_info.config(text=label if nb else "Aucun fichier arnaques_*.json trouvé")
        self._refresh_words()
        self._result_count.config(text="")
        self._res_tree.delete(*self._res_tree.get_children())
        self._displayed_records = []

    # ── Fréquence des mots ────────────────────────────────────────────────────

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower()
        tokens = re.findall(r"[a-záàâäéèêëîïôöùûüçœæ]{3,}", text)
        if self._stopwords_var.get():
            tokens = [t for t in tokens if t not in STOP_FR]
        return tokens

    def _count_words(self) -> collections.Counter:
        counter: collections.Counter = collections.Counter()
        for rec in self._all_records:
            for field in TEXT_FIELDS:
                val = rec.get(field) or ""
                counter.update(self._tokenize(val))
        return counter

    def _refresh_words(self):
        try:
            min_occ = int(self._min_occ_var.get())
        except ValueError:
            min_occ = 2

        counter = self._count_words()
        self._word_counter = counter

        self._words_tree.delete(*self._words_tree.get_children())
        pairs = [(w, n) for w, n in counter.items() if n >= min_occ]
        if self._words_sort_col == "nb":
            pairs.sort(key=lambda x: x[1], reverse=self._words_sort_rev)
        else:
            pairs.sort(key=lambda x: x[0], reverse=self._words_sort_rev)

        for word, nb in pairs:
            self._words_tree.insert("", "end", values=(word, nb))

    def _sort_words(self, col: str):
        if self._words_sort_col == col:
            self._words_sort_rev = not self._words_sort_rev
        else:
            self._words_sort_col = col
            self._words_sort_rev = col == "nb"
        self._refresh_words()

    def _on_word_select(self, _=None):
        sel = self._words_tree.selection()
        if not sel:
            return
        word = self._words_tree.item(sel[0], "values")[0]
        self._kw_var.set(word)
        self._do_search()

    # ── Recherche ─────────────────────────────────────────────────────────────

    def _do_search(self):
        kw = self._kw_var.get().strip().lower()
        self._res_tree.delete(*self._res_tree.get_children())
        self._displayed_records = []
        if not kw:
            self._result_count.config(text="")
            return

        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        matches = []
        for rec in self._all_records:
            for field in TEXT_FIELDS + ["email", "url_arnaque", "pseudonyme", "url"]:
                val = rec.get(field) or ""
                if pattern.search(val):
                    matches.append(rec)
                    break

        self._displayed_records = matches
        self._result_count.config(text=f"{len(matches)} résultat(s)")

        for rec in matches:
            apercu = (rec.get("apercu") or rec.get("contenu") or
                      rec.get("commentaire") or "")[:120]
            self._res_tree.insert("", "end", values=(
                rec.get("_tag", ""),
                rec.get("id", ""),
                rec.get("date", ""),
                (rec.get("categorie") or "")[:30],
                apercu,
            ))

    def _clear_search(self):
        self._kw_var.set("")
        self._res_tree.delete(*self._res_tree.get_children())
        self._displayed_records = []
        self._result_count.config(text="")
        self._detail_text.configure(state="normal")
        self._detail_text.delete("1.0", "end")
        self._detail_text.configure(state="disabled")

    def _on_result_select(self, _=None):
        sel = self._res_tree.selection()
        if not sel:
            return
        idx = self._res_tree.index(sel[0])
        if idx >= len(self._displayed_records):
            return
        rec = self._displayed_records[idx]

        lines = []
        for k, v in rec.items():
            if k.startswith("_") or not v:
                continue
            lines.append(f"{k:20s}: {v}")
        text = "\n".join(lines)

        self._detail_text.configure(state="normal")
        self._detail_text.delete("1.0", "end")
        self._detail_text.insert("end", text)
        self._detail_text.configure(state="disabled")

    # ── Scraper tout le site ──────────────────────────────────────────────────

    def _check_all_tags(self, state: bool):
        for var in self._tag_check_vars.values():
            var.set(state)

    def _cmd_scrape_all(self):
        selected = [t for t, v in self._tag_check_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Aucun tag", "Cochez au moins un tag.")
            return
        if self._proc and self._proc.poll() is None:
            messagebox.showwarning("En cours", "Un processus tourne déjà. Arrêtez-le d'abord.")
            return

        script = HERE / "scraper_signal_arnaques.py"
        mode   = self._mode_var.get()
        try:
            mx = int(self._max_var.get())
        except ValueError:
            mx = 0

        self._log(f"\n{'='*60}\n", "accent")
        self._log(f"  SCRAPING TOTAL — {len(selected)} tags\n", "accent")
        self._log(f"  {', '.join(selected)}\n", "info")
        self._log(f"{'='*60}\n\n", "accent")
        self._set_status(f"Scraping total en cours — 0/{len(selected)} tags")
        self._all_progress.config(text=f"0 / {len(selected)} tags traités")

        def _worker():
            for i, tag in enumerate(selected, 1):
                if self._proc and getattr(self._proc, "_stopped", False):
                    break
                self.after(0, self._log,
                           f"\n--- Tag {i}/{len(selected)} : {tag} ---\n", "accent")
                self.after(0, self._all_progress.config,
                           {"text": f"{i-1} / {len(selected)} — en cours : {tag}"})
                self.after(0, self._set_status,
                           f"Tag {i}/{len(selected)} : {tag}")

                cmd = [sys.executable, str(script), "--tag", tag]
                if mode == "detail":
                    cmd.append("--detail")
                if mx > 0:
                    cmd += ["--max", str(mx)]

                try:
                    self._proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        cwd=str(HERE),
                    )
                    for line in self._proc.stdout:
                        color = (
                            "error"   if any(w in line for w in ("ECHEC", "Bloqu", "[!]", "Sorry")) else
                            "warn"    if any(w in line for w in ("retry", "attente", "TIMEOUT")) else
                            "success" if any(w in line for w in ("OK", "sauveg", "Termine")) else
                            "accent"  if line.startswith("===") or line.startswith("[") else
                            "info"
                        )
                        self.after(0, self._log, line, color)
                    self._proc.wait()
                except Exception as e:
                    self.after(0, self._log, f"[Erreur] {tag}: {e}\n", "error")

            self.after(0, self._log,
                       f"\n{'='*60}\nScraping total terminé — {len(selected)} tags.\n{'='*60}\n",
                       "success")
            self.after(0, self._all_progress.config,
                       {"text": f"{len(selected)} / {len(selected)} tags traités"})
            self.after(0, self._set_status, "Scraping total terminé.")

        threading.Thread(target=_worker, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # Helpers communs
    # ══════════════════════════════════════════════════════════════════════════

    def _section(self, parent, title):
        tk.Label(parent, text=f"  {title}",
                 bg=ACCENT, fg="white", font=FONT_B,
                 padx=6, pady=3).pack(fill="x", pady=(8, 2))

    def _populate_tree(self, data: dict, filter_str: str = ""):
        for item in self._tree.get_children():
            self._tree.delete(item)
        q = filter_str.lower().strip()
        for cat, tags in data.items():
            visible = [t for t in tags if q in t.lower()] if q else tags
            if not visible:
                continue
            node = self._tree.insert("", "end", text=cat, open=bool(q))
            for tag in visible:
                self._tree.insert(node, "end", text="", values=(tag,))

    def _filter_tags(self, *_):
        self._populate_tree(TAGS, self._search_var.get())

    def _on_tag_select(self, _=None):
        sel = self._tree.selection()
        if not sel:
            return
        vals = self._tree.item(sel[0], "values")
        if vals:
            self._tag_var.set(vals[0])
            self._refresh_ids_status()

    def _refresh_ids_status(self):
        tag  = self._tag_var.get().strip()
        path = HERE / f"ids_{tag}.json"
        if path.exists():
            try:
                n = len(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                n = "?"
            self._ids_status.config(
                text=f"✔ ids_{tag}.json trouvé ({n} IDs)", fg=SUCCESS)
        else:
            self._ids_status.config(
                text=f"✘ ids_{tag}.json absent — lancez d'abord ①", fg=WARNING)

        # Statut checkpoint
        cp_path = HERE / f"checkpoint_{tag}.json"
        if cp_path.exists():
            try:
                cp = json.loads(cp_path.read_text(encoding="utf-8"))
                done  = cp.get("done_count", "?")
                total = cp.get("total_count", "?")
                upd   = cp.get("last_updated", "")[:16].replace("T", " ")
                self._checkpoint_status.config(
                    text=f"⏸ Checkpoint : {done}/{total} traités  ({upd})",
                    fg=WARNING)
                self._resume_var.set(True)
            except Exception:
                self._checkpoint_status.config(text="", fg=FG2)
        else:
            self._checkpoint_status.config(text="", fg=FG2)
            self._resume_var.set(False)

    def _log(self, text: str, tag: str = "info"):
        self._console.configure(state="normal")
        self._console.insert("end", text, tag)
        self._console.see("end")
        self._console.configure(state="disabled")

    def _clear_console(self):
        self._console.configure(state="normal")
        self._console.delete("1.0", "end")
        self._console.configure(state="disabled")

    def _set_status(self, text: str):
        self._statusbar.config(text=text)

    # ── Lancement processus ────────────────────────────────────────────────────

    def _get_tag(self) -> str | None:
        tag = self._tag_var.get().strip().lower()
        if not tag:
            messagebox.showwarning("Tag manquant", "Saisissez ou sélectionnez un tag.")
            return None
        return tag

    def _cmd_collect_ids(self):
        tag = self._get_tag()
        if not tag:
            return
        script = HERE / "collecter_ids.py"
        if not script.exists():
            messagebox.showerror("Fichier manquant", f"{script} introuvable.")
            return
        self._log(f"\n{'='*60}\n", "accent")
        self._log(f"  ÉTAPE 1 — Collecte des IDs  (tag: {tag})\n", "accent")
        self._log(f"{'='*60}\n", "accent")
        self._log("  Une fenêtre Chrome va s'ouvrir.\n  Ne la fermez pas avant la fin.\n\n", "warn")
        cmd = [sys.executable, str(script), "--tag", tag]
        self._run_in_powershell(cmd, tag)

    def _cmd_scrape(self):
        tag = self._get_tag()
        if not tag:
            return
        self._ban_frame.pack_forget()
        self._current_scrape_tag = tag
        self._build_scrape_cmd_and_run(tag, resume=self._resume_var.get())

    def _build_scrape_cmd_and_run(self, tag: str, resume: bool = False):
        script = HERE / "scraper_signal_arnaques.py"
        if not script.exists():
            messagebox.showerror("Fichier manquant", f"{script} introuvable.")
            return
        cmd = [sys.executable, str(script), "--tag", tag]
        if self._mode_var.get() == "detail":
            cmd.append("--detail")
        try:
            mx = int(self._max_var.get())
            if mx > 0:
                cmd += ["--max", str(mx)]
        except ValueError:
            pass
        if resume:
            cmd.append("--resume")
        if self._debug_var.get():
            cmd.append("--debug")
        if self._proxy_var.get():
            cmd.append("--proxy")
        try:
            dlo = float(self._delay_lo_var.get())
            dhi = float(self._delay_hi_var.get())
            cmd += ["--delay", str(dlo), str(dhi)]
        except (ValueError, AttributeError):
            pass
        mode_lbl = ("complet" if "--detail" in cmd else "rapide") + (" +resume" if resume else "")
        self._log(f"\n{'='*60}\n", "accent")
        self._log(f"  Scraping  tag: {tag}  mode: {mode_lbl}\n", "accent")
        try:
            self._log(f"  Délai : {self._delay_lo_var.get()}–{self._delay_hi_var.get()}s\n", "info")
        except Exception:
            pass
        if self._debug_var.get():
            self._log(f"  Debug actif -> logs/debug_{tag}_*.log\n", "warn")
        self._log(f"{'='*60}\n\n", "accent")
        self._run_subprocess(cmd)

    def _cmd_resume_after_ban(self):
        tag = getattr(self, "_current_scrape_tag", None) or self._get_tag()
        if not tag:
            return
        self._ban_frame.pack_forget()
        self._log(f"\n  Reprise après changement d'IP — tag: {tag}\n\n", "success")
        self._build_scrape_cmd_and_run(tag, resume=True)

    def _cmd_stop(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self._log("\n[Processus arrêté par l'utilisateur]\n", "warn")
            self._set_status("Arrêté.")

    def _run_in_powershell(self, cmd: list[str], tag: str):
        ps_cmd = " ".join(f'"{c}"' for c in cmd)
        full = (
            f'Start-Process powershell -ArgumentList '
            f'"-NoExit", "-Command", "cd \'{HERE}\'; {ps_cmd}" '
            f'-WindowStyle Normal'
        )
        subprocess.Popen(["powershell", "-Command", full])
        self._log("  PowerShell ouvert dans une nouvelle fenêtre.\n", "success")
        self._log(f"  Quand terminé, revenez ici et cliquez ②.\n\n", "info")
        self._set_status(f"PowerShell lancé pour {tag}. Attendez la fin avant ②.")

        def _watch():
            import time
            ids_path = HERE / f"ids_{tag}.json"
            for _ in range(300):
                time.sleep(1)
                if ids_path.exists():
                    self.after(0, self._refresh_ids_status)
                    self.after(0, lambda: self._log(
                        f"  ✔ ids_{tag}.json créé — vous pouvez lancer ②\n", "success"))
                    break
        threading.Thread(target=_watch, daemon=True).start()

    def _run_subprocess(self, cmd: list[str]):
        if self._proc and self._proc.poll() is None:
            messagebox.showwarning("En cours", "Un processus tourne déjà. Arrêtez-le d'abord.")
            return
        self._set_status("En cours…")

        def _worker():
            try:
                self._proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=str(HERE),
                )
                ban_detected = False
                for line in self._proc.stdout:
                    if "[BAN_DETECTED]" in line:
                        ban_detected = True
                    color = (
                        "error"   if any(w in line for w in ("ECHEC", "Erreur", "Bloqu", "[!]", "Sorry", "BAN")) else
                        "warn"    if any(w in line for w in ("retry", "attente", "Conseil", "TIMEOUT", "REPRISE")) else
                        "success" if any(w in line for w in ("OK", "sauveg", "Termine", "IDs charges")) else
                        "accent"  if line.startswith("===") or line.startswith("[") else
                        "info"
                    )
                    self.after(0, self._log, line, color)
                self._proc.wait()
                code = self._proc.returncode
                if code == 2 or ban_detected:
                    self.after(0, self._set_status, "BLOQUÉ par Cloudflare — changez d'IP.")
                    self.after(0, self._show_ban_banner)
                else:
                    self.after(0, self._set_status,
                               "Terminé avec succès." if code == 0 else f"Terminé (code {code}).")
                self.after(0, self._refresh_ids_status)
            except Exception as e:
                self.after(0, self._log, f"\n[Erreur interne] {e}\n", "error")
                self.after(0, self._set_status, "Erreur.")

        threading.Thread(target=_worker, daemon=True).start()

    def _show_ban_banner(self):
        self._ban_frame.pack(fill="x", padx=8, pady=4)
        self._log("\n  -> Bannière de reprise affichée dans les Actions.\n", "warn")


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    app = App()
    app.mainloop()
