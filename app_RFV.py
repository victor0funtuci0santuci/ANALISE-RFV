import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from io import BytesIO

# Configuração da página (deve ser o primeiro comando Streamlit)
st.set_page_config(page_title='RFV', layout='wide', initial_sidebar_state='expanded')

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def recencia_class(x, r, q_dict):
    if x <= q_dict[r][0.25]: return 'A'
    elif x <= q_dict[r][0.50]: return 'B'
    elif x <= q_dict[r][0.75]: return 'C'
    else: return 'D'

def freq_val_class(x, fv, q_dict):
    if x <= q_dict[fv][0.25]: return 'D'
    elif x <= q_dict[fv][0.50]: return 'C'
    elif x <= q_dict[fv][0.75]: return 'B'
    else: return 'A'

def main():
    st.title('Análise RFV - Recência, Frequência e Valor')
    st.markdown('---')
    
    st.sidebar.write("## Suba o arquivo de dados")
    data_file = st.sidebar.file_uploader("Escolha um arquivo CSV ou Excel", type=['csv', 'xlsx'])
    
    if data_file is not None:
        df_compras = pd.read_csv(data_file, parse_dates=['DiaCompra'])
        dia_atual = df_compras['DiaCompra'].max()
        
        st.write(f'### Data mais recente na base: {dia_atual}')
        
        df_recencia = df_compras.groupby('ID_cliente')['DiaCompra'].max().reset_index()
        df_recencia['Recencia'] = (dia_atual - df_recencia['DiaCompra']).dt.days
        df_recencia.drop(columns=['DiaCompra'], inplace=True)
        
        df_frequencia = df_compras.groupby('ID_cliente')['CodigoCompra'].count().reset_index()
        df_frequencia.columns = ['ID_cliente', 'Frequencia']
        
        df_valor = df_compras.groupby('ID_cliente')['ValorTotal'].sum().reset_index()
        df_valor.columns = ['ID_cliente', 'Valor']
        
        df_RFV = df_recencia.merge(df_frequencia, on='ID_cliente').merge(df_valor, on='ID_cliente')
        df_RFV.set_index('ID_cliente', inplace=True)
        
        quartis = df_RFV.quantile(q=[0.25, 0.5, 0.75])
        df_RFV['R_quartil'] = df_RFV['Recencia'].apply(recencia_class, args=('Recencia', quartis))
        df_RFV['F_quartil'] = df_RFV['Frequencia'].apply(freq_val_class, args=('Frequencia', quartis))
        df_RFV['V_quartil'] = df_RFV['Valor'].apply(freq_val_class, args=('Valor', quartis))
        df_RFV['RFV_Score'] = df_RFV.R_quartil + df_RFV.F_quartil + df_RFV.V_quartil
        
        dict_acoes = {
            'AAA': 'Enviar cupons de desconto, pedir indicação de amigos.',
            'DDD': 'Clientes com baixo gasto e baixa frequência, pouca ação necessária.',
            'DAA': 'Clientes de alto valor, enviar cupons para recuperação.',
            'CAA': 'Clientes com compras altas no passado, tentar reengajamento.'
        }
        df_RFV['Ações de Marketing'] = df_RFV['RFV_Score'].map(dict_acoes)
        
        st.write('## Segmentação RFV')
        st.write(df_RFV.head())
        st.write('### Quantidade de clientes por grupo')
        st.write(df_RFV['RFV_Score'].value_counts())
        
        df_xlsx = to_excel(df_RFV)
        st.download_button(label='📥 Baixar Resultados', data=df_xlsx, file_name='RFV_Analise.xlsx')
        
if __name__ == '__main__':
    main()
