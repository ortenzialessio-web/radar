import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 1. Configurazione della pagina (Interfaccia Wide + Adattamento Mobile)
st.set_page_config(
    page_title="Radar Macro Dashboard", 
    page_icon="📈", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. Ottimizzazione CSS per Mobile Android (compattamento elementi e reattività)
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    .stTabs [data-baseweb='tab-list'] { gap: 4px; }
    div[data-testid="stMetric"] {
        background-color: rgba(28, 131, 225, 0.05);
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid #1c83e1;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 Radar Scenari Macroeconomici")
st.caption("Dashboard Visiva Avanzata con dati storici e live estratti da Yahoo Finance (Ambiente Python 3.11).")

# 3. Definizione completa dei 10 Portafogli dal foglio originale
PORTFOLIOS = {
    "GOLDILOCKS": ["QQQ", "XLK", "XLY", "IEF", "SMH"],
    "RECESSION": ["TLT", "SHY", "XLU", "XLP", "GLD"],
    "STAGFLATION": ["GLD", "DBC", "XLE", "TIP", "XLU"],
    "REFLATION": ["XLI", "XLF", "IWM", "EEM", "DBC"],
    "SOCIETÀ DEBITRICI": ["QQQ", "XLK", "XLY", "IWM", "ARKK"],
    "CASH PREFERENZIALE": ["SHY", "BIL", "IEI", "AGG", "LQD"],
    "HARD ASSETS": ["GLD", "SLV", "DBB", "USO", "UNG"],
    "SOCIETÀ PRODUTTRICI": ["XLI", "XLB", "XLE", "XLV", "XLP"],
    "DEBASEMENT (CON BTC)": ["GLD", "SLV", "IBIT", "QQQ", "XLK"],
    "DEBASEMENT (SENZA BTC)": ["GLD", "SLV", "QQQ", "XLK", "IWM"]
}

# 4. Funzione di caricamento dati robusta con caching integrato
@st.cache_data(show_spinner=False)
def fetch_financial_data(all_tickers):
    data_dict = {}
    today = datetime.today()
    start_date = (today - timedelta(days=400)).strftime('%Y-%m-%d')
    
    for ticker in all_tickers:
        try:
            t_obj = yf.Ticker(ticker)
            hist = t_obj.history(start=start_date)
            
            if hist.empty or len(hist) < 2:
                continue
                
            current_price = hist['Close'].iloc[-1]
            price_1g = hist['Close'].iloc[-2]
            price_1m = hist['Close'].iloc[-22] if len(hist) >= 22 else hist['Close'].iloc[0]
            
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
        except Exception:
            continue
    return data_dict

# Estrazione atomica di tutti i ticker unici per velocizzare le chiamate alle API
all_tickers = list(set([t for p in PORTFOLIOS.values() for t in p]))

# Pulsante di aggiornamento ad alta visibilità (Larghezza adattiva)
if st.button("🔄 Aggiorna Ora i Dati", use_container_width=True, type="primary"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("Scaricamento metriche e analisi trend macro..."):
    data = fetch_financial_data(all_tickers)

# Elaborazione preliminare delle medie per popolare grafici e riepiloghi
summary_rows = []
for name, tickers in PORTFOLIOS.items():
    rows = [data[t.upper()] for t in tickers if t.upper() in data]
    if rows:
        df_temp = pd.DataFrame(rows)
        summary_rows.append({
            "PORTAFOGLIO": name,
            "1G %": df_temp["1G %"].mean(),
            "1M %": df_temp["1M %"].mean(),
            "YTD %": df_temp["YTD %"].mean(),
            "1AN %": df_temp["1AN %"].mean()
        })

df_summary = pd.DataFrame(summary_rows) if summary_rows else pd.DataFrame()

# 5. Generazione dei Tab (Opzione A con layout a schede)
tab_names = ["📋 COMPARA SCENARI"] + list(PORTFOLIOS.keys())
tabs = st.tabs(tab_names)

# --- TAB 0: DASHBOARD VISIVA GENERALE ---
with tabs[0]:
    st.subheader("📊 Performance Comparate dei 10 Scenari")
    
    if not df_summary.empty:
        # GRAFICO INTERATTIVO: Confronto Rendimenti da inizio anno (YTD)
        # Ottimo su Android perché permette di fare pan/zoom col dito
        st.markdown("**Focus Rendimento da inizio anno (YTD %):**")
        
        # Prepariamo i dati per il grafico nativo Streamlit
        chart_data = df_summary.set_index("PORTAFOGLIO")[["YTD %"]]
        st.bar_chart(chart_data, use_container_width=True)
        
        # TABELLA DI RIEPILOGO COMPLETA
        st.markdown("**Matrice delle Performance Medie:**")
        st.dataframe(
            df_summary.style.format({
                "1G %": "{:+.2f}%", "1M %": "{:+.2f}%", 
                "YTD %": "{:+.2f}%", "1AN %": "{:+.2f}%"
            }).map(
                lambda v: "color: #2ecc71; font-weight: bold;" if v > 0 else "color: #e74c3c; font-weight: bold;" if v < 0 else "", 
                subset=["1G %", "1M %", "YTD %", "1AN %"]
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error("Nessun dato caricato. Controlla la connessione a Yahoo Finance.")

# --- TAB 1-10: DETTAGLIO SINGOLI PORTAFOGLI ---
for idx, (name, tickers) in enumerate(PORTFOLIOS.items(), start=1):
    with tabs[idx]:
        rows = [data[t.upper()] for t in tickers if t.upper() in data]
        
        if rows:
            df = pd.DataFrame(rows)
            
            # Calcolo delle medie del paniere corrente
            m_1g = df["1G %"].mean()
            m_1m = df["1M %"].mean()
            m_ytd = df["YTD %"].mean()
            m_1an = df["1AN %"].mean()
            
            # SEZIONE KPI CARDS (Stile Dashboard Finanziaria)
            # Su Android si impilano automaticamente in modo ordinato
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(label="Media Giornaliera (1G)", value=f"{m_1g:+.2f}%")
            col2.metric(label="Media Mensile (1M)", value=f"{m_1m:+.2f}%")
            col3.metric(label="Inizio Anno (YTD)", value=f"{m_ytd:+.2f}%")
            col4.metric(label="Un Anno (1AN)", value=f"{m_1an:+.2f}%")
            
            st.markdown("---")
            st.markdown("**Composizione e Dettaglio Asset:**")
            
            # Costruzione e inserimento della riga finale "MEDIA PORTAFOGLIO"
            media_row = {
                "Ticker": "MEDIA PORTAFOGLIO", "Prezzo": None,
                "1G %": m_1g, "1M %": m_1m, "YTD %": m_ytd, "1AN %": m_1an
            }
            df = pd.concat([df, pd.DataFrame([media_row])], ignore_index=True)
            
            # Renderizzazione tabella di dettaglio del portafoglio
            st.dataframe(
                df.style.format({
                    "Prezzo": lambda x: f"{x:.2f} $" if pd.notnull(x) else "-",
                    "1G %": "{:+.2f}%", "1M %": "{:+.2f}%", 
                    "YTD %": "{:+.2f}%", "1AN %": "{:+.2f}%"
                }).map(
                    lambda v: "color: #2ecc71; font-weight: bold;" if v > 0 else "color: #e74c3c; font-weight: bold;" if v < 0 else "", 
                    subset=["1G %", "1M %", "YTD %", "1AN %"]
                ), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning(f"I ticker del paniere {name} non hanno restituito dati validi.")

st.info("💡 **Consiglio Pro per Android:** Per rimuovere la barra dell'indirizzo del browser e usarlo a schermo intero come un'app nativa, clicca sui tre puntini di Chrome e seleziona 'Aggiungi a schermata Home'.")
