from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from models import FinancialRecord, Session
from report_generator import generate_html_report

app = FastAPI()


@app.get("/record/{user_id}", response_class=HTMLResponse)
async def read_record(user_id: int):
    session = Session()
    financial_records = session.query(FinancialRecord).filter_by(user_id=user_id).all()

    if not financial_records:
        raise HTTPException(status_code=404, detail="Для указанного пользователя не найдено финансовых записей.")

    html_content = generate_html_report(financial_records)

    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
