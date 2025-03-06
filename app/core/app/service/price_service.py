import pandas as pd
from app.models.price import Price
from app.core.database import SessionLocal
from app.core.config import settings

def insert_price_data(file_path: str):
    sheet_name = settings.EXCEL_SHEET_NAME
    df = pd.read_excel(file_path, sheet_name=sheet_name) # '가격' 시트 이름
    df['date'] = pd.to_datetime(df['date'])

    db = SessionLocal()
    try:
        for _, row in df.iterrows():
            price = Price(
                date=row['date'].to_pydatetime(),
                ticker=row['ticker'],
                price=row['price']
            )
            db.add(price)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
