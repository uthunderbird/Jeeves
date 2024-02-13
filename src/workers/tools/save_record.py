from langchain_core.tools import StructuredTool
from pydantic.v1 import BaseModel
from pydantic.v1 import Field


class SaveRecordSchema(BaseModel):
    product: str = Field(description='entity')
    price: int = Field(description='price')
    quantity: int = Field(description='quantity')
    status: str = Field(description='status')
    amount: int = Field(description='amount')


def save_record(**data_dict):

    session = Session()

    financial_record = Transaction(
        user_id=self.full_message.from_user.id,
        username=self.full_message.from_user.username,
        user_message=self.full_message.text,
        product=data_dict.get("product"),
        price=data_dict.get("price"),
        quantity=data_dict.get("quantity"),
        status=data_dict.get("status"),
        amount=data_dict.get("amount")
    )

    session.add(financial_record)
    session.commit()
    session.close()

    return 'Structured JSON record saved successfully'


StructuredTool.from_function(
    func=save_record,
    name='save_record',
    description="""Useful to save structured dict record into database""",
    args_schema=SaveRecordSchema,
)