import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import plotly.graph_objects as go
from io import StringIO, BytesIO

# --- Page Configuration ---
st.set_page_config(
    page_title="EstimaTB",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Functions ---

def load_data(uploaded_file):
    """Loads data from CSV or Excel, handling potential parsing errors."""
    try:
        if uploaded_file.name.endswith('.csv'):
            # Attempt to read with standard separator, then with comma as decimal
            try:
                return pd.read_csv(uploaded_file)
            except Exception:
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, decimal=',')
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            return pd.read_excel(uploaded_file, engine='openpyxl')
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        st.info("Por favor, verifique se o arquivo é um CSV ou Excel válido e se as colunas estão nos formatos corretos.")
        return None
    return None

def validate_data(df):
    """Validates the dataframe columns and data."""
    required_cols = ['Data', 'Tmin', 'Tmax', 'NF']
    errors = []
    
    # Check for required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Colunas obrigatórias não encontradas no arquivo: {', '.join(missing_cols)}. Por favor, renomeie as colunas para 'Data', 'Tmin', 'Tmax', 'NF'.")
        return df, errors

    # Convert 'Data' to datetime
    try:
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        if df['Data'].isnull().any():
            # If coercion fails, try without dayfirst
            df['Data'] = pd.to_datetime(df['Data'], errors='raise')

    except Exception:
        errors.append("Não foi possível converter a coluna 'Data' para um formato de data. Verifique os valores nesta coluna (ex: DD/MM/AAAA).")

    # Convert numeric columns, coercing errors
    for col in ['Tmin', 'Tmax', 'NF']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Check for Tmin > Tmax
    if (df['Tmin'] > df['Tmax']).any():
        errors.append("Existem linhas onde a 'Tmin' é maior que a 'Tmax'. Por favor, verifique os dados de temperatura.")

    # Check for decrease in NF
    nf_series = df['NF'].dropna().reset_index(drop=True)
    if (nf_series.diff() < 0).any():
       errors.append("Existem linhas onde o 'NF' (Número de Folhas) diminui em relação à medição anterior. Isso pode indicar um erro de digitação.")

    return df, errors


def calculate_tb(df):
    """Calculates the basal temperature by minimizing the MSE."""
    df['Tmed'] = (df['Tmin'] + df['Tmax']) / 2
    
    pheno_df = df.dropna(subset=['NF']).copy()
    
    results = []
    # Define the range of base temperatures to test
    base_temps = np.arange(0, 20.5, 0.5)

    for tb in base_temps:
        # Calculate daily thermal sum (STd)
        df['STd'] = df['Tmed'] - tb
        df.loc[df['STd'] < 0, 'STd'] = 0
        
        # Calculate accumulated thermal sum (STa)
        df['STa'] = df['STd'].cumsum()
        
        # Get the STa for the dates with NF measurements
        sta_for_regression = df.loc[pheno_df.index]['STa']
        
        # Prepare data for regression
        X = sta_for_regression.values.reshape(-1, 1)
        y = pheno_df['NF'].values
        
        # Perform linear regression
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        
        # Calculate metrics
        mse = mean_squared_error(y, y_pred)
        r2 = model.score(X, y)
        
        results.append({'Tb': tb, 'QME': mse, 'R2': r2})

    results_df = pd.DataFrame(results)
    best_tb = results_df.loc[results_df['QME'].idxmin()]
    
    return results_df, best_tb

# --- UI ---

st.title("EstimaTB")
st.markdown("Uma ferramenta para estimar a Temperatura Basal (Tb) de culturas agrícolas através do método do Quadrado Médio do Erro (QME).")

st.markdown("---")

# --- Sidebar for Instructions and Upload ---
with st.sidebar:
    st.header("Instruções")
    st.markdown("""
    1.  **Prepare seu arquivo**: Ele deve ser um arquivo CSV ou Excel.
    2.  **Formate as colunas**: O arquivo deve conter exatamente estas quatro colunas:
        - `Data` (as datas de medição)
        - `Tmin` (temperatura mínima diária)
        - `Tmax` (temperatura máxima diária)
        - `NF` (número de folhas; deixe em branco nos dias sem medição)
    3.  **Faça o upload**: Use o botão abaixo para carregar seu arquivo.
    4.  **Analise os resultados**: A aplicação calculará automaticamente a temperatura basal e exibirá os resultados.
    """)
    uploaded_file = st.file_uploader("Escolha um arquivo (CSV ou Excel)", type=['csv', 'xls', 'xlsx'])


# --- Main Application Logic ---
if uploaded_file is not None:
    data = load_data(uploaded_file)
    
    if data is not None:
        st.success(f"Arquivo '{uploaded_file.name}' carregado com sucesso.")
        validated_data, errors = validate_data(data)

        if errors:
            st.warning("Foram encontrados problemas com os seus dados:")
            for error in errors:
                st.error(f"- {error}")
        else:
            st.info("Os dados foram validados e parecem corretos. Iniciando a análise...")

            with st.spinner("Calculando a Temperatura Basal... Este processo pode levar um momento."):
                results_df, best_tb = calculate_tb(validated_data.copy())

            st.header("Resultados da Análise")
            
            # Display the best Tb
            col1, col2 = st.columns(2)
            col1.metric(
                label="Temperatura Basal Estimada (Tb)",
                value=f"{best_tb['Tb']:.1f} °C"
            )
            col2.metric(
                label="Menor Quadrado Médio do Erro (QME)",
                value=f"{best_tb['QME']:.4f}"
            )

            # Display Plotly chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=results_df['Tb'], 
                y=results_df['QME'],
                mode='lines+markers',
                name='QME',
                marker=dict(color='#1f77b4') # Professional blue
            ))
            # Add a vertical line for the best Tb
            fig.add_vline(
                x=best_tb['Tb'], 
                line_width=2, 
                line_dash="dash", 
                line_color="#d62728" # Professional red
            )
            fig.update_layout(
                title="Quadrado Médio do Erro (QME) vs. Temperatura Basal (Tb)",
                xaxis_title="Temperatura Basal (°C)",
                yaxis_title="Quadrado Médio do Erro (QME)",
                template="plotly_white",
                font=dict(family="sans-serif")
            )
            st.plotly_chart(fig, use_container_width=True)

            # Display results table in an expander
            with st.expander("Ver Tabela de Resultados Detalhados"):
                st.dataframe(results_df.style.format({
                    'Tb': '{:.1f}',
                    'QME': '{:.4f}',
                    'R2': '{:.4f}'
                }))

else:
    st.info("Aguardando o upload de um arquivo de dados para iniciar a análise.")

st.markdown("---")
st.markdown("_Desenvolvido como uma ferramenta de auxílio para pesquisa agrícola._")
