import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Configurazione della pagina ottimizzata per Mobile Android e Desktop
st.set_page_config(page_title="Radar Scenari Macro", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

# Stile CSS personalizzato
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} .stTabs [data-baseweb='tab-list'] { gap: 8px; }</style>", unsafe_allow_html=True)

st.title("📊 Portafogli Radar Scenari Macro")
st.caption("Esecuzione stabile su ambiente Python 3.11. Dati storici e real-time via Yahoo Finance.")

# Definizione dei portafogli dal foglio originale
PORTFOLIOS = {
    "Goldilocks": ["QQQ", "XLK", "XLY", "IEF", "SMH"],
    "Recession": ["TLT", "SHY", "XLU", "XLP", "GLD"],
    "Stagflation": ["GLD", "DBC", "XLE", "TIP", "XLU"],
    "Reflation": ["XLI", "XLF", "IWM", "EEM", "DBC"]
}

@st.cache_data(show_spinner=False)
def fetch_financial_data(all_tickers):
    data_dict = {}
    today = datetime.today()
    # Scarichiamo 400 giorni per essere sicuri di coprire l'anno storico (circa 252 giorni di borsa aperta)
    start_date = (today - timedelta(days=400)).strftime('%Y-%m-%d')
    
    for ticker in all_tickers:
        try:
            t_obj = yf.Ticker(ticker)
            # Scarica i dati storici in un colpo solo
            hist = t_obj.history(start=start_date)
            
            if hist.empty or len(hist) < 2:
                continue
                
            current_price = hist['Close'].iloc[-1]
            
            # Calcolo dei punti di riferimento storici (gestendo i giorni di chiusura mercato)
            price_1g = hist['Close'].iloc[-2]
            price_1m = hist['Close'].iloc[-22] if len(hist) >= 22 else hist['Close'].iloc[0]
            
            # Ricerca inizio anno (YTD)
            hist_ytd = hist[hist.index.year == today.year]
            price_ytd = hist_ytd['Close'].iloc[0] if not hist_ytd.empty else current_price
            
            price_1an = hist['Close'].iloc[-252] if len(hist) >= 252 else hist['Close'].iloc[0]
            
            data_dict[ticker.upper()] = {
                "Ticker": ticker.upper(),
                "Prezzo": float(current_price),
                "1G %": float(((current_price - price_1g) / price_1g) * 100),
                "1M %": float(((current_price - price_1m) / price_1m) * 100),
                "YTD %": float(((current_price - price_ytd) / price_ytd) * 100),
                "1AN %": float(((current_price - price_1an) / price_1an) * 100)
            }
        except Exception as e:
            continue
    return data_dict

# Estrazione ticker unici
all_tickers = list(set([t for p in PORTFOLIOS.values() for t in p]))

# Interfaccia di controllo: pulsante aggiorna
if st.button("🔄 Aggiorna Ora", use_container_width=True, type="primary"):
    st.cache_data.clear()
    st.status("Dati svuotati! Ricaricamento in corso...").update(state="complete")

with st.spinner("Connessione a Yahoo Finance in corso..."):
    data = fetch_financial_data(all_tickers)

# Renderizzazione ad Opzione A (Schede/Tabs per ottimizzazione smartphone)
tabs = st.tabs(list(PORTFOLIOS.keys()))
for tab, (name, tickers) in zip(tabs, PORTFOLIOS.items()):
    with tab:
        # Estrai solo i dati dei ticker del portafoglio corrente
        rows = [data[t.upper()] for t in tickers if t.upper() in data]
        
        if rows:
            df = pd.DataFrame(rows)
            
            # Calcolo della riga "MEDIA PORTAFOGLIO" come nel foglio Excel
            media_row = {
                "Ticker": "MEDIA PORTAFOGLIO",
                "Prezzo": None,
                "1G %": df["1G %"].mean(),
                "1M %": df["1M %"].mean(),
                "YTD %": df["YTD %"].mean(),
                "1AN %": df["1AN %"].mean()
            }
            
            # Unisci la riga della media alla tabella principale
            df = pd.concat([df, pd.DataFrame([media_row])], ignore_index=True)
            
            # Formattazione condizionale e visualizzazione tabella
            st.dataframe(
                df.style.format({
                    "Prezzo": lambda x: f"{x:.2f} $" if pd.notnull(x) else "-",
                    "1G %": "{:+.2f}%", 
                    "1M %": "{:+.2f}%", 
                    "YTD %": "{:+.2f}%", 
                    "1AN %": "{:+.2f}%"
                }).map(
                    lambda v: "color: #2ecc71; font-weight: bold;" if v > 0 else "color: #e74c3c; font-weight: bold;" if v < 0 else "", 
                    subset=["1G %", "1M %", "YTD %", "1AN %"]
                ), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning("Nessun dato disponibile al momento per questo scenario.")

st.info("💡 **Consiglio Android:** Apri il link dal browser dello smartphone, clicca sui tre puntini in alto a destra e seleziona 'Aggiungi a schermata Home' per usarla a tutto schermo come una vera app nativa.")
