import talib
import pandas as pd
from datetime import datetime, timedelta
from binance.exceptions import BinanceAPIException

def fetch_candles_to_df(symbol, interval, lookback, client):
    """Recoge las velas de los últimos 'lookback' días en intervalos especificados y las almacena en un DataFrame."""
    
    while True:
        try:
            # Obtiene la última vela
            candles = client.get_klines(symbol=symbol, interval=interval, limit=60)
            break
        except BinanceAPIException as e:
            print(f"Error al actualizar las velas: {e}")
    
    # Convierte las velas a DataFrame
    df = pd.DataFrame(candles, columns=['open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'close_time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)
    
    # Convierte las columnas a numérico
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
	# Crear un índice temporal único (time_idx)
    df['time_idx'] = range(len(df))
    df['series_id'] = 'default_series'
    
    # Calcula el Simple Moving Average (SMA) de los precios de cierre
    df['SMA_10'] = talib.SMA(df['Close'], timeperiod=2)  # SMA de 10 periodos

    # 1. EMA de periodos cortos:
    df['EMA_3'] = talib.EMA(df['Close'], timeperiod=2)
    df['EMA_5'] = talib.EMA(df['Close'], timeperiod=5)

    # Calcula el Relative Strength Index (RSI)
    df['RSI'] = talib.RSI(df['Close'], timeperiod=2)

    # Calcula el MACD
    df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['Close'], fastperiod=3, slowperiod=5, signalperiod=1)

    # Calcula el Average True Range (ATR)
    df['ATR'] = talib.ATR(df['High'], df['Low'], df['Close'], timeperiod=2)

    # Calcula el On Balance Volume (OBV)
    df['OBV'] = talib.OBV(df['Close'], df['Volume'])

    # Patrones de velas japonesas
    df['DOJI'] = talib.CDLDOJI(df['Open'], df['High'], df['Low'], df['Close'])
    df['HAMMER'] = talib.CDLHAMMER(df['Open'], df['High'], df['Low'], df['Close'])
    df['INV_HAMMER'] = talib.CDLINVERTEDHAMMER(df['Open'], df['High'], df['Low'], df['Close'])
    df['SHOOTING_STAR'] = talib.CDLSHOOTINGSTAR(df['Open'], df['High'], df['Low'], df['Close'])
    df['HANG_MAN'] = talib.CDLHANGINGMAN(df['Open'], df['High'], df['Low'], df['Close'])
    df['ENGULFING'] = talib.CDLENGULFING(df['Open'], df['High'], df['Low'], df['Close'])

    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['Close'], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)

    # Eliminar filas donde todos los valores son NaN
    df.dropna(inplace=True)
    
    return df


def update_candles_df(df, symbol, interval, client):
    """Actualiza el DataFrame con la última vela cerrada."""
    while True:
        try:
            # Obtiene la última vela
            candles = client.get_klines(symbol=symbol, interval=interval, limit=60)
            break
        except BinanceAPIException as e:
            print(f"Error al actualizar las velas: {e}")
    
    # Convierte las velas a DataFrame
    df = pd.DataFrame(candles, columns=['open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'close_time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)
    
    # Convierte las columnas a numérico
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
	# Crear un índice temporal único (time_idx)
    df['time_idx'] = range(len(df))
    df['series_id'] = 'default_series'
    
    # Calcula el Simple Moving Average (SMA) de los precios de cierre
    df['SMA_10'] = talib.SMA(df['Close'], timeperiod=2)  # SMA de 10 periodos

    # 1. EMA de periodos cortos:
    df['EMA_3'] = talib.EMA(df['Close'], timeperiod=2)
    df['EMA_5'] = talib.EMA(df['Close'], timeperiod=5)

    # Calcula el Relative Strength Index (RSI)
    df['RSI'] = talib.RSI(df['Close'], timeperiod=2)

    # Calcula el MACD
    df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['Close'], fastperiod=3, slowperiod=5, signalperiod=1)

    # Calcula el Average True Range (ATR)
    df['ATR'] = talib.ATR(df['High'], df['Low'], df['Close'], timeperiod=2)

    # Calcula el On Balance Volume (OBV)
    df['OBV'] = talib.OBV(df['Close'], df['Volume'])

    # Patrones de velas japonesas
    df['DOJI'] = talib.CDLDOJI(df['Open'], df['High'], df['Low'], df['Close'])
    df['HAMMER'] = talib.CDLHAMMER(df['Open'], df['High'], df['Low'], df['Close'])
    df['INV_HAMMER'] = talib.CDLINVERTEDHAMMER(df['Open'], df['High'], df['Low'], df['Close'])
    df['SHOOTING_STAR'] = talib.CDLSHOOTINGSTAR(df['Open'], df['High'], df['Low'], df['Close'])
    df['HANG_MAN'] = talib.CDLHANGINGMAN(df['Open'], df['High'], df['Low'], df['Close'])
    df['ENGULFING'] = talib.CDLENGULFING(df['Open'], df['High'], df['Low'], df['Close'])

    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['Close'], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
        
    return df