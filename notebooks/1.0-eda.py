import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.stattools import adfuller, kpss
from scipy.fft import fft, fftfreq
import os
from faker import Faker

plt.style.use('seaborn-v0_8-darkgrid')
fake = Faker()


columns = ['unit_number', 'time_cycle', 'op_setting_1', 'op_setting_2', 'op_setting_3'] + \
          [f'sensor_meas_{i}' for i in range(1, 22)]


data_path = '../data/raw/CMaps/train_FD001.txt'
if os.path.exists(data_path):
    df = pd.read_csv(data_path, delim_whitespace=True, header=None, names=columns)
else:
    print(f"File {data_path} not found. Creating a dummy dataset for demonstration.")
   
    dummy_data = np.random.randn(1000, 26)
    df = pd.DataFrame(dummy_data, columns=columns)
    df['unit_number'] = np.repeat(np.arange(1, 11), 100)
    df['time_cycle'] = np.tile(np.arange(1, 101), 10)

df.head()


sensor_cols = [col for col in df.columns if 'sensor' in col]
df[sensor_cols].hist(bins=50, figsize=(20, 15))
plt.tight_layout()
plt.show()


plt.figure(figsize=(16, 12))
sns.heatmap(df[sensor_cols].corr(), annot=False, cmap='coolwarm')
plt.title("Sensor Correlation Heatmap")
plt.show()


missing_vals = df.isnull().sum()
print("Missing Values:\n", missing_vals[missing_vals > 0])


unit1 = df[df['unit_number'] == 1]['sensor_meas_2'].values


adf_result = adfuller(unit1)
print(f'ADF Statistic: {adf_result[0]}')
print(f'p-value: {adf_result[1]}')


kpss_result = kpss(unit1, regression='c', nlags='auto')
print(f'\nKPSS Statistic: {kpss_result[0]}')
print(f'p-value: {kpss_result[1]}')


N = len(unit1)
T = 1.0 
yf = fft(unit1)
xf = fftfreq(N, T)[:N//2]

plt.figure(figsize=(10, 4))
plt.plot(xf, 2.0/N * np.abs(yf[0:N//2]))
plt.title("FFT Spectrum of Sensor 2 for Unit 1")
plt.xlabel("Frequency")
plt.ylabel("Amplitude")
plt.show()


def inject_random_walk_anomaly(series, start_idx, length, intensity_multiplier=2.0):
    """Injects a random walk anomaly into a pandas Series."""
    rw = np.cumsum(np.random.randn(length)) * intensity_multiplier
    mocked_series = series.copy()
    mocked_series.iloc[start_idx:start_idx+length] += rw
    return mocked_series

df_anom = df.copy()

unit1_idx = df_anom.index[df_anom['unit_number'] == 1].tolist()
start_anom = unit1_idx[10] 
length_anom = 20

df_anom['sensor_meas_2'] = inject_random_walk_anomaly(df_anom['sensor_meas_2'], start_anom, length_anom, intensity_multiplier=5.0)

plt.figure(figsize=(12, 4))
plt.plot(df['sensor_meas_2'].iloc[unit1_idx], label='Original', alpha=0.7)
plt.plot(df_anom['sensor_meas_2'].iloc[unit1_idx], label='With Anomaly', alpha=0.7, linestyle='--')
plt.title("Sensor 2 with Injected Random Walk Anomaly")
plt.legend()
plt.show()


df_anom['is_anomaly']=0
df_anom.loc[start_anom:start_anom+length_anom-1, 'is_anomaly'] = 1

print("Generated dummy anomaly metadata using Faker:")
for _ in range(3):
    print(f"Engineer: {fake.name()}, Alert ID: {fake.uuid4()}, Status: {fake.word(ext_words=['CRITICAL', 'WARNING'])}")
