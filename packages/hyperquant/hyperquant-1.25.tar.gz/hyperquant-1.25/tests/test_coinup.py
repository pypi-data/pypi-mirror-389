import pybotters
from hyperquant.broker.coinup import Coinup, CoinUpDataStore
import asyncio
from logging import Logger
import time
from dataclasses import dataclass
from typing import Any, Literal
from hyperquant.logkit import get_logger
from hyperquant.broker.coinup import Coinup

apis = {"coinup": ["948a3841361bd38c30fc37355c3fb01a35135042c1c44698bed6f9cd6262cce0"]}


async def test_update():
    async with pybotters.Client(apis=apis) as client:
        async with Coinup(client=client) as broker:
            # await broker.update("detail")
            # print(broker.store.detail.get({"symbol": "WLFI-USDT"}))
            await broker.update("position")
            print(broker.store.position.find())
            # await broker.update("history_orders")
            # print(broker.store.history_orders.find())

            # await broker.update('orders')
            # print(broker.store.orders.find())

async def test_cancel_order():
    async with pybotters.Client(apis=apis) as client:
        async with Coinup(client=client) as broker:
            await broker.cancel_order('169', '2951914186269633768') 

async def test_place_order():
    async with pybotters.Client(apis=apis) as client:
        async with Coinup(client=client) as broker:
            # 市价单
            order = await broker.place_order(
                'WLFI-USDT',
                side='sell',
                volume='1',
                order_type='market',
                offset='CLOSE',
            )
            print(order)

async def test_sub_book():
    async with pybotters.Client(apis=apis) as client:
        async with Coinup(client=client) as broker:
            # symbols = [d['symbol'] for d in broker.store.detail.find()]
            # symbols = symbols[:30]
            symbols = ['ENA-USDT', 'BNB-USDT']

            await broker.sub_orderbook(symbols, depth_limit=1)
            print("Subscribed orderbook", symbols)
            # while True:
            #     await asyncio.sleep(1)
            #     print(broker.store.book.find())
            with broker.store.book.watch() as watcher:
                async for change in watcher:
                    print(change.data)


def _to_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _extract_position_volume(snapshot: dict[str, Any] | None) -> float:
    if not snapshot:
        return 0.0
    return _to_float(
        snapshot.get("canCloseVolume")
        or snapshot.get("positionVolume")
        or snapshot.get("volume")
    )


def _extract_order_id(payload: Any) -> str | None:
    if payload is None:
        return None
    if 'ids' in payload:
        ids = payload.get('ids')
        if isinstance(ids, list) and ids:
            return str(ids[0])
    else:
        return None

def _extract_order_state(snapshot: dict[str, Any] | None) -> str | None:
    if not snapshot:
        return None
    for key in ("status", "state", "orderStatus", "statusName"):
        value = snapshot.get(key)
        if value in (None, ""):
            continue
        return str(value)
    return None


def _is_order_final(snapshot: dict[str, Any] | None) -> bool:
    state = _extract_order_state(snapshot)
    if state is None:
        return False

    normalized = state.strip().lower()
    if normalized in {
        "0",
        "1",
        "new",
        "pending",
        "processing",
        "submitting",
        "submitted",
        "wait",
        "waiting",
        "partial",
        "partialfill",
        "partial-filled",
        "partially_filled",
        "partially-filled",
    }:
        return False

    try:
        numeric = float(normalized)
    except ValueError:
        pass
    else:
        # CoinUp 使用 0/1 表示活跃状态，其余视为终态
        if int(numeric) in (0, 1):
            return False
        return True

    if any(token in normalized for token in ("cancel", "done", "finish", "filled", "complete", "success", "fail")):
        return True

    # 其他未知状态保持保守，由调用方通过时间/仓位变化判断
    return False


@dataclass
class OrderSyncResult:
    position: dict[str, Any] | None
    order: dict[str, Any] | None
    before_volume: float
    after_volume: float


async def order_sync_polling(
    broker: Coinup,
    *,
    symbol: str,
    side: Literal["BUY", "SELL"],
    volume: float | int | str,
    offset: Literal["OPEN", "CLOSE"],
    order_type: Literal["limit", "market", 1, 2] = "limit",
    price: float | int | str | None = None,
    leverage_level: int | str = 1,
    position_type: int | str = 1,
    order_unit: int | str = 2,
    expect_change: float = 0.0,
    window_sec: float = 6.0,
    poll_interval: float = 0.5,
    cancel_retry: int = 3,
    logger: Logger | None = None,
) -> OrderSyncResult:
    await broker.update("position")
    baseline = broker.store.position.get({"symbol": symbol})
    before_volume = _extract_position_volume(baseline)

    contract_id = broker.get_contract_id(symbol)
    history_payload = {"contractId": contract_id} if contract_id else None

    order_id: str | None = None
    need_cancel = True
    current_volume = before_volume
    position_snapshot: dict[str, Any] | None = None
    order_snapshot: dict[str, Any] | None = None
    try:
        started_at = time.time() * 1000
        response = await broker.place_order(
            symbol=symbol,
            side=side,
            volume=volume,
            order_type=order_type,
            price=price,
            position_type=position_type,
            leverage_level=leverage_level,
            offset=offset,
            order_unit=order_unit,
        )
        latency = int(time.time() * 1000 - started_at)
        if logger:
            logger.info(f"下单延迟 {latency} ms")
        order_id = _extract_order_id(response)
        if order_id is None:
            raise RuntimeError(f"place_order 缺少 order_id: {response}")
    except Exception:
        raise

    deadline = time.monotonic() + window_sec

    try:
        while time.monotonic() < deadline:
            try:
                await broker.update(
                    "history_orders",
                    history_orders_payload=history_payload,
                )
            except Exception as exc:  # pragma: no cover - 防御
                if logger:
                    logger.debug(f"history_orders 更新失败: {exc}")
            if order_id is not None:
                candidate = broker.store.history_orders.get({"orderId": order_id})
                if candidate:
                    order_snapshot = candidate
                    if _is_order_final(candidate):
                        need_cancel = False
                        break

            await asyncio.sleep(poll_interval)
        else:
            if logger:
                logger.warning(
                    f"订单处理超时: symbol={symbol} side={side} offset={offset} order_id={order_id}"
                )
    finally:
        if order_id and need_cancel:
            for attempt in range(cancel_retry):
                try:
                    await broker.cancel_order(symbol, order_id)
                    break
                except Exception as exc:  # pragma: no cover - 防御
                    if logger:
                        logger.info(
                            f"撤单失败({attempt + 1}/{cancel_retry}): order_id={order_id} err={exc}"
                        )
                    await asyncio.sleep(0.5)

        try:
            await broker.update(
                "history_orders",
                history_orders_payload=history_payload,
            )
        except Exception as exc:  # pragma: no cover - 防御
            if logger:
                logger.debug(f"history_orders 更新失败: {exc}")
        if order_id is not None:
            latest_entry = broker.store.history_orders.get({"orderId": order_id})
            if latest_entry:
                order_snapshot = latest_entry

        try:
            await broker.update("position")
        except Exception as exc:  # pragma: no cover - 防御
            if logger:
                logger.debug(f"position 更新失败: {exc}")
        position_snapshot = broker.store.position.get({"symbol": symbol})
        current_volume = _extract_position_volume(position_snapshot)

    return OrderSyncResult(position_snapshot, order_snapshot, before_volume, current_volume)

async def test_order_sync_polling():
    logger = get_logger("test_order_sync_polling")
    async with pybotters.Client(apis=apis) as client:
        async with Coinup(client=client) as broker:
            result = await order_sync_polling(
                broker,
                symbol="WLFI-USDT",
                side="BUY",
                volume=3,
                offset="OPEN",
                order_type="market",
                logger=logger,
            )
            print(result)



if __name__ == "__main__":
    import asyncio

    asyncio.run(test_update())
