from fastmcp import FastMCP
from pydantic import Field
from okx.Trade import TradeAPI

from .config import *

ACCOUNT = TradeAPI(
    api_key=OKX_API_KEY,
    api_secret_key=OKX_API_SECRET,
    passphrase=OKX_PASSPHRASE,
    use_server_time=False,
    flag=OKX_TRADE_FLAG,
    domain=OKX_BASE_URL,
)


def add_tools(mcp: FastMCP):

    @mcp.tool(
        title="Place order",
        description="Place an order only if you have sufficient funds",
    )
    def place_order(
        instId: str = Field(description="Instrument ID, e.g. BTC-USDT"),
        tdMode: str = Field(description="Trade mode."
                                        "Margin mode: `cross`/`isolated`. Non-Margin mode: `cash`. "
                                        "\n`spot_isolated`: (only applicable to SPOT lead trading, `tdMode` should be `spot_isolated` for SPOT lead trading.)"
                                        "\nNote: `isolated` is not available in multi-currency margin mode and portfolio margin mode."),
        side: str = Field(description="Order side, `buy`/`sell`"),
        ordType: str = Field(description="Order type. "
                                         "\n`market`: Market order, only applicable to SPOT/MARGIN/FUTURES/SWAP"
                                         "\n`limit`: Limit order"
                                         "\n`post_only`: Post-only order"
                                         "\n`fok`: Fill-or-kill order"
                                         "\n`ioc`: Immediate-or-cancel order"
                                         "\n`optimal_limit_ioc`: Market order with immediate-or-cancel order (applicable only to Expiry Futures and Perpetual Futures)."
                                         "\n`mmp`: Market Maker Protection (only applicable to Option in Portfolio Margin mode)"
                                         "\n`mmp_and_post_only`: Market Maker Protection and Post-only order(only applicable to Option in Portfolio Margin mode)"),
        sz: str = Field(description="Quantity to buy or sell"),
        ccy: str = Field("", description="Margin currency. Applicable to all `isolated` `MARGIN` orders and `cross` `MARGIN` orders in `Futures mode`"),
        clOrdId: str = Field("", description="Client Order ID as assigned by the client."
                                             "A combination of case-sensitive alphanumerics, all numbers, or all letters of up to 32 characters."
                                             "Only applicable to general order. It will not be posted to algoId when placing TP/SL order after the general order is filled completely."),
        tag: str = Field("", description="Order tag. A combination of case-sensitive alphanumerics, all numbers, or all letters of up to 16 characters"),
        posSide: str = Field("", description="Position side. The default is `net` in the net mode. "
                                             "It is required in the `long/short` mode, and can only be `long` or `short`. "
                                             "Only applicable to `FUTURES`/`SWAP`."),
        px: str = Field("", description="Order price. Only applicable to `limit`,`post_only`,`fok`,`ioc`,`mmp`,`mmp_and_post_only` order. "
                                        "When placing an option order, one of px/pxUsd/pxVol must be filled in, and only one can be filled in"),
        tgtCcy: str = Field("", description="Whether the target currency uses the quote or base currency. "
                                            "`base_ccy`: Base currency, `quote_ccy`: Quote currency. "
                                            "Only applicable to `SPOT` Market Orders. "
                                            "Default is `quote_ccy` for buy, `base_ccy` for sell"),
        reduceOnly: str = Field("", description="Whether orders can only reduce in position size. "
                                                "Valid options: `true` or `false`. The default value is `false`. "
                                                "Only applicable to `MARGIN` orders, and `FUTURES`/`SWAP` orders in net mode. "
                                                "Only applicable to `Futures mode` and `Multi-currency margin`."),
        stpMode: str = Field("", description="Self trade prevention mode: `cancel_maker`,`cancel_taker`,`cancel_both`. Cancel both does not support FOK. "
                                             "The account-level acctStpMode will be used to place orders by default. The default value of this field is `cancel_maker`. "
                                             "Users can log in to the webpage through the master account to modify this configuration. "
                                             "Users can also utilize the stpMode request parameter of the placing order endpoint to determine the stpMode of a certain order."),
        pxUsd: str = Field("", description="Place options orders in `USD`. Only applicable to options. "
                                           "When placing an option order, one of px/pxUsd/pxVol must be filled in, and only one can be filled in"),
        pxVol: str = Field("", description="Place options orders based on implied volatility, where 1 represents 100%. Only applicable to options. "
                                           "When placing an option order, one of px/pxUsd/pxVol must be filled in, and only one can be filled in"),
        banAmend: str = Field("", description="Whether to disallow the system from amending the size of the SPOT Market Order. "
                                              "Valid options: `true` or `false`. The default value is `false`. "
                                              "If `true`, system will not amend and reject the market order if user does not have sufficient funds. "
                                              "Only applicable to SPOT Market Orders"),
        attachAlgoOrds: list | None = Field(None, description="TP/SL information attached when placing order"),
    ):
        params = {
            'instId': instId, 'tdMode': tdMode, 'side': side, 'ordType': ordType, 'sz': sz, 'ccy': ccy,
            'clOrdId': clOrdId, 'tag': tag, 'posSide': posSide, 'px': px, 'reduceOnly': reduceOnly,
            'tgtCcy': tgtCcy, 'stpMode': stpMode, 'pxUsd': pxUsd, 'pxVol': pxVol, 'banAmend': banAmend,
        }
        if isinstance(reduceOnly, bool):
            params['reduceOnly'] = 'true' if reduceOnly else 'false'
        if isinstance(banAmend, bool):
            params['banAmend'] = 'true' if banAmend else 'false'
        if attachAlgoOrds:
            params['attachAlgoOrds'] = attachAlgoOrds
        return ACCOUNT.place_order(**params)

    @mcp.tool(
        title="Cancel order",
        description="Cancel an incomplete order",
    )
    def cancel_order(
        instId: str = Field(description="Instrument ID, e.g. BTC-USDT"),
        ordId: str = Field("", description="Order ID. Either ordId or clOrdId is required. If both are passed, ordId will be used"),
        clOrdId: str = Field("", description="Client Order ID as assigned by the client"),
    ):
        return ACCOUNT.cancel_order(instId=instId, ordId=ordId, clOrdId=clOrdId)

    @mcp.tool(
        title="Order details",
        description="Retrieve order details",
    )
    def get_trade_order(
        instId: str = Field(description="Instrument ID, e.g. BTC-USDT"),
        ordId: str = Field("", description="Order ID. Either ordId or clOrdId is required. If both are passed, ordId will be used"),
        clOrdId: str = Field("", description="Client Order ID as assigned by the client"),
    ):
        resp = ACCOUNT.get_order(instId=instId, ordId=ordId, clOrdId=clOrdId)
        resp["_response_schema"] = """
        instType	String	Instrument type `MARGIN/SWAP/FUTURES/OPTION`
        instId	String	Instrument ID
        tgtCcy	String	Order quantity unit setting for sz
            base_ccy: Base currency ,quote_ccy: Quote currency
            Only applicable to SPOT Market Orders
            Default is quote_ccy for buy, base_ccy for sell
        ccy	String	Margin currency
            Applicable to all isolated MARGIN orders and cross MARGIN orders in Futures mode, FUTURES and SWAP contracts.
        ordId	String	Order ID
        clOrdId	String	Client Order ID as assigned by the client
        tag	String	Order tag
        px	String	Price. For options, use coin as unit (e.g. BTC, ETH)
        pxUsd	String	Options price in USDOnly applicable to options; return "" for other instrument types
        pxVol	String	Implied volatility of the options orderOnly applicable to options; return "" for other instrument types
        pxType	String	Price type of options
            px: Place an order based on price, in the unit of coin (the unit for the request parameter px is BTC or ETH)
            pxVol: Place an order based on pxVol
            pxUsd: Place an order based on pxUsd, in the unit of USD (the unit for the request parameter px is USD)
        sz	String	Quantity to buy or sell
        pnl	String	Profit and loss (excluding the fee). Applicable to orders which have a trade and aim to close position. It always is 0 in other conditions
        ordType	String	Order type
            market: Market order
            limit: Limit order
            post_only: Post-only order
            fok: Fill-or-kill order
            ioc: Immediate-or-cancel order
            optimal_limit_ioc: Market order with immediate-or-cancel order
            mmp: Market Maker Protection (only applicable to Option in Portfolio Margin mode)
            mmp_and_post_only: Market Maker Protection and Post-only order(only applicable to Option in Portfolio Margin mode)
            op_fok: Simple options (fok)
        side	String	Order side
        posSide	String	Position side
        tdMode	String	Trade mode
        accFillSz	String	Accumulated fill quantity
            The unit is base_ccy for SPOT and MARGIN, e.g. BTC-USDT, the unit is BTC; For market orders, the unit both is base_ccy when the tgtCcy is base_ccy or quote_ccy;
            The unit is contract for FUTURES/SWAP/OPTION
        fillPx	String	Last filled price. If none is filled, it will return "".
        tradeId	String	Last traded ID
        fillSz	String	Last filled quantity
            The unit is base_ccy for SPOT and MARGIN, e.g. BTC-USDT, the unit is BTC; For market orders, the unit both is base_ccy when the tgtCcy is base_ccy or quote_ccy;
            The unit is contract for FUTURES/SWAP/OPTION
        fillTime	String	Last filled time
        avgPx	String	Average filled price. If none is filled, it will return "".
        state	String	State. canceled/live/partially_filled/filled/mmp_canceled
        stpMode	String	Self trade prevention mode
        lever	String	Leverage, from 0.01 to 125. Only applicable to MARGIN/FUTURES/SWAP
        attachAlgoClOrdId	String	Client-supplied Algo ID when placing order attaching TP/SL.
        tpTriggerPx	String	Take-profit trigger price.
        tpTriggerPxType	String	Take-profit trigger price type.
            last: last price
            index: index price
            mark: mark price
        tpOrdPx	String	Take-profit order price.
        slTriggerPx	String	Stop-loss trigger price.
        slTriggerPxType	String	Stop-loss trigger price type.
            last: last price
            index: index price
            mark: mark price
        slOrdPx	String	Stop-loss order price.
        attachAlgoOrds	Array of objects	TP/SL information attached when placing order
        > attachAlgoId	String	The order ID of attached TP/SL order. It can be used to identity the TP/SL order when amending. It will not be posted to algoId when placing TP/SL order after the general order is filled completely.
        > attachAlgoClOrdId	String	Client-supplied Algo ID when placing order attaching TP/SL
            A combination of case-sensitive alphanumerics, all numbers, or all letters of up to 32 characters.
            It will be posted to algoClOrdId when placing TP/SL order once the general order is filled completely.
        > tpOrdKind	String	TP order kind. condition/limit
        > tpTriggerPx	String	Take-profit trigger price.
        > tpTriggerPxType	String	Take-profit trigger price type.
            last: last price
            index: index price
            mark: mark price
        > tpOrdPx	String	Take-profit order price.
        > slTriggerPx	String	Stop-loss trigger price.
        > slTriggerPxType	String	Stop-loss trigger price type.
            last: last price
            index: index price
            mark: mark price
        > slOrdPx	String	Stop-loss order price.
        > sz	String	Size. Only applicable to TP order of split TPs
        > amendPxOnTriggerType	String	Whether to enable Cost-price SL. Only applicable to SL order of split TPs.
            0: disable, the default value
            1: Enable
        > amendPxOnTriggerType	String	Whether to enable Cost-price SL. Only applicable to SL order of split TPs.
            0: disable, the default value
            1: Enable
        > failCode	String	The error code when failing to place TP/SL order, e.g. 51020. The default is ""
        > failReason	String	The error reason when failing to place TP/SL order. The default is ""
        linkedAlgoOrd	Object	Linked SL order detail, only applicable to the order that is placed by one-cancels-the-other (OCO) order that contains the TP limit order.
        > algoId	String	Algo ID
        feeCcy	String	Fee currency
            For maker sell orders of Spot and Margin, this represents the quote currency. For all other cases, it represents the currency in which fees are charged.
        fee	String	Fee amount
            For Spot and Margin (excluding maker sell orders): accumulated fee charged by the platform, always negative
            For maker sell orders in Spot and Margin, Expiry Futures, Perpetual Futures and Options: accumulated fee and rebate (always in quote currency for maker sell orders in Spot and Margin)
        rebateCcy	String	Rebate currency
            For maker sell orders of Spot and Margin, this represents the base currency. For all other cases, it represents the currency in which rebates are paid.
        rebate	String	Rebate amount, only applicable to Spot and Margin
            For maker sell orders: Accumulated fee and rebate amount in base currency.
            For all other cases, it represents the maker rebate amount, always positive, return "" if no rebate.
        source	String	Order source
            6: The normal order triggered by the trigger order
            7: The normal order triggered by the TP/SL order
            13: The normal order triggered by the algo order
            25: The normal order triggered by the trailing stop order
            34: The normal order triggered by the chase order
        category	String	Category. normal/twap/adl/full_liquidation/partial_liquidation/delivery/ddh(Delta dynamic hedge)/auto_conversion
        reduceOnly	String	Whether the order can only reduce the position size. Valid options: true or false.
        isTpLimit	String	Whether it is TP limit order. true or false
        cancelSource	String	Code of the cancellation source.
        cancelSourceReason	String	Reason for the cancellation.
        quickMgnType	String	Quick Margin type, Only applicable to Quick Margin Mode of isolated margin. manual/auto_borrow/auto_repay
        algoClOrdId	String	Client-supplied Algo ID. There will be a value when algo order attaching algoClOrdId is triggered, or it will be "".
        algoId	String	Algo ID. There will be a value when algo order is triggered, or it will be "".
        tradeQuoteCcy	String	The quote currency used for trading.
        """
        return resp

    @mcp.tool(
        title="Order list",
        description="Retrieve all incomplete orders under the current account",
    )
    def get_order_list(
        instType: str = Field("", description="Instrument type: `MARGIN/SWAP/FUTURES/OPTION`"),
        instFamily: str = Field("", description="Instrument family. Applicable to `FUTURES/SWAP/OPTION`"),
        instId: str = Field("", description="Instrument ID, e.g. BTC-USD-200927"),
        state: str = Field("", description="State: `live`/`partially_filled`"),
        ordType: str = Field("", description="Order type. "
                                             "\n`market`: Market order"
                                             "\n`limit`: Limit order"
                                             "\n`post_only`: Post-only order"
                                             "\n`fok`: Fill-or-kill order"
                                             "\n`ioc`: Immediate-or-cancel order"
                                             "\n`optimal_limit_ioc`: Market order with immediate-or-cancel order"
                                             "\n`mmp`: Market Maker Protection (only applicable to Option in Portfolio Margin mode)"
                                             "\n`mmp_and_post_only`: Market Maker Protection and Post-only order(only applicable to Option in Portfolio Margin mode)"
                                             "\n`op_fok`: Simple options (fok)"),
    ):
        resp = ACCOUNT.get_order_list(
            instType=instType,
            instFamily=instFamily,
            instId=instId,
            state=state,
            ordType=ordType,
            limit=100,
        )
        resp["_response_schema"] = """
        instType	String	Instrument type
        instId	String	Instrument ID
        tgtCcy	String	Order quantity unit setting for sz
            base_ccy: Base currency, quote_ccy: Quote currency
            Only applicable to SPOT Market Orders
            Default is quote_ccy for buy, base_ccy for sell
        ccy	String	Margin currency. Applicable to all isolated MARGIN orders and cross MARGIN orders in Futures mode, FUTURES and SWAP contracts.
        ordId	String	Order ID
        clOrdId	String	Client Order ID as assigned by the client
        tag	String	Order tag
        px	String	Price. For options, use coin as unit (e.g. BTC, ETH)
        pxUsd	String	Options price in USDOnly applicable to options; return "" for other instrument types
        pxVol	String	Implied volatility of the options orderOnly applicable to options; return "" for other instrument types
        pxType	String	Price type of options
            px: Place an order based on price, in the unit of coin (the unit for the request parameter px is BTC or ETH)
            pxVol: Place an order based on pxVol
            pxUsd: Place an order based on pxUsd, in the unit of USD (the unit for the request parameter px is USD)
        sz	String	Quantity to buy or sell
        pnl	String	Profit and loss (excluding the fee).
            Applicable to orders which have a trade and aim to close position. It always is 0 in other conditions
        ordType	String	Order type
            market: Market order
            limit: Limit order
            post_only: Post-only order
            fok: Fill-or-kill order
            ioc: Immediate-or-cancel order
            optimal_limit_ioc: Market order with immediate-or-cancel order
            mmp: Market Maker Protection (only applicable to Option in Portfolio Margin mode)
            mmp_and_post_only: Market Maker Protection and Post-only order(only applicable to Option in Portfolio Margin mode)
            op_fok: Simple options (fok)
        side	String	Order side
        posSide	String	Position side
        tdMode	String	Trade mode
        accFillSz	String	Accumulated fill quantity
        fillPx	String	Last filled price
        tradeId	String	Last trade ID
        fillSz	String	Last filled quantity
        fillTime	String	Last filled time
        avgPx	String	Average filled price. If none is filled, it will return "".
        state	String	State. live/partially_filled
        lever	String	Leverage, from 0.01 to 125. Only applicable to MARGIN/FUTURES/SWAP
        attachAlgoClOrdId	String	Client-supplied Algo ID when placing order attaching TP/SL.
        tpTriggerPx	String	Take-profit trigger price.
        tpTriggerPxType	String	Take-profit trigger price type.
            last: last price
            index: index price
            mark: mark price
        tpOrdPx	String	Take-profit order price.
        slTriggerPx	String	Stop-loss trigger price.
        slTriggerPxType	String	Stop-loss trigger price type.
            last: last price
            index: index price
            mark: mark price
        slOrdPx	String	Stop-loss order price.
        attachAlgoOrds	Array of objects	TP/SL information attached when placing order
        > attachAlgoId	String	The order ID of attached TP/SL order. It can be used to identity the TP/SL order when amending. It will not be posted to algoId when placing TP/SL order after the general order is filled completely.
        > attachAlgoClOrdId	String	Client-supplied Algo ID when placing order attaching TP/SL
            A combination of case-sensitive alphanumerics, all numbers, or all letters of up to 32 characters.
            It will be posted to algoClOrdId when placing TP/SL order once the general order is filled completely.
        > tpOrdKind	String	TP order kind. condition/limit
        > tpTriggerPx	String	Take-profit trigger price.
        > tpTriggerPxType	String	Take-profit trigger price type.
            last: last price
            index: index price
            mark: mark price
        > tpOrdPx	String	Take-profit order price.
        > slTriggerPx	String	Stop-loss trigger price.
        > slTriggerPxType	String	Stop-loss trigger price type.
            last: last price
            index: index price
            mark: mark price
        > slOrdPx	String	Stop-loss order price.
        > sz	String	Size. Only applicable to TP order of split TPs
        > amendPxOnTriggerType	String	Whether to enable Cost-price SL. Only applicable to SL order of split TPs.
            0: disable, the default value
            1: Enable
        > failCode	String	The error code when failing to place TP/SL order, e.g. 51020. The default is ""
        > failReason	String	The error reason when failing to place TP/SL order. The default is ""
        linkedAlgoOrd	Object	Linked SL order detail, only applicable to the order that is placed by one-cancels-the-other (OCO) order that contains the TP limit order.
        > algoId	String	Algo ID
        stpMode	String	Self trade prevention mode
        feeCcy	String	Fee currency
            For maker sell orders of Spot and Margin, this represents the quote currency. For all other cases, it represents the currency in which fees are charged.
        fee	String	Fee amount
            For Spot and Margin (excluding maker sell orders): accumulated fee charged by the platform, always negative
            For maker sell orders in Spot and Margin, Expiry Futures, Perpetual Futures and Options: accumulated fee and rebate (always in quote currency for maker sell orders in Spot and Margin)
        rebateCcy	String	Rebate currency
            For maker sell orders of Spot and Margin, this represents the base currency. For all other cases, it represents the currency in which rebates are paid.
        rebate	String	Rebate amount, only applicable to Spot and Margin
            For maker sell orders: Accumulated fee and rebate amount in base currency.
            For all other cases, it represents the maker rebate amount, always positive, return "" if no rebate.
        source	String	Order source
            6: The normal order triggered by the trigger order
            7: The normal order triggered by the TP/SL order
            13: The normal order triggered by the algo order
            25: The normal order triggered by the trailing stop order
            34: The normal order triggered by the chase order
        reduceOnly	String	Whether the order can only reduce the position size. Valid options: true or false.
        quickMgnType	String	Quick Margin type, Only applicable to Quick Margin Mode of isolated margin. manual/auto_borrow/auto_repay
        algoClOrdId	String	Client-supplied Algo ID. There will be a value when algo order attaching algoClOrdId is triggered, or it will be "".
        algoId	String	Algo ID. There will be a value when algo order is triggered, or it will be "".
        isTpLimit	String	Whether it is TP limit order. true or false
        cancelSource	String	Code of the cancellation source.
        cancelSourceReason	String	Reason for the cancellation.
        tradeQuoteCcy	String	The quote currency used for trading.
        """
        return resp
