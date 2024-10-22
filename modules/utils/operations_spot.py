from binance.enums import *
from binance.exceptions import BinanceAPIException
import math

def comprar_spot(balance, client):

    def ajustar_precio(precio, tick_size):
        """Ajusta el precio al tick size más cercano permitido."""
        tick_decimals = str(tick_size)[::-1].find('.')
        return round(precio / tick_size) * tick_size
    
    def calcular_cantidad_btc(client, balance_usdt, precio_orden):
        # Obtener el precio actual de BTC en términos de USDT
        info = client.get_symbol_info('BTCUSDT')
        lot_size_filter = [f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
        step_size = float(lot_size_filter['stepSize'])

        # Calcular la cantidad de BTC que puedes comprar
        cantidad_btc = balance_usdt / precio_orden

        # Asegurarse de que la cantidad cumple con las restricciones de tamaño de lote
        cantidad_btc = math.floor(cantidad_btc / step_size) * step_size

        cantidad_btc = round(cantidad_btc, 6)

        return cantidad_btc

    info = client.get_symbol_info('BTCUSDT')
    price_filter = [f for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
    tick_size = float(price_filter['tickSize'])

    # Obtener el precio de apertura de la vela actual
    klines = client.get_klines(symbol='BTCUSDT', interval=KLINE_INTERVAL_5MINUTE)
    precio_apertura = float(klines[-1][1])

    # Calcular el precio de la orden de límite como el 99.9% del precio de apertura
    precio_orden_limite = precio_apertura * 1.00001

    # Define cuántos ticks por debajo del precio de mercado quieres que esté el stopPrice
    ticks_por_debajo = 3

    # Ajusta el precio_sl para que esté unos ticks por debajo del precio de mercado
    precio_orden_limite = ajustar_precio(precio_orden_limite - ticks_por_debajo * tick_size, tick_size)

    cantidad_btc = calcular_cantidad_btc(client, balance, precio_orden_limite)

    tries = 0

    while tries < 10:
        try:
            order = client.create_order(
                symbol='BTCUSDT',
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=cantidad_btc,
                price="{:0.0{}f}".format(precio_orden_limite, 5),
                )
            print("Orden de compra de límite creada:", order)
            return order
        except BinanceAPIException as e:
            print(f"Error al realizar la operación: {e}")
            precio_orden_limite += 1
            tries += 1
            print("Incrementando precio_compra y volviendo a intentar...")
    return None

def vender_spot_rapido(client):
    """
    Vende toda la cantidad de un activo específico en margin aislado.
    
    Args:
    client (Client): Instancia del cliente de Binance.
    symbol (str): Símbolo del par de trading, por ejemplo 'BTCUSDT'.
    asset (str): El activo que deseas vender, por ejemplo 'BTC'.

    """
    
    def obtener_saldo(client, moneda):
        """Obtiene el saldo disponible de un activo específico en margin aislado."""
        account_details = client.get_account()
        for balance in account_details['balances']:
            if balance['asset'] == moneda:
                return float(balance['free'])
        return 0

    try:
        while obtener_saldo(client, 'BTC') > 0:
            cantidad_btc = obtener_saldo(client, 'BTC')
            print(cantidad_btc)

            if cantidad_btc > 0:

                order = client.create_order(
                    symbol='BTCUSDT',
                    side=SIDE_SELL,
                    type=ORDER_TYPE_MARKET,
                    quantity=cantidad_btc,
                    )
                print("Orden de venta de límite creada:", order)
            else:
                print("No hay saldo disponible de BTC.")
    except BinanceAPIException as e:
        print(f"Error al realizar la operación: {e}")

def vender_spot(client, bot):
    """
    Vende toda la cantidad de un activo específico en margin aislado.
    
    Args:
    client (Client): Instancia del cliente de Binance.
    symbol (str): Símbolo del par de trading, por ejemplo 'BTCUSDT'.
    asset (str): El activo que deseas vender, por ejemplo 'BTC'.

    """

    def obtener_saldo(client, moneda):
        """Obtiene el saldo disponible de un activo específico en margin aislado."""
        account_details = client.get_account()
        for balance in account_details['balances']:
            if balance['asset'] == moneda:
                return float(balance['free'])
        return 0
    
    def ajustar_precio(precio, tick_size):
        """Ajusta el precio al tick size más cercano permitido."""
        tick_decimals = str(tick_size)[::-1].find('.')
        return round(precio / tick_size) * tick_size

    try:

        if bot.id_order_tp > 0:
                # Si el bloque try se ejecuta con éxito, cancela la orden con id `bot.order_id_tp`
                client.cancel_order(symbol='BTCUSDT', orderId=bot.id_order_tp)
                bot.id_order_tp = 0
                print("Orden de Take Profit cancelada.")

        cantidad_btc = obtener_saldo(client, 'BTC')

        if cantidad_btc > 0:

            info = client.get_symbol_info('BTCUSDT')
            price_filter = [f for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
            tick_size = float(price_filter['tickSize'])

            # Obtener el precio de apertura de la vela actual
            klines = client.get_klines(symbol='BTCUSDT', interval=KLINE_INTERVAL_5MINUTE)
            precio_apertura = float(klines[-1][1])

            # Calcular el precio de la orden de límite como el 99.9% del precio de apertura
            precio_orden_limite = precio_apertura * 1.001

            # Define cuántos ticks por debajo del precio de mercado quieres que esté el stopPrice
            ticks_por_debajo = 3

            # Ajusta el precio_sl para que esté unos ticks por debajo del precio de mercado
            precio_orden_limite = ajustar_precio(precio_orden_limite - ticks_por_debajo * tick_size, tick_size)

            while True:
                try:
                    order = client.create_order(
                        symbol='BTCUSDT',
                        side=SIDE_SELL,
                        type=ORDER_TYPE_STOP_LOSS_LIMIT,
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity="{:0.0{}f}".format(cantidad_btc, 5),
                        price="{:0.0{}f}".format(precio_orden_limite, 5),  # Precio al cual se ejecutará la venta
                        stopPrice="{:0.0{}f}".format(precio_orden_limite, 5),  # Precio que activará la orden
                    )  # Asume margin aislado
                        
                    bot.id_order_sell = order['orderId']
                    print("Orden de venta de límite creada:", order)

                    break;
                except BinanceAPIException as e:
                    print(f"Error al realizar la operación: {e}")
                    precio_orden_limite -= 1
                    print("Incrementando precio_venta y volviendo a intentar...")
        else:
            print("No hay saldo disponible de BTC.")
    except BinanceAPIException as e:
        print(f"Error al realizar la operación: {e}")

def set_sl_tp_spot(client, symbol, cantidad, precio_sl, precio_tp, bot):
    """
    Establece órdenes separadas de stop loss y take profit.
    
    Args:
    client (Client): El cliente de la API de Binance configurado.
    symbol (str): El símbolo del par de trading.
    cantidad (float): La cantidad del activo para las órdenes.
    precio_sl (float): El precio para el stop loss.
    precio_tp (float): El precio para el take profit.

    """
    

    def ajustar_precio(precio, tick_size):
        """Ajusta el precio al tick size más cercano permitido."""
        tick_decimals = str(tick_size)[::-1].find('.')
        return round(precio / tick_size) * tick_size

    info = client.get_symbol_info('BTCUSDT')
    price_filter = [f for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
    tick_size = float(price_filter['tickSize'])

    
    # Define cuántos ticks por debajo del precio de mercado quieres que esté el stopPrice
    ticks_por_debajo = 3

    # Ajusta el precio_sl para que esté unos ticks por debajo del precio de mercado
    precio_sl = ajustar_precio(precio_sl - ticks_por_debajo * tick_size, tick_size)
    precio_tp = ajustar_precio(precio_tp - ticks_por_debajo * tick_size, tick_size)

    while True:
        try:
            # Establecer orden de take profit (venta limitada)
            orden_tp = client.create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_TAKE_PROFIT_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity="{:0.0{}f}".format(cantidad, 5),
                price="{:0.0{}f}".format(precio_tp, 5),
                stopPrice="{:0.0{}f}".format(precio_tp, 5),  # Precio que activará la orden
            )  # Asume margin aislado
            print("Orden de Take Profit establecida:", orden_tp)
            # Obtener el ID de la orden
            bot.id_order_tp = orden_tp['orderId']
            print("El ID de la orden es:", bot.id_order_tp)
            break  # Salir del bucle while si se estableció la orden exitosamente
        except BinanceAPIException as e:
            print(f"Error al establecer la orden de Take Profit: {e}")
            # Incrementar el precio_tp para intentar nuevamente
            precio_tp += 1
            print("Incrementando precio_tp y volviendo a intentar...")


    

        
