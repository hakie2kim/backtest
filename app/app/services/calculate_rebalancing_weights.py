from app.app.services.calculate_momentum import calculate_momentum
from datetime import date
from typing import List, Tuple


def calculate_rebalancing_weights(
        ticker_prices: dict,
        trade_date: date,
        caculate_month: int
) -> List[Tuple[str, float]]:
    """
    리밸런싱 비중을 계산합니다.

    Args:
        ticker_prices: ticker별 가격 데이터 딕셔너리 (예: {'SPY': [Price 객체, ...], 'QQQ': [...], ...})
        trade_date: 매매일 (date 객체)
        caculate_month: 비중 계산 기준 개월 수

    Returns:
        리밸런싱 비중 리스트 (예: [('SPY', 0.5), ('QQQ', 0.5), ('GLD', 0.0)])
    """

    # ticker list 정의
    tickers = ['SPY', 'QQQ', 'GLD']

    # TIP 기준값 계산
    tip_momentum = calculate_momentum('TIP', ticker_prices.get('TIP', []), trade_date, caculate_month)

    # TIP 기준값이 음수인지 확인
    if tip_momentum is None or tip_momentum < 0:
        # TIP 기준값이 없거나 음수이면 모든 자산의 비중을 0으로 설정
        weights = {ticker: (0.0) for ticker in tickers}
    else:
        # 3개월 수익률 계산
        momentums = {}
        for ticker in tickers:
            momentums[ticker] = calculate_momentum(ticker, ticker_prices.get(ticker, []), trade_date, caculate_month)
        # 모멘텀 순위 계산 (내림차순)
        ranked_tickers = sorted(momentums, key=momentums.get, reverse=True)

        # 상위 2개 자산에 0.5 비중 할당, 나머지는 0
        weights = {}
        for ticker in tickers:
            if ticker in ranked_tickers[:2]:
                weights[ticker] = (0.5)
            else:
                weights[ticker] = (0.0)

    # 최종 결과: (ticker, weight) 형태의 튜플 리스트로 반환
    result = [(ticker, weights.get(ticker, 0.0)) for ticker in ['SPY', 'QQQ', 'GLD']]  # ticker 순서 정의
    return result

