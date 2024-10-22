from binance.enums import *

def comprar_margin(balance, client):
    client.isolated_margin_account(symbol='BTCUSDT', leverage=20)
    order = client.create_margin_order(
        symbol='BTCUSDT',
        side=SIDE_BUY,
        type=ORDER_TYPE_MARKET,
        quoteOrderQty=balance,
        isIsolated='TRUE')  # Asegúrate de especificar que es una orden en margin aislado
    return order


def vender_margin(client):
    """
    Vende toda la cantidad de un activo específico en margin aislado.
    
    Args:
    client (Client): Instancia del cliente de Binance.
    symbol (str): Símbolo del par de trading, por ejemplo 'BTCUSDT'.
    asset (str): El activo que deseas vender, por ejemplo 'BTC'.

    """
    
    def obtener_saldo_margin_aislado(client, symbol, asset):
        """Obtiene el saldo disponible de un activo específico en margin aislado."""
        info = client.get_isolated_margin_account()
        for asset_balance in info['assets']:
            if asset_balance['baseAsset']['asset'] == asset and asset_balance['symbol'] == symbol:
                balance = float(asset_balance['baseAsset']['free'])
                return balance
        return 0

    cantidad_btc = obtener_saldo_margin_aislado(client, 'BTCUSDT', 'BTC')
    
    if cantidad_btc > 0:
        order = client.create_margin_order(
            symbol='BTCUSDT',
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=cantidad_btc,
            isIsolated='TRUE')
        print("Orden de venta de mercado ejecutada en margin aislado:", order)
    else:
        print("No hay saldo disponible de BTC para vender en margin aislado.")

def set_sl_tp_margin(client, symbol, cantidad, precio_sl, precio_tp):
    """
    Establece órdenes separadas de stop loss y take profit.
    
    Args:
    client (Client): El cliente de la API de Binance configurado.
    symbol (str): El símbolo del par de trading.
    cantidad (float): La cantidad del activo para las órdenes.
    precio_sl (float): El precio para el stop loss.
    precio_tp (float): El precio para el take profit.
    """
    # Establecer orden de take profit (venta limitada)
    orden_tp = client.create_margin_order(
        symbol=symbol,
        side=SIDE_SELL,
        type=ORDER_TYPE_LIMIT,
        timeInForce=TIME_IN_FORCE_GTC,
        quantity="{:.8f}".format(cantidad),
        price="{:.8f}".format(precio_tp),
        isIsolated='TRUE')  # Asume margin aislado
    
    print("Orden de Take Profit establecida:", orden_tp)
    
    # Establecer orden de stop loss (stop-limit)
    orden_sl = client.create_margin_order(
        symbol=symbol,
        side=SIDE_SELL,
        type=ORDER_TYPE_STOP_LOSS_LIMIT,
        timeInForce=TIME_IN_FORCE_GTC,
        quantity="{:.8f}".format(cantidad),
        price="{:.8f}".format(precio_sl),  # Precio al cual se ejecutará la venta
        stopPrice="{:.8f}".format(precio_sl),  # Precio que activará la orden
        isIsolated='TRUE')  # Asume margin aislado
    
    print("Orden de Stop Loss establecida:", orden_sl)

