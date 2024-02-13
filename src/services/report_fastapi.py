from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from budget.models.models import Transaction, Session
from sqlalchemy import extract, func
from datetime import datetime, date

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/record/{user_id}", response_class=HTMLResponse)
async def read_record_html(request: Request, user_id: int):
    return templates.TemplateResponse("report.html", {"request": request, "user_id": user_id})


@app.get("/api/record/sum/{user_id}", response_class=JSONResponse)
async def get_records_sum(user_id: int):
    with Session() as session:
        query = session.query(
            func.sum(Transaction.amount).label("total_amount"),
            Transaction.status
        ).filter_by(user_id=user_id).group_by(Transaction.status).all()

    sums_by_status = {status: total_amount for total_amount, status in query}
    return JSONResponse(content=sums_by_status)


@app.get("/api/record/{user_id}", response_class=JSONResponse)
async def read_record_api(
    user_id: int,
    target_date: str = Query(None, description="Целевая дата в формате 'YYYY-MM'"),
    status: str = Query(None, description="Статус записей (Expenses, Income)"),
):
    with Session() as session:
        query = session.query(Transaction).filter_by(user_id=user_id)

        if target_date is not None:
            target_date = datetime.strptime(target_date, "%Y-%m")
            target_date = date(target_date.year, target_date.month, 1)

            query = query.filter(
                extract('year', func.to_date(Transaction.timestamp, 'DD-MM-YY HH24:MI')) == target_date.year,
                extract('month', func.to_date(Transaction.timestamp, 'DD-MM-YY HH24:MI')) == target_date.month
            )

        if status is not None:
            query = query.filter(Transaction.status.in_([status]))

        financial_records = query.all()

    if not financial_records:
        raise HTTPException(
            status_code=404,
            detail=f"Для пользователя {user_id} не найдено финансовых записей за {target_date.year}-{target_date.month}"
        )

    records_json = [
        {
            "username": record.username,
            "user_message": record.user_message,
            "product": record.product,
            "price": record.price,
            "quantity": record.quantity,
            "status": record.status,
            "amount": record.amount,
            "timestamp": record.timestamp,
        }
        for record in financial_records
    ]

    return JSONResponse(content=records_json)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
