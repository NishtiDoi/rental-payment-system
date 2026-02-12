from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://postgres:1234@127.0.0.1:5432/rental_payment_system",
    echo=True,
)
engine.connect()
print("connected")
