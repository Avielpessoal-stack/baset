import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# Configuração da página
st.set_page_config(
    page_title="Análise Agrometeorológica - Upload Excel",
    page_icon="🌱",
    layout="wide"
)

# Título principal
st.title("🌱 Análise Agrometeorológica - Abobrinha Italiana")
st.markdown("### Upload de Planilha Excel para Estimativa Automática da Temperatura Basal (Tb)")

# Funções auxiliares
def detectar_colunas_automaticamente(df):
    """Detecta automaticamente as colunas de temperatura e número de folhas"""
    colunas = df.columns.tolist()

    # Detectar colunas de temperatura
    tmin_cols = [col for col in colunas if any(termo in col.lower() for termo in ['tmin', 't min', 'temp min', 'temperatura min'])]
    tmax_cols = [col for col in colunas if any(termo in col.lower() for termo in ['tmax', 't max', 'temp max', 'temperatura max'])]

    # Detectar coluna de número de folhas
    nf_cols = [col for col in colunas if any(termo in col.lower() for termo in ['nf', 'folhas', 'numero', 'número', 'leaves'])]

    return {
        'tmin': tmin_cols[0] if tmin_cols else None,
        'tmax': tmax_cols[0] if tmax_cols else None,
        'nf': nf_cols[0] if nf_cols else None,
        'todas_colunas': colunas
    }

def calcular_tmed(tmin, tmax):
    """Calcula temperatura média"""
    return (tmin + tmax) / 2

def calcular_std(tmed, tb):
    """Calcula soma térmica diária (STd)"""
    return np.maximum(tmed - tb, 0)

def calcular_sta(std):
    """Calcula soma térmica acumulada (STa)"""
    return np.cumsum(std)

def realizar_regressao(x, y, inicio_emergencia=0):
    """Realiza regressão linear e retorna coeficientes e R²"""
    if len(x) <= inicio_emergencia:
        return None, None, 0, None, None

    x_reg = x[inicio_emergencia:].reshape(-1, 1)
    y_reg = y[inicio_emergencia:]

    # Remove valores NaN
    mask = ~(np.isnan(x_reg.flatten()) | np.isnan(y_reg))
    if np.sum(mask) < 2:
        return None, None, 0, None, None

    x_reg_clean = x_reg[mask].reshape(-1, 1)
    y_reg_clean = y_reg[mask]

    reg = LinearRegression().fit(x_reg_clean, y_reg_clean)
    y_pred = reg.predict(x_reg_clean)
    r2 = r2_score(y_reg_clean, y_pred)

    return reg.coef_[0], reg.intercept_, r2, x_reg_clean.flatten(), y_pred

def estimar_tb_otimo(df, tb_range, col_tmin, col_tmax, col_nf, inicio_emergencia=0):
    """Estima a Tb ótima baseada no maior R²"""
    resultados = []

    for tb in tb_range:
        try:
            # Calcular Tmed, STd e STa
            tmed = calcular_tmed(
                pd.to_numeric(df[col_tmin], errors='coerce'), 
                pd.to_numeric(df[col_tmax], errors='coerce')
            )
            std = calcular_std(tmed, tb)
            sta = calcular_sta(std)

            # Realizar regressão
            nf_values = pd.to_numeric(df[col_nf], errors='coerce').values
            coef, intercept, r2, x_reg, y_pred = realizar_regressao(sta, nf_values, inicio_emergencia)

            resultados.append({
                'Tb': tb,
                'R²': r2 if r2 is not None else 0,
                'Coeficiente_Angular': coef if coef is not None else 0,
                'Intercepto': intercept if intercept is not None else 0
            })
        except Exception as e:
            resultados.append({
                'Tb': tb,
                'R²': 0,
                'Coeficiente_Angular': 0,
                'Intercepto': 0
            })

    return pd.DataFrame(resultados)

def gerar_analise_ia(tb_otimo, r2_otimo, coef_angular, intercepto):
    """Gera análise automática com IA integrada"""
    analise = f"""
    ## 🤖 Análise Automática com IA

    ### 📊 Resultados Principais:
    - **Temperatura Basal Ótima:** {tb_otimo}°C
    - **Coeficiente de Determinação (R²):** {r2_otimo:.4f}
    - **Coeficiente Angular:** {coef_angular:.6f}
    - **Intercepto:** {intercepto:.4f}

    ### 🧠 Interpretação IA:
    """

    # Análise do R²
    if r2_otimo >= 0.9:
        analise += "✅ **Excelente ajuste**: O modelo explica mais de 90% da variação no número de folhas."
    elif r2_otimo >= 0.8:
        analise += "✅ **Bom ajuste**: O modelo explica mais de 80% da variação no número de folhas."
    elif r2_otimo >= 0.7:
        analise += "⚠️ **Ajuste moderado**: O modelo explica mais de 70% da variação, mas pode haver outros fatores influenciando."
    else:
        analise += "❌ **Ajuste fraco**: R² baixo indica que outros fatores além da temperatura podem estar influenciando significativamente o desenvolvimento."

    # Análise da Tb
    if tb_otimo < 8:
        analise += f"\n\n🌡️ **Tb baixa ({tb_otimo}°C)**: Indica que a abobrinha italiana pode se desenvolver mesmo em temperaturas mais baixas."
    elif tb_otimo <= 12:
        analise += f"\n\n🌡️ **Tb moderada ({tb_otimo}°C)**: Valor típico para abobrinha italiana, indicando desenvolvimento normal."
    else:
        analise += f"\n\n🌡️ **Tb alta ({tb_otimo}°C)**: Pode indicar uma cultivar que necessita de temperaturas mais elevadas para desenvolvimento."

    # Análise do coeficiente angular
    if coef_angular > 0.01:
        analise += f"\n\n📈 **Desenvolvimento rápido**: Coeficiente angular alto ({coef_angular:.6f}) indica rápida emissão de folhas com o acúmulo térmico."
    elif coef_angular > 0.005:
        analise += f"\n\n📈 **Desenvolvimento moderado**: Coeficiente angular moderado ({coef_angular:.6f}) indica desenvolvimento normal."
    else:
        analise += f"\n\n📈 **Desenvolvimento lento**: Coeficiente angular baixo ({coef_angular:.6f}) pode indicar desenvolvimento mais lento ou outros fatores limitantes."

    return analise

# Interface principal
def main():
    # Sidebar para upload
    st.sidebar.header("📁 Upload da Planilha")

    uploaded_file = st.sidebar.file_uploader(
        "Faça upload da planilha Excel (.xlsx)",
        type=['xlsx', 'xls'],
        help="Planilha deve conter colunas de Tmin, Tmax e Número de Folhas"
    )

    if uploaded_file is not None:
        try:
            # Ler arquivo Excel
            with st.spinner("Carregando planilha..."):
                # Tentar ler todas as abas
                excel_file = pd.ExcelFile(uploaded_file)
                sheet_names = excel_file.sheet_names

                st.sidebar.subheader("📊 Seleção de Aba")
                selected_sheet = st.sidebar.selectbox("Selecione a aba:", sheet_names)

                # Ler aba selecionada
                df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

                # Detectar automaticamente as colunas
                colunas_detectadas = detectar_colunas_automaticamente(df)

                st.success(f"✅ Planilha carregada! Aba: {selected_sheet}")
                st.info(f"📋 Dados: {len(df)} linhas x {len(df.columns)} colunas")

                # Mostrar preview dos dados
                st.subheader("👀 Preview dos Dados")
                st.dataframe(df.head(10))

                # Configuração das colunas
                st.sidebar.subheader("🔧 Configuração das Colunas")

                # Seleção manual ou automática
                usar_deteccao_auto = st.sidebar.checkbox(
                    "Usar detecção automática", 
                    value=True,
                    help="O app tentará detectar automaticamente as colunas de temperatura e folhas"
                )

                if usar_deteccao_auto and all(colunas_detectadas[k] for k in ['tmin', 'tmax', 'nf']):
                    col_tmin = colunas_detectadas['tmin']
                    col_tmax = colunas_detectadas['tmax']
                    col_nf = colunas_detectadas['nf']

                    st.sidebar.success("✅ Colunas detectadas automaticamente:")
                    st.sidebar.write(f"• Tmin: {col_tmin}")
                    st.sidebar.write(f"• Tmax: {col_tmax}")
                    st.sidebar.write(f"• NF: {col_nf}")
                else:
                    st.sidebar.warning("⚠️ Seleção manual necessária")
                    colunas = df.columns.tolist()
                    col_tmin = st.sidebar.selectbox("Coluna Temperatura Mínima:", colunas)
                    col_tmax = st.sidebar.selectbox("Coluna Temperatura Máxima:", colunas)
                    col_nf = st.sidebar.selectbox("Coluna Número de Folhas:", colunas)

                # Parâmetros da análise
                st.sidebar.subheader("🔬 Parâmetros da Análise")

                tb_min = st.sidebar.number_input("Tb Mínima (°C):", value=5.0, step=0.5)
                tb_max = st.sidebar.number_input("Tb Máxima (°C):", value=15.0, step=0.5)
                tb_step = st.sidebar.number_input("Passo Tb (°C):", value=0.5, step=0.1)

                inicio_emergencia = st.sidebar.number_input(
                    "Linha de início (emergência):", 
                    value=0, 
                    min_value=0, 
                    max_value=len(df)-1,
                    step=1
                )

                # Botão para executar análise
                if st.sidebar.button("🚀 Executar Análise Automática", type="primary"):
                    with st.spinner("🤖 Executando análise com IA integrada..."):
                        try:
                            # Gerar range de Tb
                            tb_range = np.arange(tb_min, tb_max + tb_step, tb_step)

                            # Estimar Tb ótimo
                            resultados = estimar_tb_otimo(
                                df, tb_range, col_tmin, col_tmax, col_nf, inicio_emergencia
                            )

                            # Encontrar Tb ótimo
                            tb_otimo_idx = resultados['R²'].idxmax()
                            tb_otimo = resultados.loc[tb_otimo_idx, 'Tb']
                            r2_otimo = resultados.loc[tb_otimo_idx, 'R²']
                            coef_otimo = resultados.loc[tb_otimo_idx, 'Coeficiente_Angular']
                            intercept_otimo = resultados.loc[tb_otimo_idx, 'Intercepto']

                            # Salvar resultados na sessão
                            st.session_state.resultados = resultados
                            st.session_state.tb_otimo = tb_otimo
                            st.session_state.r2_otimo = r2_otimo
                            st.session_state.coef_otimo = coef_otimo
                            st.session_state.intercept_otimo = intercept_otimo
                            st.session_state.df_analise = df
                            st.session_state.colunas_selecionadas = {
                                'tmin': col_tmin, 'tmax': col_tmax, 'nf': col_nf
                            }
                            st.session_state.inicio_emergencia = inicio_emergencia

                            st.success(f"🎉 Análise concluída! Tb ótimo: {tb_otimo}°C (R² = {r2_otimo:.4f})")

                        except Exception as e:
                            st.error(f"❌ Erro na análise: {str(e)}")
                            st.error("Verifique se as colunas selecionadas contêm dados numéricos válidos.")

                # Mostrar resultados se existirem
                if 'resultados' in st.session_state:
                    mostrar_resultados()

        except Exception as e:
            st.error(f"❌ Erro ao carregar planilha: {str(e)}")
            st.error("Verifique se o arquivo é um Excel válido (.xlsx ou .xls)")

    else:
        # Instruções quando não há arquivo
        st.markdown("""
        ## 📋 Como usar este app:

        ### 1. **Prepare sua planilha Excel**
        - Formato: `.xlsx` ou `.xls`
        - Deve conter colunas com:
          - **Temperatura Mínima** (Tmin)
          - **Temperatura Máxima** (Tmax)
          - **Número de Folhas** observado (NF)

        ### 2. **Faça upload**
        - Use o botão na barra lateral
        - Selecione a aba desejada
        - Configure os parâmetros

        ### 3. **Análise automática**
        - O app detecta automaticamente as colunas
        - Calcula a Tb ótima para múltiplas épocas/cultivares
        - Gera gráficos de dispersão
        - Fornece análise com IA integrada

        ### 4. **Metodologia**
        - **Temperatura Média**: Tmed = (Tmin + Tmax) / 2
        - **Soma Térmica Diária**: STd = max(Tmed - Tb, 0)
        - **Soma Térmica Acumulada**: STa = Σ STd
        - **Regressão Linear**: NF = a × STa + b
        - **Seleção Tb Ótima**: Tb com maior R²

        ### 5. **Recursos**
        ✅ **Upload direto de Excel**  
        ✅ **Detecção automática de colunas**  
        ✅ **Análise com IA integrada**  
        ✅ **Gráficos interativos**  
        ✅ **Download dos resultados**  
        ✅ **Múltiplas épocas/cultivares**
        """)

def mostrar_resultados():
    """Mostra os resultados da análise"""
    resultados = st.session_state.resultados
    tb_otimo = st.session_state.tb_otimo
    r2_otimo = st.session_state.r2_otimo
    coef_otimo = st.session_state.coef_otimo
    intercept_otimo = st.session_state.intercept_otimo
    df = st.session_state.df_analise
    colunas = st.session_state.colunas_selecionadas
    inicio_emergencia = st.session_state.inicio_emergencia

    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🌡️ Tb Ótimo", f"{tb_otimo}°C")
    with col2:
        st.metric("📊 R² Máximo", f"{r2_otimo:.4f}")
    with col3:
        st.metric("📈 Coef. Angular", f"{coef_otimo:.6f}")
    with col4:
        st.metric("📍 Intercepto", f"{intercept_otimo:.4f}")

    # Análise com IA
    analise_ia = gerar_analise_ia(tb_otimo, r2_otimo, coef_otimo, intercept_otimo)
    st.markdown(analise_ia)

    # Gráfico R² vs Tb
    st.subheader("📈 Gráfico: R² vs Temperatura Basal")
    fig1 = px.line(
        resultados, 
        x='Tb', 
        y='R²',
        title='Variação do R² em função da Temperatura Basal',
        labels={'Tb': 'Temperatura Basal (°C)', 'R²': 'Coeficiente de Determinação (R²)'}
    )

    # Destacar ponto ótimo
    fig1.add_scatter(
        x=[tb_otimo], 
        y=[r2_otimo],
        mode='markers',
        marker=dict(size=15, color='red', symbol='star'),
        name=f'Tb Ótimo ({tb_otimo}°C)'
    )

    fig1.update_layout(height=500)
    st.plotly_chart(fig1, use_container_width=True)

    # Análise detalhada para Tb ótimo
    st.subheader(f"🔍 Análise Detalhada - Tb = {tb_otimo}°C")

    # Recalcular para Tb ótimo
    tmed = calcular_tmed(
        pd.to_numeric(df[colunas['tmin']], errors='coerce'), 
        pd.to_numeric(df[colunas['tmax']], errors='coerce')
    )
    std = calcular_std(tmed, tb_otimo)
    sta = calcular_sta(std)
    nf_values = pd.to_numeric(df[colunas['nf']], errors='coerce')

    # Realizar regressão para gráfico de dispersão
    coef, intercept, r2, x_reg, y_pred = realizar_regressao(sta, nf_values, inicio_emergencia)

    # Gráfico de dispersão STa vs NF (como na planilha modelo)
    fig2 = go.Figure()

    # Pontos observados
    mask = ~np.isnan(nf_values)
    fig2.add_trace(go.Scatter(
        x=sta[mask], 
        y=nf_values[mask],
        mode='markers',
        name='Dados Observados',
        marker=dict(size=8, color='blue', opacity=0.7)
    ))

    # Linha de regressão
    if x_reg is not None and y_pred is not None:
        fig2.add_trace(go.Scatter(
            x=x_reg,
            y=y_pred,
            mode='lines',
            name=f'Regressão Linear (R²={r2:.4f})',
            line=dict(color='red', width=3)
        ))

    fig2.update_layout(
        title=f'Gráfico de Dispersão: STa vs Número de Folhas (Tb = {tb_otimo}°C)',
        xaxis_title='Soma Térmica Acumulada (STa)',
        yaxis_title='Número de Folhas (NF)',
        height=500
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Tabela de resultados
    st.subheader("📋 Tabela Completa de Resultados")
    st.dataframe(resultados.round(6))

    # Dados detalhados
    df_detalhado = pd.DataFrame({
        'Dia': range(1, len(df) + 1),
        'Tmin': pd.to_numeric(df[colunas['tmin']], errors='coerce'),
        'Tmax': pd.to_numeric(df[colunas['tmax']], errors='coerce'),
        'Tmed': tmed,
        'STd': std,
        'STa': sta,
        'NF_Observado': nf_values
    })

    st.subheader("📊 Dados Detalhados da Análise")
    st.dataframe(df_detalhado)

    # Downloads
    st.subheader("💾 Download dos Resultados")

    col1, col2 = st.columns(2)

    with col1:
        csv_resultados = resultados.to_csv(index=False)
        st.download_button(
            label="📥 Download Resultados Tb (CSV)",
            data=csv_resultados,
            file_name=f"resultados_tb_analise.csv",
            mime="text/csv"
        )

    with col2:
        csv_detalhado = df_detalhado.to_csv(index=False)
        st.download_button(
            label="📥 Download Dados Detalhados (CSV)",
            data=csv_detalhado,
            file_name=f"dados_detalhados_tb_{tb_otimo}C.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
