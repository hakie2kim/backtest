from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

def calculate_trade_day(start_year: int, start_month: int, trade_date: int) -> date:
    """
    매매일을 계산합니다.
    Args:
        start_year: 시작 년도
        start_month: 시작 월
        trade_date: 매매일 (일)
    Returns:
        계산된 매매일 (date 객체)
    """
    try:
        # 매매일을 해당 월의 trade_date로 설정
        trade_day = date(start_year, start_month, trade_date)
    except ValueError:
        # 해당 월에 trade_date 일이 없는 경우, 월말일로 설정
        import calendar
        last_day = calendar.monthrange(start_year, start_month)[1]
        trade_day = date(start_year, start_month, last_day)

    # 매매일이 주말인 경우, 가장 가까운 이전 평일로 변경
    trade_day = find_nearest_weekday(trade_day)

    return trade_day


def calculate_past_trade_day(start_year: int, start_month: int, trade_date: int, caculate_month: int) -> date:
    """
    3개월 전 매매일을 계산합니다.
    Args:
        start_year: 시작 년도
        start_month: 시작 월
        trade_date: 매매일 (일)
        caculate_month: 비중 계산 기준 개월 수
    Returns:
        계산된 3개월 전 매매일 (date 객체)
    """
    try:
        # 3개월 전 날짜 계산
        past_month = start_month - caculate_month
        past_year = start_year
        if past_month <= 0:
            past_month += 12
            past_year -= 1

        past_trade_day = date(past_year, past_month, trade_date + 1)
    except ValueError:
        # 해당 월에 trade_date + 1 일이 없는 경우, 월말일로 설정
        import calendar
        last_day = calendar.monthrange(past_year, past_month)[1]
        past_trade_day = date(past_year, past_month, last_day)

    # 매매일이 주말인 경우, 가장 가까운 이전 평일로 변경
    past_trade_day = find_nearest_weekday(past_trade_day)

    return past_trade_day


def find_nearest_weekday(date_val: date) -> date:
    """
    주어진 날짜에서 가장 가까운 평일을 찾습니다.
    Args:
        date_val: 기준 날짜 (date 객체)
    Returns:
        가장 가까운 평일 (date 객체)
    """
    if date_val.weekday() >= 5:  # 토요일 또는 일요일인 경우
        if date_val.weekday() == 5:  # 토요일
            date_val -= relativedelta(days=1)  # 금요일
        else:  # 일요일
            date_val += relativedelta(days=1)  # 월요일
    return date_val
