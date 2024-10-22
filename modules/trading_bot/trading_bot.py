from dataclasses import dataclass, field
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from pytorch_forecasting import TimeSeriesDataSet
import os
import time

from update_df import update_candles_df, fetch_candles_to_df
from predecir_precios import predecir_precios
from utils import get_modo_operacion, cancel_orders_spot, cancel_orders_margin
from operations_margin import comprar_margin, vender_margin, set_sl_tp_margin
from operations_spot import comprar_spot, vender_spot, set_sl_tp_spot


@dataclass
class TradingBot:
    df_predicciones: pd.DataFrame = field(default_factory=pd.DataFrame)
    results: pd.DataFrame = field(default_factory=pd.DataFrame)
    ds_predicciones: TimeSeriesDataSet = None
    list_predicciones: list = field(default_factory=list)
    estado: str = 'running'
    modo_operacion: str = 'none'
    historial_operaciones: list = field(default_factory=list)
    balance: float = 0.0
    balance_inicial: float = 0.0
    client: Client = None  # Inicialmente el cliente no está definido
    id_order_tp: int = 0
    id_order_sell: int = 0
    order_id_sl: int = 0
    precio_compra: float = 0.0
    error_real_venta: str = 'positivo'
    error_real_compra: str = 'positivo'
    error_cambio: int = 0

    def establecer_cliente(self, api_key: str, api_secret: str, testnet: bool = False):
        """Establece el cliente de Binance para el bot."""
        if testnet:
            self.client = Client(api_key, api_secret, testnet=True)
            self.client.API_URL = 'https://testnet.binance.vision/api'
            self.client.WSS_URL = 'wss://testnet.binance.vision/ws'
        else:
            self.client = Client(api_key, api_secret)

        
    
    def inicializar_df_predicciones(self, symbol, interval, lookback, modelo_prediccion):
        self.df_predicciones = fetch_candles_to_df(symbol, interval, lookback, self.client)
        self.list_predicciones = predecir_precios(modelo_prediccion, self.list_predicciones, self.df_predicciones)
        

    def inicializar_balance_margin(self, moneda):
        """
        Obtiene el balance libre de un activo específico en una cuenta de margin.
        
        Args:
        client (Client): El cliente de la API de Binance configurado.
        asset (str): El activo del cual quieres obtener el balance libre (ej., 'BTC').
        
        Returns:
        float: El balance libre del activo en la cuenta de margin.
        """
        account_details = self.client.get_isolated_margin_account()
        for balance in account_details['balances']:
            if balance['asset'] == moneda:
                self.balance_inicial = self.balance = float(balance['free'])
    
    def actualizar_balance_margin(self, moneda):
        """
        Obtiene el balance libre de un activo específico en una cuenta de margin.
        
        Args:
        client (Client): El cliente de la API de Binance configurado.
        asset (str): El activo del cual quieres obtener el balance libre (ej., 'BTC').
        
        Returns:
        float: El balance libre del activo en la cuenta de margin.
        """
        account_details = self.client.get_isolated_margin_account()
        for balance in account_details['balances']:
            if balance['asset'] == moneda:
                self.balance = float(balance['free'])

    def inicializar_balance_spot(self, moneda):
        """
        Obtiene el balance libre de un activo específico en una cuenta de margin.
        
        Args:
        client (Client): El cliente de la API de Binance configurado.
        asset (str): El activo del cual quieres obtener el balance libre (ej., 'BTC').
        
        Returns:
        float: El balance libre del activo en la cuenta de margin.
        """
        try:
            account_details = self.client.get_account()
            for balance in account_details['balances']:
                if balance['asset'] == moneda:
                    self.balance_inicial = self.balance = float(balance['free'])
        except BinanceAPIException as e:
            print(f"Error al actualizar el balance: {e}")

    def actualizar_balance_spot(self, moneda):
        """
        Obtiene el balance libre de un activo específico en una cuenta de margin.
        
        Args:
        client (Client): El cliente de la API de Binance configurado.
        asset (str): El activo del cual quieres obtener el balance libre (ej., 'BTC').
        
        Returns:
        float: El balance libre del activo en la cuenta de margin.
        """
        try:
            account_details = self.client.get_account()
            for balance in account_details['balances']:
                if balance['asset'] == moneda:
                    self.balance = float(balance['free'])
        except BinanceAPIException as e:
            print(f"Error al actualizar el balance: {e}")

    def actualizar_df_predicciones(self, symbol, interval, modelo_prediccion):
        self.df_predicciones = update_candles_df(self.df_predicciones, symbol, interval, self.client)

        if os.path.exists("results/error.csv"):
            error_historico = pd.read_csv("results/error.csv")
        else:
            error_historico = pd.DataFrame(columns=['Close Predicho', 'Close Real', 'Rendimiento'])
         # Crea un DataFrame con los nuevos resultados
        nuevos_errores = pd.DataFrame({
            'Close Predicho': [self.list_predicciones[0][0][0]],
            'Close Real': [self.df_predicciones.tail(1)['Close'].iloc[0]],
            'Rendimiento': [((self.list_predicciones[0][0][0] - self.df_predicciones.tail(1)['Close'].iloc[0]) / self.df_predicciones.tail(1)['Close'].iloc[0]) * 100]
        })

        # Concatena los nuevos resultados con los resultados históricos
        error_actualizado = pd.concat([error_historico, nuevos_errores])

        # Guarda el DataFrame actualizado en el archivo
        error_actualizado.to_csv("results/error.csv", index=False)
        
        if ((self.list_predicciones[0][0][0] - self.df_predicciones.tail(1)['Close'].iloc[0]) > 0):
            self.error_cambio -= 1
        else:
            self.error_cambio += 1


        if (self.error_cambio >= 3):
            self.error_real_compra = 'positivo'
        else:
            self.error_real_compra = 'negativo'
        if (self.error_cambio >= 0):
            self.error_real_venta = 'positivo'
        else:
            self.error_real_venta = 'negativo'
        print("Error cambio:", self.error_cambio)

        self.list_predicciones = predecir_precios(modelo_prediccion, self.list_predicciones, self.df_predicciones)

    def operar_margin(self):
        self.modo_operacion = get_modo_operacion(self.df_predicciones.tail(1), self.list_predicciones, self.balance)
        if (self.modo_operacion == 'comprar'):
            cancel_orders_margin(self.client, 'BTCUSDT')
            order = comprar_margin(self.balance, self.client)
            total_qty = sum(float(fill['qty']) for fill in order['fills'])
            total_spent = sum(float(fill['price']) * float(fill['qty']) for fill in order['fills'])
            precio_compra_promedio = total_spent / total_qty if total_qty else 0
            
            print(f"Precio de compra promedio: {precio_compra_promedio}")
            print(f"Precio total gastado: {total_spent}")
            print(f"Precio total comprado: {total_qty}")

            ganancia_objetivo = total_spent * 0.02
            perdida_objetivo = total_spent * 0.01
            posicion_tamaño = total_spent * 20
            ganancia_apal = ganancia_objetivo / posicion_tamaño
            perdida_apal = perdida_objetivo / posicion_tamaño
            
            precio_stop_loss = precio_compra_promedio * (1 - perdida_apal)
            precio_take_profit = precio_compra_promedio * (1 + ganancia_apal)

            print(f"Precio de compra promedio: {precio_compra_promedio}")
            print(f"Precio Stop Loss: {precio_stop_loss}")
            print(f"Precio Take Profit: {precio_take_profit}")

            set_sl_tp_margin(self.client, 'BTCUSDT', total_qty, precio_stop_loss, precio_take_profit)
        elif (self.modo_operacion == 'vender'):
            vender_margin(self.client)

    def operar_spot(self):
        self.actualizar_balance_spot('USDT')
        self.modo_operacion = get_modo_operacion(self.df_predicciones.tail(2), self.list_predicciones, self.balance, self)
        print(self.modo_operacion)
        if (self.modo_operacion == 'comprar'):
            order = comprar_spot(self.balance, self.client)

            if order != None:
                order_status = order['status']
                print(order_status)

                
                # Registra el tiempo cuando comienza el bucle
                start_time = time.time()
                while order_status not in ['FILLED', 'CANCELED', 'EXPIRED'] and time.time() - start_time < 1200:
                    order = self.client.get_order(
                        symbol='BTCUSDT',
                        orderId=order['orderId'])
                    order_status = order['status']
                    
                if order_status == 'FILLED' or order_status == 'PARTIALLY_FILLED':
                    print(order_status)
                    if (order_status == 'PARTIALLY_FILLED'):
                        cancel_orders_spot(self.client, 'BTCUSDT')
                        print("La Orden de compra no se completo")
                        total_qty = float(order['executedQty'])
                    else:
                        print("La Orden de compra se completo")
                        total_qty = float(order['origQty'])
                    self.precio_compra = precio_compra_promedio = float(order['price'])
                    print("Precio de compra promedio: ", precio_compra_promedio)

                    # Define tus porcentajes de stop loss y take profit
                    porcentaje_stop_loss = 0.001  # 1%
                    porcentaje_take_profit = 0.001  # 2%
                    
                    precio_stop_loss = precio_compra_promedio * (1 - porcentaje_stop_loss)
                    precio_take_profit = precio_compra_promedio * (1 + porcentaje_take_profit)

                    set_sl_tp_spot(self.client, 'BTCUSDT', total_qty, precio_stop_loss, precio_take_profit, self)
                elif order_status in ['CANCELED', 'EXPIRED']:
                    print("La orden de compra fue cancelada o expiró.")
                    vender_spot(self.client, self)
                else:
                    cancel_orders_spot(self.client, 'BTCUSDT')

        elif (self.modo_operacion == 'vender'):
            vender_spot(self.client, self)