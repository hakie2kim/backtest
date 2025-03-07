from app.app.utils.date import find_nearest_weekday
from datetime import date
from dateutil.relativedelta import relativedelta


def calculate_momentum(ticker: str, ticker_prices: dict, trade_date: date, caculate_month: int) -> float:
    """특정 ticker의 모멘텀 (3개월 수익률) 을 계산합니다."""

    # 매매일 3개월 전 날짜 계산
    past_date = trade_date - relativedelta(months=caculate_month)
    past_date = find_nearest_weekday(past_date)

    # 매매일, 매매일 3개월 전 가격 구하기
    trade_price = None
    past_price = None

    # ticker_prices[ticker] 존재 여부 먼저 확인
    if ticker in ticker_prices and ticker_prices[ticker]:
        prices = ticker_prices[ticker]

        # trade_date에 해당하는 가격 조회
        trade_price = next((price for price in prices if price.date == trade_date), None)

        # past_date에 해당하는 가격 조회
        past_price = next((price for price in prices if price.date == past_date), None)

    # 매매일, 매매일 3개월 전 값 존재하지 않을 시 None 반환
    if past_price is None or trade_price is None:
        return None

    # 3개월 수익률 계산: (매매일 SPY 값 / 매매일 3개월 전 SPY 값) - 1
    momentum = (trade_price.price / past_price.price) - 1
    return float(momentum)

