import requests
from bs4 import BeautifulSoup
from datetime import datetime
from app.models.price import Price
from app.core.database import SessionLocal

def update_price(ticker: str):
    url = f"https://finance.yahoo.com/quote/{ticker}/history"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 가격 추출: <span class="base yf-ipw1h0" data-testid="qsp-price">
        price_span = soup.find("span", class_="base yf-ipw1h0", attrs={"data-testid": "qsp-price"})

        if price_span:
            price_str = price_span.text
            price = float(price_str.replace(",", ""))
        else:
            print(f"Could not find price for {ticker}")
            return  # 가격을 찾을 수 없으면 함수 종료

        # 미국 EST 18시에 작동 -> 오늘 날짜
        date = datetime.now().date()

        db = SessionLocal()
        try:
            existing_price = db.query(Price).filter(Price.ticker == ticker, Price.date == date).first()

            if existing_price:
                existing_price.price = price
            else:
                new_price = Price(ticker=ticker, date=date, price=price)
                db.add(new_price)

            db.commit()
            print(f"Updated price for {ticker} on {date}")

        except Exception as e:
            db.rollback()
            print(f"Error updating price for {ticker}: {e}")
        finally:
            db.close()

    except requests.exceptions.RequestException as e:
        print(f"Request failed for {ticker}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred for {ticker}: {e}")

# TODO: Cron 스케줄링
if __name__ == "__main__":
    tickers = ["SPY", "QQQ", "GLD", "TIP", "BIL"]
    for ticker in tickers:
        update_price(ticker)