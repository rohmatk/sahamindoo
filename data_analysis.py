import pandas as pd
import os
import glob

investor_mapping = {
    'ID': 'Individual',
    'CP': 'Corporate (Perusahaan)',
    'MF': 'Mutual Fund (Reksa Dana)',
    'IB': 'Financial Institution (Lembaga Keuangan)',
    'IS': 'Insurance (Asuransi)',
    'SC': 'Securities Company (Perusahaan Efek)',
    'PF': 'Pension Fund (Dana Pensiun)',
    'FD': 'Foundation (Yayasan)',
    'OT': 'Others (Lainnya)'
}

local_cols = ['Local IS','Local CP','Local PF','Local IB','Local ID','Local MF','Local SC','Local FD','Local OT']
foreign_cols = ['Foreign IS','Foreign CP','Foreign PF','Foreign IB','Foreign ID','Foreign MF','Foreign SC','Foreign FD','Foreign OT']

def proses_data_ksei(folder='data/'):
    files = glob.glob(os.path.join(folder, '*.txt'))
    if not files:
        return None, None, None, None

    df_list = []
    for f in files:
        try:
            temp_df = pd.read_csv(f, sep='|')
            temp_df['Bulan'] = pd.to_datetime(temp_df['Date'], dayfirst=True, errors='coerce').dt.to_period('M').astype(str)
            df_list.append(temp_df)
        except:
            continue

    df = pd.concat(df_list, ignore_index=True)
    df['Total Lokal'] = df[local_cols].sum(axis=1)
    df['Total Asing'] = df[foreign_cols].sum(axis=1)

    return df, investor_mapping, local_cols, foreign_cols