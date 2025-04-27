import streamlit as st 
import pandas as pd

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Archivio Banda AFIS", layout="wide", initial_sidebar_state="expanded")

# --- SIDEBAR ---
st.sidebar.title("GUIDA ALL'USO")
st.sidebar.markdown("""
Questo è l'Archivio completo della banda aggiornato a novembre 2024.<br><br>
I possibili errori che si possono riscontrare nella ricerca dei brani sono 
possibili errori di battitura nelle colonne che non sono **CLASSIFICATORE**, 
in quanto è da ritenersi la fonte più affidabile per la ricerca dei brani.<br><br>
Digitando il titolo, potrebbe non esserci una corrispondenza.

Per garantire la possibilità di correzioni se si trovano errori, è possibile modificare il file 
che viene esposto, che verrà salvato con le correzioni 
e con la possibilità di scaricarlo corretto una volta premuto il bottone "salva modifiche".
""", unsafe_allow_html=True)

# --- CARICAMENTO DATI ---
df = pd.read_excel("ARCHIVIO COMPLETO 2024 aggiornato.xlsx")
df['DIFFICOLTA'] = df['DIFFICOLTA'].astype(str)
df["DIFFICOLTA"] = df["DIFFICOLTA"].replace("nan", "-")

st.header("Archivio completo banda")

# --- BARRA DI RICERCA AVANZATA ---
search_input = st.text_input("🔎 Ricerca per Classificatore, Titolo, Autore, ...",placeholder="Esempio A01 Mozart MAMBO N°5 ...")

# --- FILTRI SU CLASSIFICATORE E GENERE ---
col1, col2 = st.columns(2)

with col1:
    classificatori_unici = df['CLASSIFICATORE'].dropna().unique().tolist()
    classificatori_selezionati = st.multiselect("🗂️ Filtra per Classificatore", options=sorted(classificatori_unici), 
                                                placeholder="Seleziona classificatori...")

with col2:
    generi_unici = df['GENERE'].dropna().unique().tolist()
    generi_selezionati = st.multiselect("🎼 Filtra per Genere (Attenzione: non tutti i brani hanno il genere disponibile)", options=sorted(generi_unici),
                                        placeholder="Seleziona generi...")

# --- COPIA ORIGINALE PER LAVORARE IN PARALLELO ---
df_originale = df.copy()

# --- APPLICAZIONE FILTRI ---
if generi_selezionati:
    df = df[df['GENERE'].isin(generi_selezionati)]

if classificatori_selezionati:
    df = df[df['CLASSIFICATORE'].isin(classificatori_selezionati)]

# --- FUNZIONE RICERCA AVANZATA ---
def advanced_search(df, search_input):
    if not search_input:
        return df
    keywords = search_input.lower().split()
    mask = df.apply(lambda row: all(
        any(word in str(cell).lower() for cell in row) for word in keywords
    ), axis=1)
    return df[mask]

# --- APPLICAZIONE RICERCA ---
df_filtered = advanced_search(df, search_input)

# --- MODIFICA DEL DATAFRAME FILTRATO ---
st.subheader("📝 Modifica i dati se necessario:")
edited_df = st.data_editor(df_filtered, height=500, num_rows="dynamic")

# --- SALVATAGGIO MODIFICHE NEL DATAFRAME ORIGINALE ---
if st.button("💾 Salva modifiche"):
    try:
        # Aggiorna SOLO le righe corrispondenti nel df_originale
        df_originale.update(edited_df)

        # Salva tutto il DataFrame originale aggiornato
        df_originale.to_excel("ARCHIVIO COMPLETO 2024 aggiornato.xlsx", index=False)
        st.success("✅ Modifiche salvate correttamente su tutto l'archivio!")
    except Exception as e:
        st.error(f"Errore durante il salvataggio: {e}")
