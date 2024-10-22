import sys
sys.path.insert(0, './modules/trading_bot')
sys.path.insert(0, './modules/update_df')
sys.path.insert(0, './modules/predictions')
sys.path.insert(0, './modules/utils')

import threading
import pandas as pd
from pytorch_forecasting import TemporalFusionTransformer
from datetime import datetime
import time
import os
import math

from utils import controller_spot, get_modo_operacion, cancel_orders_spot
from trading_bot import TradingBot
from operations_spot import vender_spot_rapido
from datetime import datetime


def main():   
   API_KEY = 'Il7AIrG7k1CaXawPKVMSQAaiWEcYpIOswKzZIuObVPN3oO8JQEatLBHbkSzNk4ER'
   SECRET_KEY = 'cEhGHkIuzgpoWmoiZuYrp8UEdNLb4Oh01pshY0xWOD3yOi0lruycCbdDm4t0Ap4H'

   model_path = "E:\VIDA PROFESIONAL\PROYECTS\marxIA\TrainModels\\marxIA\Transformer_prices\\mejores_versiones_5m\\version_4\checkpoints\epoch=38-step=3900.ckpt"
   modelo_cargado = TemporalFusionTransformer.load_from_checkpoint(model_path)

   nombre_archivo = "results/trial_1.csv"

   bot = TradingBot()
   bot.establecer_cliente(API_KEY, SECRET_KEY, testnet=False)
   ganancia_total = 0
   while datetime.now().hour < 18 and ganancia_total < 0.18:

      # Guarda la hora de inicio
      start_time = time.time()

      # Intenta leer el archivo existente o inicializa un DataFrame vacío si el archivo no existe
      if os.path.exists(nombre_archivo):
         resultados_historicos = pd.read_csv(nombre_archivo)
      else:
         resultados_historicos = pd.DataFrame(columns=['Balance Inicial', 'Balance Final', 'Porcentaje de Cambio', 'Tiempo Ejecucion'])

      bot.inicializar_df_predicciones("BTCUSDT", "5m", 1, modelo_cargado)
      bot.error_cambio = 0
      
      print(bot.balance)
      account_details = bot.client.get_isolated_margin_account()
      print(account_details)
      print(bot.client)
      
      break
       

if __name__ == "__main__":
    main()

