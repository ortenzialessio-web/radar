import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 1. Configurazione della pagina (Interfaccia Wide + Adattamento Mobile)
st.set_page_config(
    page_title="Macro Radar Premium", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. INIEZIONE CSS: Web Design Premium (Dark Theme, Carte Neon, Tab personalizzati)
st.markdown("""
<style>
    /* Rimozione elementi nativi di disturbo */
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    header {visibility: hidden;}
    
    /* Sfondo globale dell'applicazione (Slate Dark) */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Personalizzazione Titoli */
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        background: linear-gradient(45deg, #1f6feb, #58a6ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
        margin-bottom: 5px !important;
    }
    
    /* Design personalizzato per le schede (Tabs Navigator) */
    .stTabs [data-baseweb='tab-list'] {
        gap: 6px;
        background-color: #161b22;
        padding: 8px;
        border-radius: 12px;
        border: 1px solid #30363d;
    }
    .stTabs [data-baseweb='tab'] {
        height: 40px;
        white-space: nowrap;
        background-color: transparent;
        border-radius: 8px;
        color: #8b949e !important;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb='tab'][aria-selected="true"] {
        background-color: #21262d !important;
        color: #58a6ff !important;
        border: 1px solid #30363d;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
    }

    /* Stile Premium per le Carte Metric (KPI) */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        padding: 18px 15px;
        border-radius: 14px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #1f6feb;
    }
    div[data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
    }

    /* Pulsante Aggiorna customizzato */
    div.stButton > button {
        background: linear-gradient(90deg, #1f6feb 0%, #238636 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 15px rgba(31, 111, 235, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        transform: scale(1.01);
        box-shadow: 0 6px 20px rgba(31, 111, 235, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# Intestazione
st.title("⚡ Radar Macro Premium Dashboard")
st.markdown("<p style='color: #8b949e; margin-top:-10px; margin-bottom:25px;'>Analisi quantitativa stagna e in tempo reale degli scenari macroeconomici.</p>", unsafe_allow_html=True)

# 3. Mappatura Esplicita e Statica dei Nomi Asset (Velocizza l'App ed evita i blocchi API Yahoo)
ETF_NAMES = {
    "QQQ": "Invesco QQQ Trust (Nasdaq 100)",
    "XLK": "Technology Select Sector SPDR Fund",
    "XLY": "Consumer Discretionary Select Sector SPDR",
    "IEF": "iShares 7-10 Year Treasury Bond ETF",
    "SMH": "VanEck Semiconductor ETF",
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "SHY": "iShares 1-3 Year Treasury Bond ETF",
    "XLU": "Utilities Select Sector SPDR Fund",
    "XLP": "Consumer Staples Select Sector SPDR Fund",
    "GLD": "SPDR Gold Shares",
    "DBC": "Invesco DB Commodity Index Tracking Fund",
    "XLE": "Energy Select Sector SPDR Fund",
    "TIP": "iShares TIPS Bond ETF",
    "XLI": "Industrial Select Sector SPDR Fund",
    "XLF": "Financial Select Sector SPDR Fund",
    "IWM": "iShares Russell 2000 ETF",
    "EEM": "iShares MSCI Emerging Markets ETF",
    "SLV": "iShares Silver Trust",
    "DBB": "Invesco DB Base Metals Fund",
    "USO": "United States Oil Fund LP",
    "UNG": "United States Natural Gas Fund LP",
    "XLB": "Materials Select Sector SPDR Fund",
    "XLV": "Health Care Select Sector SPDR Fund",
    "IBIT": "iShares Bitcoin Trust",
    "IB1T.DE": "iShares Bitcoin ETP (XETRA)",
    "VWCE.DE": "Vanguard FTSE All-World UCITS ETF (XETRA)",
    "EGLN": "iShares Physical Gold ETC",
    "SPFS.DE": "SPDR S&P 500 UCITS ETF (XETRA)",
    "WNUC.DE": "Amundi MSCI World Nuclear Energy UCITS ETF",
    "CEBL.DE": "iShares MSCI Eurozone ESG UCITS ETF"
}

# Elenco pulito e statico degli 8 portafogli da monitorare
PURE_PORTFOLIOS = {
    "GOLDILOCKS": ["QQQ", "XLK", "XLY", "IEF", "SMH"],
    "RECESSION": ["TLT", "SHY", "XLU", "XLP", "GLD"],
    "STAGFLATION": ["GLD", "DBC", "XLE", "TIP", "XLU"],
    "REFLATION": ["XLI", "XLF", "IWM", "EEM", "DBC"],
    "HARD ASSETS": ["GLD", "SLV", "DBB", "USO", "UNG"],
    "SOCIETÀ PRODUTTRICI": ["XLI", "XLB", "XLE", "XLV", "XLP"],
    "DEBASEMENT (CON BTC)": ["GLD", "SLV", "IBIT", "QQQ", "XLK"],
    "PORTAFOGLIO KT": ["IB1T.DE", "VWCE.DE", "EGLN", "SPFS.DE", "WNUC.DE", "CEBL.DE"]
}

# 4. Funzione ottimizzata ad altissima stabilità mediante Bulk Download
@st.cache_data(show_spinner=False)
def fetch_financial_data(all_tickers):
    data_dict = {}
    today = datetime.today()
    start_date = (today - timedelta(days=400)).strftime('%Y-%m-%d')
    
    try:
        bulk_data = yf.download(all_tickers, start=start_date, group_by='ticker', auto_adjust=True, progress=False)
        
        for ticker in all_tickers:
            if len(all_tickers) > 1:
                hist = bulk_data[ticker]
            else:
                hist = bulk_data
                
            hist = hist.dropna(subset=['Close'])
            if hist.empty or len(hist) < 2: 
                continue
                
            current_price = float(hist['Close'].iloc[-1])
            price_1g = float(hist['Close'].iloc[-2])
            price_1m = float(hist['Close'].iloc[-22]) if len(hist) >= 22 else float(hist['Close'].iloc[-1])
            
            hist_ytd = hist[hist.index.year == today.year]
            price_ytd = float(hist_ytd['Close'].iloc[-1]) if not hist_ytd.empty else current_price
            price_1an = float(hist['Close'].iloc[-252]) if len(hist) >= 252 else float(hist['Close'].iloc[0])
            
            data_dict[ticker.upper()] = {
                "Ticker": ticker.upper(),
                "Nome Asset": ETF_NAMES.get(ticker.upper(), "ETF Globale / Settoriale"),
                "Prezzo": current_price,
                "1G %": float(((current_price - price_1g) / price_1g) * 100),
                "1M %": float(((current_price - price_1m) / price_1m) * 100),
                "YTD %": float(((current_price - price_ytd) / price_ytd) * 100),
                "1AN %": float(((current_price - price_1an) / price_1an) * 100)
            }
    except Exception as e:
        st.error(f"Errore durante il download collettivo: {e}")
        
    return data_dict

# FUNZIONE GLOBALE PER IL RENDERING (Spostata fuori per evitare errori di indentazione)
def render_portfolio_details(name, portfolio_dataframes):
    if name in portfolio_dataframes:
        df = portfolio_dataframes[name].copy()
        m_1g, m_1m, m_ytd, m_1an = df["1G %"].mean(), df["1M %"].mean(), df["YTD %"].mean(), df["1AN %"].mean()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(label="Δ GIORNALIERA", value=f"{m_1g:+.2f}%", delta=f"{m_1g:+.2f}%" if m_1g != 0 else None)
        c2.metric(label="Δ MENSILE", value=f"{m_1m:+.2f}%", delta=f"{m_1m:+.2f}%" if m_1m != 0 else None)
        c3.metric(label="RENDIMENTO YTD", value=f"{m_ytd:+.2f}%", delta=f"{m_ytd:+.2f}%" if m_ytd != 0 else None)
        c4.metric(label="RENDIMENTO 1 ANNO", value=f"{m_1an:+.2f}%", delta=f"{m_1an:+.2f}%" if m_1an != 0 else None)
        
        st.markdown("<br><p style='font-size:1.1rem; font-weight:600; color:#58a6ff;'>Composizione di Dettaglio Asset</p>", unsafe_allow_html=True)
        
        media_row = {
            "Ticker": "MEDIA PORTAFOGLIO", "Nome Asset": "Media ponderata del paniere corrente", "Prezzo": None,
            "1G %": m_1g, "1M %": m_1m, "YTD %": m_ytd, "1AN %": m_1an
        }
        df = pd.concat([df, pd.DataFrame([media_row])], ignore_index=True)
        
        styled_df = df.style.format({
            "Prezzo": lambda x: f"{x:.2f} $" if pd.notnull(x) else "—",
            "1G %": "{:+.2f}%", "1M %": "{:+.2f}%", "YTD %": "{:+.2f}%", "1AN %": "{:+.2f}%"
        }).map(
            lambda v: "color: #39d353; font-weight: bold;" if v > 0 else "color: #f85149; font-weight: bold;" if v < 0 else "", 
            subset=["1G %", "1M %", "YTD %", "1AN %"]
        )
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Nessun componente di mercato disponibile per questo scenario.")

# Estrazione ticker unici
all_tickers = []
for p in PURE_PORTFOLIOS.values():
    all_tickers.extend(p)
all_tickers = list(set(all_tickers))

# Pulsante Aggiorna
if st.button("🔄 AGGIORNA TERMINALE DI MERCATO", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.write("") 

with st.spinner("Sincronizzazione canali finanziari stabili..."):
    data = fetch_financial_data(all_tickers)

# Calcolo delle metriche aggregate per la schermata di riepilogo
summary_rows = []
portfolio_dataframes = {}

for name, tickers in PURE_PORTFOLIOS.items():
