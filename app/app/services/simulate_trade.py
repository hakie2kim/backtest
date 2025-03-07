from sqlalchemy import extract
from app.core.database import SessionLocal
from app.models.price import Price
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import List, Tuple, Dict
import numpy as np


def calculate_asset_returns(
        current_price: float,
        previous_price: float
) -> float:
    """
    특정 자산의 수익률을 계산합니다.
    Args:
        current_price: 현재 매매일의 종가
        previous_price: 이전 매매일의 종가

    Returns:
        수익률 (float)
    """
    if previous_price == 0:
        return 0.0  # 이전 가격이 0인 경우 수익률을 0으로 처리 (ZeroDivisionError 방지)

    asset_return = (current_price / previous_price) - 1
    return asset_return


def simulate_trade(ticker_prices: Dict[str, List[Price]], weights: List[Tuple[str, float]], trade_date: date,
                   nav: float, cost: float, previous_prices: Dict[str, Price]) -> Tuple[float, float, Dict[str, Price]]:
    """
    주어진 리밸런싱 비중과 가격 데이터를 사용하여 매매를 시뮬레이션하고, 매매 후 NAV 를 계산합니다.

    Args:
        ticker_prices (Dict[str, List[Price]]): ticker별 가격 데이터 딕셔너리 (예: {'SPY': [Price 객체, ...], 'QQQ': [...], ...})
        weights (List[Tuple[str, float]]): 리밸런싱 비중 리스트 (예: [('SPY', 0.5), ('QQQ', 0.5), ('GLD', 0.0), ('BIL', 0.0)])
        trade_date (date): 매매일 (date 객체)
        nav (float): 현재 NAV (Net Asset Value)
        cost (float): 거래 수수료율
        previous_prices (Dict[str, Price]): 이전 매매일의 가격 정보 딕셔너리 (예: {'SPY': Price 객체, 'QQQ': Price 객체, ...})

    Returns:
        Tuple[float, float, Dict[str, Price]]: 매매 후 NAV, 거래 비용, 현재 매매일의 가격 정보
    """
    nav_after_trade = 0.0
    trade_cost = 0.0
    current_prices: Dict[str, Price] = {}  # 현재 매매일의 가격 정보 저장
    nav_before_trade: Dict[str, float] = {}  # 매매 전 nav
    trade_costs: Dict[str, float] = {}  # 거래 수수료
    returns: Dict[str, float] = {}  # 수익률
    target_nav: Dict[str, float] = {}  # 목표 NAV

    # 사용할 티커 목록 정의
    tickers = ['SPY', 'QQQ', 'GLD', 'BIL']

    # 각 ticker별 가격 정보 가져오기
    for ticker in tickers:
        if ticker in ticker_prices:
            for price in ticker_prices[ticker]:
                if price.date == trade_date:
                    current_prices[ticker] = price
                    break  # 찾았으면 종료
            else:
                # trade_date에 가격 정보가 없는 경우
                print(f"Warning: No price data found for {ticker} on {trade_date}")
        else:
            print(f"Warning: No price data found for {ticker} in ticker_prices")
            continue

    # 이전 가격 정보가 없는 경우 (첫 번째 매매일), 수익률 계산 생략
    if not previous_prices:
        # 초기 투자 비중으로 NAV 계산
        for ticker, weight in weights:
            nav_before_trade[ticker] = 0.0  # 처음 매매일의 매매 전 NAV는 0
        nav_after_trade = nav  # SPY 매매 후 NAV + QQQ 매매 후 NAV + GLD 매매 후 NAV + BIL 매매 후 NAV은 1000
    else:
        # (1) 각 자산별 "수익률" 계산
        for ticker, weight in weights:
            # 이전 매매일의 가격 정보가 있는지 확인
            if ticker in previous_prices and ticker in current_prices:
                # 가격 변화율을 사용하여 현재 가치 평가
                returns[ticker] = calculate_asset_returns(current_prices[ticker].price, previous_prices[
                    ticker].price)  # SPY 수익률 = 매매일 SPY 종가 / 이전 매매일 SPY 종가
            else:
                returns[ticker] = 1.0  # 이전 가격 정보가 없으면 수익률 1로 설정

        # (2) 각 자산별 "매매 후 NAV" 계산
        nav_after_fees = nav
        for ticker, weight in weights:
            nav_before_trade[ticker] = nav_after_fees * weight[0]  # SPY 매매 전 NAV = SPY 매매 후 NAV * SPY 수익률

        # (3) 목표 NAV 계산
        nav_total_before = sum(nav_before_trade.values())
        for ticker, weight in weights:
            target_nav[ticker] = nav_total_before * weight[1]

        # (4) 각 자산별 "거래 수수료" 계산
        for ticker, weight in weights:
            trade_costs[ticker] = abs(target_nav.get(ticker, 0.0) - nav_before_trade.get(ticker,
                                                                                         0.0)) * cost  # ABS(SPY 목표 NAV - SPY 매매 전 NAV) * 거래 수수료율

        # (5) "비용 차감 후 NAV" 계산
        nav_after_fees = sum(nav_before_trade.values()) - sum(
            trade_costs.values())  # (SPY 매매 전 NAV + QQQ 매매 전 NAV + GLD 매매 전 NAV + BIL 매매 전 NAV) - (SPY 거래 수수료 + QQQ 거래 수수료 + GLD 거래 수수료 + BIL 거래 수수료)

    # (6) 각 자산별 "매매 후 NAV" 계산
    for ticker, weight in weights:
        nav_after_trade += nav_after_fees * weight[1]  # SPY 매매 후 NAV = 비용 차감 후 NAV * SPY 리밸런싱 비중

    trade_cost = sum(trade_costs.values())  # SPY 거래 수수료 + QQQ 거래 수수료 + GLD 거래 수수료 + BIL 거래 수수료

    return nav_after_trade, trade_cost, current_prices


async def calculate_asset_returns(
        current_price: float,
        previous_price: float
) -> float:
    """
    각 자산별 수익률을 계산합니다.

    Args:
        current_price (float): 현재 매매일의 종가
        previous_price (float): 직전 매매일의 종가

    Returns:
        float: 해당 자산의 수익률
    """
    if previous_price == 0:
        return 0.0  # 이전 가격이 0인 경우, 수익률을 0으로 설정 (ZeroDivisionError 방지)

    asset_return = current_price / previous_price
    return asset_return


async def calculate_asset_pre_nav(
        asset_post_nav: float,
        asset_return: float
) -> float:
    """
    각 자산별 매매 전 NAV 를 계산합니다.

    Args:
        asset_post_nav (float): 해당 자산의 매매 후 NAV
        asset_return (float): 해당 자산의 수익률

    Returns:
        float: 해당 자산의 매매 전 NAV
    """
    return asset_post_nav * asset_return


async def calculate_nav_total_before(asset_pre_navs: Dict[str, float]) -> float:
    """
    매매 전 NAV 총합을 계산합니다.
    Args:
        asset_pre_navs (Dict[str, float]): 각 자산별 매매 전 NAV 딕셔너리
    Returns:
        float: 매매 전 NAV 총합
    """
    return sum(asset_pre_navs.values())


async def calculate_target_nav(
        nav_total_before: float,
        asset_weight: float
) -> float:
    """
    각 자산별 목표 NAV 를 계산합니다.

    Args:
        nav_total_before (float): 매매 전 NAV 총합
        asset_weight (float): 해당 자산의 리밸런싱 비중

    Returns:
        float: 해당 자산의 목표 NAV
    """
    return nav_total_before * asset_weight


async def calculate_trade_cost(
        target_nav: float,
        asset_pre_nav: float,
        cost_rate: float
) -> float:
    """
    각 자산별 거래 수수료를 계산합니다.

    Args:
        target_nav (float): 해당 자산의 목표 NAV
        asset_pre_nav (float): 해당 자산의 매매 전 NAV
        cost_rate (float): 거래 수수료율

    Returns:
        float: 해당 자산의 거래 수수료
    """
    return abs(target_nav - asset_pre_nav) * cost_rate


async def calculate_nav_after_fees(
        asset_pre_navs: List[float],
        trade_costs: List[float]
) -> float:
    """
    비용 차감 후 NAV 를 계산합니다.

    Args:
        asset_pre_navs (List[float]): 각 자산별 매매 전 NAV 리스트
        trade_costs (List[float]): 각 자산별 거래 수수료 리스트

    Returns:
        float: 비용 차감 후 NAV
    """
    return sum(asset_pre_navs) - sum(trade_costs)


async def calculate_asset_post_nav(
    nav_after_fees: float,
    asset_weight: float
) -> float:
    """
    각 자산별 매매 후 NAV 를 계산합니다.
    Args:
        nav_after_fees (float): 비용 차감 후 NAV
        asset_weight (float): 해당 자산의 리밸런싱 비중
    Returns:
        float: 해당 자산의 매매 후 NAV
    """
    return nav_after_fees * asset_weight


async def simulate_trade(ticker_prices: Dict[str, List[Price]], weights: List[Tuple[str, float]], trade_date: date,
                         nav: float, cost: float, previous_prices: Dict[str, Price]) -> Tuple[
    float, float, Dict[str, Price]]:
    """
    주어진 리밸런싱 비중과 가격 데이터를 사용하여 매매를 시뮬레이션하고, 매매 후 NAV 를 계산합니다.
    Args:
        ticker_prices (Dict[str, List[Price]]): ticker별 가격 데이터 딕셔너리 (예: {'SPY': [Price 객체, ...], 'QQQ': [...], ...})
        weights (List[Tuple[str, float]]): 리밸런싱 비중 리스트 (예: [('SPY': 0.5), ('QQQ': 0.5), ('GLD', 0.0), ('BIL', 0.0)])
        trade_date (date): 매매일 (date 객체)
        nav (float): 현재 NAV (Net Asset Value)
        cost (float): 거래 수수료율
        previous_prices (Dict[str, Price]): 이전 매매일의 가격 정보 딕셔너리 (예: {'SPY': Price 객체, 'QQQ': Price 객체, ...})
    Returns:
        Tuple[float, float, Dict[str, Price]]: 매매 후 NAV, 거래 비용, 현재 매매일의 가격 정보
    """
    nav_after_trade = 0.0
    trade_cost = 0.0
    current_prices: Dict[str, Price] = {}  # 현재 매매일의 가격 정보 저장
    nav_before_trade: Dict[str, float] = {}  # 매매 전 nav
    trade_costs: Dict[str, float] = {}  # 거래 수수료
    returns: Dict[str, float] = {}  # 수익률
    target_nav: Dict[str, float] = {}  # 목표 NAV
    nav_after_each: Dict[str, float] = {}  # 자산 별 매매 후 NAV
    asset_post_navs: Dict[str, float] = {}  # 자산 별 매매 후 NAV

    # 사용할 티커 목록 정의
    tickers = ['SPY', 'QQQ', 'GLD', 'BIL']

    # 각 ticker별 가격 정보 가져오기
    for ticker in tickers:
        if ticker in ticker_prices:
            for price in ticker_prices[ticker]:
                if price.date == trade_date:
                    current_prices[ticker] = price
                    break  # 찾았으면 종료
            else:
                # trade_date에 가격 정보가 없는 경우
                print(f"Warning: No price data found for {ticker} on {trade_date}")
        else:
            print(f"Warning: No price data found for {ticker} in ticker_prices")
            continue

    # 이전 가격 정보가 없는 경우 (첫 번째 매매일), 수익률 계산 생략
    if not previous_prices:
        # 초기 투자 비중으로 NAV 계산
        for ticker, weight in weights:
            nav_before_trade[ticker] = 0.0  # 처음 매매일의 매매 전 NAV는 0
        nav_after_trade = nav  # SPY 매매 후 NAV + QQQ 매매 후 NAV + GLD 매매 후 NAV + BIL 매매 후 NAV은 1000
    else:
        # (1) 각 자산별 "수익률" 계산
        tasks_returns = {
            ticker: calculate_asset_returns(current_prices[ticker].price, previous_prices[ticker].price)
            if ticker in previous_prices and ticker in current_prices
            else 1.0  # 이전 가격 정보가 없으면 수익률 1로 설정
            for ticker, (ticker, weight) in zip(tickers, weights)
        }

        # (2) 각 자산별 "매매 전 NAV" 계산
        for ticker, weight in weights:
            # (2) 각 자산별 "수익률" 계산
            asset_return = calculate_asset_returns(current_prices[ticker].price, previous_prices[
                ticker].price) if ticker in previous_prices and ticker in current_prices else 1.0
            nav_before_trade[ticker] = await calculate_asset_pre_nav(nav,
                                                                     asset_return)  # SPY 매매 전 NAV = SPY 매매 후 NAV * SPY 수익률

        # (3) 목표 NAV 계산
        nav_total_before = await calculate_nav_total_before(nav_before_trade)
        for ticker, weight in weights:
            target_nav[ticker] = await calculate_target_nav(nav_total_before, weight[1])

        # (4) 각 자산별 "거래 수수료" 계산
        for ticker, weight in weights:
            trade_costs[ticker] = await calculate_trade_cost(target_nav[ticker], nav_before_trade.get(ticker, 0.0),
                                                             cost)  # ABS(SPY 목표 NAV - SPY 매매 전 NAV) * 거래 수수료율

        # (5) "비용 차감 후 NAV" 계산
        nav_after_fees = await calculate_nav_after_fees(nav_before_trade,
                                                        trade_costs)  # (SPY 매매 전 NAV + QQQ 매매 전 NAV + GLD 매매 전 NAV + BIL 매매 전 NAV) - (SPY 거래 수수료 + QQQ 거래 수수료 + GLD 거래 수수료 + BIL 거래 수수료)

        # (6) 각 자산별 "매매 후 NAV" 계산
        for ticker, weight in weights:
            nav_after_each[ticker] = await calculate_asset_post_nav(nav_after_fees, weight[
                1])  # SPY 매매 후 NAV = 비용 차감 후 NAV * SPY 리밸런싱 비중

    trade_cost = sum(trade_costs.values())  # SPY 거래 수수료 + QQQ 거래 수수료 + GLD 거래 수수료 + BIL 거래 수수료

    return nav_after_trade, trade_cost, current_prices

