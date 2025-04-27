import streamlit as st 
import pandas as pd

st.set_page_config(page_title="Archivio Banda afis", layout="wide",initial_sidebar_state="expanded")

st.sidebar.title("GUIDA ALL'USO")
# st.sidebar.header("GUIDA ALL'USO")

st.sidebar.markdown("""
Questo è l'Archivio completo della banda aggiornato a novembre 2024.<br><br>
I possibili errori che si possono riscontrare nella ricerca dei brani sono 
possibili errori di battitura nelle colonne che non sono **CLASSIFICATORE**, 
in quanto è da ritenersi la fonte più affidabile per la ricerca dei brani. 
Digitando il titolo, potrebbe non esserci una corrispondenza.

Per garantire la possibilità di correzioni se si trovano errori, è possibile modificare il file 
che viene esposto, che verrà salvato con le correzioni 
e con la possibilità di scaricarlo corretto
""", unsafe_allow_html=True)

df = pd.read_excel("ARCHIVIO COMPLETO 2024.xlsx")
df['DIFFICOLTA'] = df['DIFFICOLTA'].astype(str)
df["DIFFICOLTA"] = df["DIFFICOLTA"].replace("nan","-")
st.header("Archivio completo banda")

# --- BARRA DI RICERCA AVANZATA ---
search_input = st.text_input("🔎 Ricerca per Classificatore, Titolo, Autore, ...")


# --- FILTRI SU GENERE E CLASSIFICATORE ---
col1, col2 = st.columns(2)

with col1:
    classificatori_unici = df['CLASSIFICATORE'].dropna().unique().tolist()
    classificatori_selezionati = st.multiselect("🗂️ Filtra per Classificatore", options=sorted(classificatori_unici))

with col2:
    generi_unici = df['GENERE'].dropna().unique().tolist()
    generi_selezionati = st.multiselect("🎼 Filtra per Genere (Attenzione, non tutti i brani hanno il genere disponibile)", options=sorted(generi_unici))


# Applica filtri
if generi_selezionati:
    df = df[df['GENERE'].isin(generi_selezionati)]

if classificatori_selezionati:
    df = df[df['CLASSIFICATORE'].isin(classificatori_selezionati)]

# Funzione di ricerca avanzata
def advanced_search(df, search_input):
    if not search_input:
        return df
    keywords = search_input.lower().split()  # Dividi in parole singole
    mask = df.apply(lambda row: all(
        any(word in str(cell).lower() for cell in row) for word in keywords
    ), axis=1)
    return df[mask]

# Applica filtro avanzato
df_filtered = advanced_search(df, search_input)

# Mostra il dataframe filtrato
st.dataframe(df_filtered, height=600)
