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
   API_KEY = '1nP0Fz78Y7fC0jnJXX7YyPbTUpLsVhbsyCmcfp5kteOLG1rUYIRosTWyacoHqOck'
   SECRET_KEY = 'qTFkaR3MzRgJuXjNA77bcVmqeGrCgRTS17LnOMUa46ecsv7yp7ujPzWYtjILtiOh'

   model_path = "E:\VIDA PROFESIONAL\PROYECTS\marxIA\TrainModels\\marxIA\Transformer_prices\\mejores_versiones_5m\\version_4\checkpoints\epoch=38-step=3900.ckpt"
   modelo_cargado = TemporalFusionTransformer.load_from_checkpoint(model_path)

   nombre_archivo = "results/trial_1.csv"

   bot = TradingBot()
   bot.establecer_cliente(API_KEY, SECRET_KEY, testnet=True)
   ganancia_total = 0
   while datetime.now().hour < 18:

      # Guarda la hora de inicio
      start_time = time.time()

      # Intenta leer el archivo existente o inicializa un DataFrame vacío si el archivo no existe
      if os.path.exists(nombre_archivo):
         resultados_historicos = pd.read_csv(nombre_archivo)
      else:
         resultados_historicos = pd.DataFrame(columns=['Balance Inicial', 'Balance Final', 'Porcentaje de Cambio', 'Tiempo Ejecucion'])

      bot.inicializar_df_predicciones("BTCUSDT", "5m", 1, modelo_cargado)
      bot.inicializar_balance_spot("USDT")
      bot.error_cambio = 0
      
      print(bot.balance)

      cancel_orders_spot(bot.client, "BTCUSDT")
      vender_spot_rapido(bot.client)

      while (controller_spot(bot) != 1):
         current_minute = datetime.now().minute
         current_sec = datetime.now().second
         if current_minute % 5 == 0 and current_sec < 2:  # Si el minuto actual es 00, 15, 30 o 45
               time.sleep(2)
               print(bot.balance)
               bot.actualizar_df_predicciones("BTCUSDT", "5m", modelo_cargado)
               print(bot.list_predicciones)
               bot.operar_spot()

               if bot.id_order_tp > 1:
                  order = bot.client.get_order(
                     symbol='BTCUSDT',
                     orderId=bot.id_order_tp)

                  print(order['status']) 
                  print(order['price'])
                  print(order['stopPrice'])

               if bot.id_order_sell > 1:
                  order = bot.client.get_order(
                     symbol='BTCUSDT',
                     orderId=bot.id_order_sell)

                  print(order['status']) 
                  print(order['price'])

         else:
               time.sleep(1)

      # Calcula y muestra la duración total
      end_time = time.time()
      duration = end_time - start_time

      # Convertir la duración a horas, minutos y segundos
      hours, remainder = divmod(duration, 3600)
      minutes, seconds = divmod(remainder, 60)

      duration = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))

      # Después del bucle, calcula el balance final
      bot.actualizar_balance_spot('USDT')

      # Calcula el porcentaje de cambio
      porcentaje_cambio = ((bot.balance - bot.balance_inicial) / bot.balance_inicial) * 100

      ganancia_total += porcentaje_cambio

      # Crea un DataFrame con los nuevos resultados
      nuevos_resultados = pd.DataFrame({
         'Balance Inicial': [bot.balance_inicial],
         'Balance Final': [bot.balance],
         'Porcentaje de Cambio': [porcentaje_cambio],
         'Tiempo Ejecucion': [duration]
      })

      # Concatena los nuevos resultados con los resultados históricos
      resultados_actualizados = pd.concat([resultados_historicos, nuevos_resultados])

      # Guarda el DataFrame actualizado en el archivo
      resultados_actualizados.to_csv(nombre_archivo, index=False)
      print(f"Resultados actualizados guardados en {nombre_archivo}")
       

if __name__ == "__main__":
    main()

