import streamlit as st
import pandas as pd
from pathlib import Path
import io

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Archivio Banda AFIS", layout="wide", initial_sidebar_state="collapsed"
)

# --- CONFIGURAZIONE LOGO ---
st.sidebar.text("Made for afis by Matteo Spoladore")

# --- SIDEBAR ---
st.sidebar.title("GUIDA ALL'USO")
st.sidebar.markdown(
    """
Questo è l'Archivio completo della banda aggiornato a novembre 2024.<br><br>
Si possono riscontrare errori nella ricerca dovuti ad errori nella scrittura dei dati (es. Grna Vrietà)
La colonna che non presenta errori è **CLASSIFICATORE**, 
in quanto è da ritenersi la fonte più affidabile per la ricerca dei brani.<br><br>
Digitando il titolo, potrebbe non esserci una corrispondenza.

Per garantire la possibilità di correzioni se si trovano errori, è possibile modificare il file 
che viene esposto, che verrà salvato con le correzioni (verrà valutato se mantenerla da me)
e con la possibilità di scaricarlo corretto una volta premuto il bottone "salva modifiche".
""",
    unsafe_allow_html=True,
)

# --- CARICAMENTO DATI ---
file_path = Path("./Archivio 2025.xlsx")
if not file_path.exists():
    st.error(f"File non trovato: {file_path.resolve()}")
    st.stop()

df = pd.read_excel(file_path)
df_originale = df.copy()

# sistema DIFFICOLTA
df_originale["DIFFICOLTA"] = df_originale["DIFFICOLTA"].astype(str)
df_originale["DIFFICOLTA"] = df_originale["DIFFICOLTA"].replace("nan", "-")

st.header("Archivio completo banda")

# --- BARRA DI RICERCA AVANZATA ---
search_input = st.text_input(
    "🔎 Ricerca per Classificatore, Titolo, Autore, ...",
    placeholder="Esempio A01 Mozart MAMBO N°5 ..."
)

# --- FILTRI SU CLASSIFICATORE E GENERE ---
col1, col2 = st.columns(2)
with col1:
    classificatori_unici = df_originale["CLASSIFICATORE"].dropna().unique().tolist()
    classificatori_selezionati = st.multiselect(
        "🗂️ Filtra per Classificatore",
        options=sorted(classificatori_unici),
        placeholder="Seleziona classificatori..."
    )
with col2:
    generi_unici = df_originale["GENERE"].dropna().unique().tolist()
    generi_selezionati = st.multiselect(
        "🎼 Filtra per Genere (Attenzione: non tutti i brani hanno il genere disponibile)",
        options=sorted(generi_unici),
        placeholder="Seleziona generi..."
    )

# --- APPLICAZIONE FILTRI (su una copia di lavoro) ---
df_lavoro = df_originale.copy()
if generi_selezionati:
    df_lavoro = df_lavoro[df_lavoro["GENERE"].isin(generi_selezionati)]
if classificatori_selezionati:
    df_lavoro = df_lavoro[df_lavoro["CLASSIFICATORE"].isin(classificatori_selezionati)]

# --- FUNZIONE RICERCA AVANZATA ---
def advanced_search(df_in, search_input):
    if not search_input:
        return df_in
    keywords = search_input.lower().split()
    mask = df_in.apply(
        lambda row: all(
            any(word in str(cell).lower() for cell in row) for word in keywords
        ),
        axis=1,
    )
    return df_in[mask]

# --- APPLICAZIONE RICERCA ---
df_filtered = advanced_search(df_lavoro, search_input)

# --- PREPARO LA TABELLA DA MOSTRARE con indice originale ---
df_display = df_filtered.reset_index().rename(columns={"index": "INDICE"})

# salva la lista di indici mostrati (usata per identificare cancellazioni)
displayed_indices = df_display["INDICE"].tolist()

# mostra editor
st.subheader("📝 Modifica i dati se necessario:")
edited_df = st.data_editor(df_display, height=500, num_rows="dynamic")

# funzione di utilità per serializzare e offrire download
def to_excel_bytes(df_to_save: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_to_save.to_excel(writer, index=False)
    return buffer.getvalue()

# --- SALVATAGGIO MODIFICHE NEL DATAFRAME ORIGINALE (gestisce update, add, delete) ---
if st.button("💾 Salva modifiche"):
    try:
        if edited_df is None:
            st.warning("Nessuna modifica rilevata.")
        else:
            if "INDICE" not in edited_df.columns:
                st.error("Indice originale non trovato nelle colonne modificate. Impossibile aggiornare.")
            else:
                cols_validi = [c for c in edited_df.columns if c in df_originale.columns]
                if not cols_validi:
                    st.error("Nessuna colonna valida da aggiornare/aggiungere.")
                else:
                    # separa righe esistenti (INDICE notna) e nuove (INDICE na)
                    existing_rows = edited_df[edited_df["INDICE"].notna()].copy()
                    new_rows = edited_df[edited_df["INDICE"].isna()].copy()

                    # normalizza tipo INDICE se possibile
                    try:
                        existing_rows["INDICE"] = existing_rows["INDICE"].astype(int)
                        displayed_indices_norm = [int(i) for i in displayed_indices if pd.notna(i)]
                    except Exception:
                        displayed_indices_norm = [i for i in displayed_indices if pd.notna(i)]

                    # ----- Aggiorna righe esistenti -----
                    if not existing_rows.empty:
                        for _, row in existing_rows.iterrows():
                            idx = row["INDICE"]
                            if idx in df_originale.index:
                                for col in cols_validi:
                                    df_originale.at[idx, col] = row[col]
                            else:
                                # se l'indice non è più presente, append come nuova riga
                                to_append = row[cols_validi].to_frame().T
                                df_originale = pd.concat([df_originale, to_append], ignore_index=True)

                    # ----- Aggiungi nuove righe (quelle senza INDICE) -----
                    if not new_rows.empty:
                        new_to_append = new_rows[cols_validi].copy()
                        df_originale = pd.concat([df_originale, new_to_append], ignore_index=True)

                    # ----- RILEVA ED ESEGUE CANCELLAZIONI -----
                    remaining_indices = []
                    if not existing_rows.empty:
                        remaining_indices = existing_rows["INDICE"].tolist()
                    # calcola quali indici sono stati cancellati dall'utente
                    deleted_indices = []
                    try:
                        deleted_indices = list(set(displayed_indices_norm) - set([int(i) for i in remaining_indices]))
                    except Exception:
                        deleted_indices = list(set(map(str, displayed_indices)) - set(map(str, remaining_indices)))

                    if deleted_indices:
                        for didx in deleted_indices:
                            if didx in df_originale.index:
                                df_originale = df_originale.drop(index=didx)
                        df_originale = df_originale.reset_index(drop=True)

                    # salva su file (sovrascrive)
                    df_originale.to_excel(file_path, index=False)
                    st.success("✅ Modifiche salvate correttamente su tutto l'archivio!")
    except Exception as e:
        st.error(f"Errore durante il salvataggio: {e}")

# --- GENERA BYTES EXCEL (sempre disponibili) ---
excel_bytes = to_excel_bytes(df_originale)

# --- BOTTONE DI DOWNLOAD (sempre visibile) ---
st.download_button(
    "📥 Scarica copia aggiornata (Excel)",
    excel_bytes,
    file_name="Archivio_2025_aggiornato.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
