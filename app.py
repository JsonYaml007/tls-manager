import streamlit as st
import pandas as pd

# Ustawienia strony
st.set_page_config(page_title="Liga Siatkówki - Manager", layout="wide")

# Funkcja do wczytywania wszystkich zakładek
@st.cache_data(ttl=300)  # Odświeżaj co 5 minut
def load_all_data(file_path):
    # Wczytujemy wszystkie arkusze do słownika DataFrames
    return pd.read_excel(file_path, sheet_name=None,engine='openpyxl')

# --- ŁADOWANIE DANYCH ---
# Możesz zamienić 'liga_siatkowki.xlsx' na URL do pliku na GitHubie/Google Drive
FILE_PATH = 'https://docs.google.com/spreadsheets/d/13-z6353IMtVxsvLVqRc4FJFh5sbAkQnvQrAXaaBRVHc/export?format=xlsx'


try:
    all_sheets = load_all_data(FILE_PATH)
    
    # Przypisanie arkuszy do zmiennych
    df_druzyny = all_sheets['Druzyny']
    df_sklady = all_sheets['Sklady']
    df_terminarz = all_sheets['Terminarz']
    df_wyniki = all_sheets['Wyniki']

    # --- BOCZNY PANEL NAWIGACJI ---
    st.sidebar.title("🏐 Menu Ligi")
    page = st.sidebar.radio("Wybierz sekcję:", 
        ["Tabela Główna", "Terminarz", "Wyniki", "Drużyny i Składy"])

    # --- LOGIKA PRZELICZANIA TABELI ---
    def calculate_standings(df_wyniki, df_druzyny):
        # Tworzymy pustą tabelę na bazie listy drużyn
        stats = {team: {'Mecze': 0, 'Punkty': 0, 'Sety_W': 0, 'Sety_P': 0} 
                 for team in df_druzyny['Nazwa_druzyny']}
        
        # Łączymy wyniki z terminarzem, aby wiedzieć kto grał
        full_results = pd.merge(df_wyniki, df_terminarz, on='ID_Meczu')

        for _, row in full_results.iterrows():
            gosp, gosc = row['Druzyna100'], row['Druzyna2']
            sG, sC = int(row['Sety_druzyna1']), int(row['Sety_druzyna2'])
            
            # Punktacja siatkarska (3:0, 3:1 -> 3pkt; 3:2 -> 2pkt; 2:3 -> 1pkt)
            pG, pC = 0, 0
            if sG == 2 and sC < 1: pG, pC = 3, 0
            elif sG == 2 and sC == 1: pG, pC = 2, 1
            elif sC == 2 and sG < 1: pG, pC = 0, 3
            elif sC == 2 and sG == 1: pG, pC = 1, 2

            for team, p, sw, sp in [(gosp, pG, sG, sC), (gosc, pC, sC, sG)]:
                if team in stats:
                    stats[team]['Mecze'] += 1
                    stats[team]['Punkty'] += p
                    stats[team]['Sety_W'] += sw
                    stats[team]['Sety_P'] += sp

        standings = pd.DataFrame.from_dict(stats, orient='index').reset_index()
        standings.columns = ['Drużyna', 'M', 'Pkt', 'Sety +', 'Sety -']
        return standings.sort_values(by=['Pkt', 'Sety +'], ascending=False)

    # --- RENDEROWANIE STRON ---
    if page == "Tabela Główna":
        st.header("🏆 Aktualna Tabela Ligowa")
        tabela = calculate_standings(df_wyniki, df_druzyny)
        st.table(tabela.reset_index(drop=True))

    elif page == "Terminarz":
        st.header("📅 Nadchodzące Mecze")
        # Filtrujemy tylko mecze bez wyników
        mecze_id = df_wyniki['ID_Meczu'].tolist()
        terminarz_view = df_terminarz[~df_terminarz['ID_Meczu'].isin(mecze_id)]
        st.dataframe(terminarz_view, use_container_width=True)

    elif page == "Wyniki":
        st.header("🔢 Ostatnie Wyniki")
        wyniki_view = pd.merge(df_wyniki, df_terminarz[['ID_Meczu', 'Druzyna12', 'Druzyna22', 'Data_kolejki','Godzina_meczu']], on='ID_Meczu')
        st.dataframe(wyniki_view[['Data_kolejki','Godzina_meczu', 'Druzyna1', 'Druzyna2', 'Sety_druzyna1', 'Sety_druzyna2']], use_container_width=True)

    elif page == "Drużyny i Składy":
        st.header("👥 Drużyny")
        wybrana_druzyna = st.selectbox("Wybierz drużynę, aby zobaczyć skład:", df_druzyny['Nazwa_druzyny'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Informacje")
            st.write(df_druzyny[df_druzyny['Nazwa_druzyny'] == wybrana_druzyna])
        with col2:
            st.subheader("Skład")
            sklad = df_sklady[df_sklady['Nazwa_druzyny'] == wybrana_druzyna]
            st.write(sklad[['Nr_zawodnika', 'Imie_zawodnika','Nazwisko_zawodnika']])

except Exception as e:
    st.error(f"Błąd ładowania pliku: {e}")
    st.info("Upewnij się, że plik 'liga_siatkowki.xlsx' znajduje się w tym samym folderze co skrypt i ma poprawne nazwy zakładek.")