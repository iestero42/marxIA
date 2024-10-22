from torch.utils.data import DataLoader
from pytorch_forecasting import TimeSeriesDataSet
import torch
import pandas as pd
import numpy as np

def predecir_precios(modelo_prediccion, predicciones_list, df):

	# Ajusta estos parámetros según tu configuración específica
	max_encoder_length = 2  # La longitud máxima del encoder
	max_prediction_length = 3  # Las siguientes 3 velas que quieres predecir

	df_clean = df.dropna()

	# Utiliza el último período disponible en `df` para la predicción, basado en la longitud del encoder
	encoder_data = df_clean.iloc[-max_encoder_length:].copy()

	print(encoder_data)

	ds_predicciones = TimeSeriesDataSet(
            encoder_data,
            time_idx="time_idx",
			target="Close",
			group_ids=["series_id"],
			min_encoder_length=1,  # Ajusta según tu caso de uso
			max_encoder_length=2,  # Suponiendo que usas las últimas 60 velas para predecir
			min_prediction_length=1,
			max_prediction_length=1,  # Suponiendo que quieres predecir las siguientes 3 velas
			static_categoricals=[],
			static_reals=[],
			time_varying_known_categoricals=[],
			time_varying_known_reals=["Open", "High", "Low", "Volume", "SMA_10", "EMA_3", "EMA_5", "RSI", "MACD", "ATR", "OBV", 
							  		  "DOJI", "HAMMER", "INV_HAMMER", "SHOOTING_STAR", "HANG_MAN", "ENGULFING", "upper_band", 
							  		  "middle_band", "lower_band"],
			time_varying_unknown_reals=["Close"],
			add_relative_time_idx=True,
			add_target_scales=True,
			add_encoder_length=True,
		)

	# Crea un nuevo TimeSeriesDataSet para los datos de predicción
	prediction_dataset = TimeSeriesDataSet.from_dataset(ds_predicciones, encoder_data, predict=True, stop_randomization=True, min_prediction_length=1, max_prediction_length=1)

	# Crea un DataLoader para el dataset de predicción
	prediction_dataloader = prediction_dataset.to_dataloader(batch_size=1, shuffle=False, num_workers=1)

	modelo_prediccion.eval()

	# Realiza la predicción utilizando el DataLoader
	predicciones = modelo_prediccion.predict(prediction_dataloader)

	# Mueve el tensor a la CPU y conviértelo a un array de NumPy
	predicciones_np = predicciones.cpu().numpy()

	# Convierte el array de NumPy a una lista
	predicciones_list_new = predicciones_np.tolist()

	predicciones_list.insert(0, predicciones_list_new)

	if len(predicciones_list) > 2:
		predicciones_list.pop()

	return predicciones_list
