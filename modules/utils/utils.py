from binance.exceptions import BinanceAPIException
from operations_spot import vender_spot

def controller_spot(bot):
    def check_order_status(bot, order_id):
        if order_id > 1:
            order = bot.client.get_order(
                symbol='BTCUSDT',
                orderId=order_id)

            # El estado de la orden se encuentra en el campo 'status' del diccionario retornado
            order_status = order['status']

            if order_status not in ['FILLED', 'CANCELED', 'EXPIRED']:
                return False
        return True

    try:
        todas_ordenes_completadas = True

        orden_venta = check_order_status(bot, bot.id_order_sell)
        if orden_venta:
            bot.id_order_sell = 0
        orden_take = check_order_status(bot, bot.id_order_tp)
        if orden_take:
            bot.id_order_tp = 0

        todas_ordenes_completadas = orden_venta and orden_take
        
        bot.actualizar_balance_spot("USDT")
        if todas_ordenes_completadas and bot.balance > 2:
            rendimiento = ((bot.balance - bot.balance_inicial) / bot.balance_inicial) * 100
            if rendimiento > 0:
                bot.estado = 'stopped'
                print('El bot ha alcanzado un 4% de ganancia')
                return 1
            if rendimiento < 0:
                bot.estado = 'stopped'
                print('El bot ha hecho un 1% de perdida')
                return 1
        return 0

    except BinanceAPIException as e:
        print(f"Error al actualizar el balance: {e}")
        return 0

def get_modo_operacion(ultima_vela, list_predicciones, balance, bot):
    """
    Obtiene el modo de operación del bot basado en la última vela real, las predicciones de las próximas tres velas,
    y el balance actual.
    
    Args:
    ultima_vela (dict): Un diccionario que contiene 'open' y 'close' de la última vela real.
    list_predicciones (list): Una lista anidada con las predicciones de 'close' para las próximas tres velas.
    balance (float): El balance actual del bot.
    
    Returns:
    str: 'comprar' si se cumplen las condiciones para comprar, 'vender' si se cumplen las condiciones para vender, 'esperar' de lo contrario.
    """
    try:
        if len(list_predicciones) > 1:
            # Aplanar la lista de predicciones ya que viene en formato de lista anidada
            predicciones = list_predicciones[0][0][0]
            desviacion_positiva = 0.00102
            desviacion_negativa = 0.00102
        
            # Verificar si la primera vela predicha cierra por debajo de la última vela real
            error_positivo = ultima_vela['Close'].iloc[1] > (predicciones + predicciones * desviacion_positiva)

            # Verificar si la primera vela predicha cierra por debajo de la última vela real
            error_negativo = ultima_vela['Close'].iloc[1] > (predicciones - predicciones * desviacion_negativa)

            bajada_close = all(ultima_vela['Close'].iloc[i] > ultima_vela['Close'].iloc[i + 1] for i in range(len(ultima_vela)-1))
            
            if (bot.error_real_venta == 'positivo'):
                error = error_positivo
            else:
                error = error_negativo
            
            condicion_bajista = error and bajada_close


            # Verificar si todas las predicciones cierran por encima de la apertura de la última vela real
            error_positivo = (((predicciones + (predicciones * desviacion_positiva)) - ultima_vela['Close'].iloc[1]) / ultima_vela['Close'].iloc[1]) >= 0.001

            # Verificar si todas las predicciones cierran por encima de la apertura de la última vela real
            error_negativo = (((predicciones - (predicciones * desviacion_negativa)) - ultima_vela['Close'].iloc[1]) / ultima_vela['Close'].iloc[1]) >= 0.001

            if (bot.error_real_compra == 'positivo'):
                error = error_positivo
            else:
                error = error_negativo
            
            # Verificar si cada vela es mayor que la anterior
            subida_close = all((((ultima_vela['Close'].iloc[i + 1] - ultima_vela['Close'].iloc[i]) / ultima_vela['Close'].iloc[i]) > 0) for i in range(len(ultima_vela)-1))
            
            condicion_subida = error and subida_close
            
            
            reduccion_1_por_ciento_venta = False

            # Verificar si alguna de las predicciones muestra un aumento mayor al 2% respecto a la última vela real
            if (bot.precio_compra != 0.0):
                reduccion_1_por_ciento_venta = ((ultima_vela['Close'].iloc[1] - bot.precio_compra) / bot.precio_compra) < -0.0005

            condicion_subida_predicciones = (predicciones > list_predicciones[1][0][0])

            condicion_bajista_predicciones = (predicciones < list_predicciones[1][0][0])

            condicion_vender = reduccion_1_por_ciento_venta and condicion_bajista 
        
            bot.actualizar_balance_spot("USDT")

            # Decidir modo de operación
            if bot.balance > 2 and bot.id_order_tp == 0 and bot.id_order_sell == 0 and condicion_subida and condicion_subida_predicciones:
                return 'comprar'
            if bot.id_order_tp != 0 and bot.id_order_sell == 0 and condicion_vender:
                return 'vender'
            else:
                return 'esperar'
        else:
            return 'esperar'
    
    except BinanceAPIException as e:
        print(f"Error al actualizar el balance: {e}")
        return 'esperar'

def get_orders_margin(client, symbol):
    """
    Obtiene todas las órdenes abiertas para un símbolo específico.
    
    Args:
    client (Client): El cliente de la API de Binance configurado.
    symbol (str): El símbolo del par de trading para el cual obtener las órdenes.
    
    Returns:
    list: Una lista de órdenes abiertas para el símbolo especificado.
    """
    try:
        ordenes = client.get_open_margin_orders(symbol=symbol)
        if ordenes:
            print(f"Órdenes abiertas para {symbol}:")
            for orden in ordenes:
                print(orden)
        else:
            print(f"No hay órdenes abiertas para {symbol}.")
        return ordenes
    except Exception as e:
        print(f"Error al obtener las órdenes abiertas para {symbol}: {e}")
   

def cancel_orders_margin(client, symbol):
    """
    Cancela todas las órdenes abiertas para un símbolo específico iterando por cada una.
    
    Args:
    client (Client): El cliente de la API de Binance configurado.
    symbol (str): El símbolo del par de trading para el cual cancelar las órdenes.
    """
    try:
        # Obtiene todas las órdenes abiertas para el símbolo
        open_orders = client.get_open_margin_orders(symbol=symbol)
        
        if not open_orders:
            print(f"No hay órdenes abiertas para {symbol}.")
            return

        # Itera sobre cada orden abierta y cancela cada una utilizando su orderId
        for order in open_orders:
            orderId = order['orderId']
            client.cancel_margin_order(symbol=symbol, orderId=orderId)
            print(f"Orden {orderId} para {symbol} ha sido cancelada.")

    except Exception as e:
        print(f"Error al cancelar las órdenes para {symbol}: {e}")



def get_orders_spot(client, symbol):
    """
    Obtiene todas las órdenes abiertas para un símbolo específico.
    
    Args:
    client (Client): El cliente de la API de Binance configurado.
    symbol (str): El símbolo del par de trading para el cual obtener las órdenes.
    
    Returns:
    list: Una lista de órdenes abiertas para el símbolo especificado.
    """
    try:
        ordenes = client.get_open_orders(symbol=symbol)
        if ordenes:
            print(f"Órdenes abiertas para {symbol}:")
            for orden in ordenes:
                print(orden)
        else:
            print(f"No hay órdenes abiertas para {symbol}.")
        return ordenes
    except Exception as e:
        print(f"Error al obtener las órdenes abiertas para {symbol}: {e}")

def cancel_orders_spot(client, symbol):
    """
    Cancela todas las órdenes abiertas para un símbolo específico iterando por cada una.
    
    Args:
    client (Client): El cliente de la API de Binance configurado.
    symbol (str): El símbolo del par de trading para el cual cancelar las órdenes.
    """
    try:
        # Obtiene todas las órdenes abiertas para el símbolo
        open_orders = client.get_open_orders(symbol=symbol)
        
        if not open_orders:
            print(f"No hay órdenes abiertas para {symbol}.")
            return

        # Itera sobre cada orden abierta y cancela cada una utilizando su orderId
        for order in open_orders:
            orderId = order['orderId']
            client.cancel_order(symbol=symbol, orderId=orderId)
            print(f"Orden {orderId} para {symbol} ha sido cancelada.")

    except Exception as e:
        print(f"Error al cancelar las órdenes para {symbol}: {e}")


	

