import pandas as pd
import matplotlib.pyplot as plt

def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
    df.set_index('Timestamp', inplace=True)
    return df


def print_data_summary(df: pd.DataFrame):
    print('--- Data Summary ---')
    print(df.describe())
    print('\nNaN counts:')
    print(df.isna().sum())
    print('\nFirst 5 rows:')
    print(df.head())
    print('\nLast 5 rows:')
    print(df.tail())


def plot_price_volume(df: pd.DataFrame, n: int = 1000, last: bool = False):
    if last:
        df = df.tail(n)
    else:
        df = df.head(n)
    plt.figure(figsize=(14, 6))
    plt.subplot(2, 1, 1)
    plt.plot(df.index[:n], df['Close'][:n], label='Close Price')
    plt.title('Close Price (first {} rows)'.format(n))
    plt.legend()
    plt.subplot(2, 1, 2)
    plt.plot(df.index[:n], df['Volume'][:n], label='Volume', color='orange')
    plt.title('Volume (first {} rows)'.format(n))
    plt.legend()
    plt.tight_layout()
    plt.show()
