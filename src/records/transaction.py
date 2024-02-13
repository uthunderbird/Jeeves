import typing

from pydantic.v1 import BaseModel
from pydantic.v1 import Field


class TransactionRecord(BaseModel):
    product: str = Field(description="The product or service identified or the source of income.")
    quantity: int = Field(default=1, description="The quantity of products, defaulting to 1 if unspecified.")
    price: float = Field(description="The unit price of the product or service, without currency. convert 'k' or 'к' to thousands")
    status: typing.Literal['spent', 'gained', 'adjustment'] = Field(
        description="The status indicating whether the amount was spent or gained.",
    )
    currency: str = Field(description="Three-letter currency code if currency is specified. `default` otherwise.")
    category: str = Field(description="The most relevant category from user category list. `Unknown` otherwise.")

    @property
    def amount(self) -> float:
        return self.price * self.quantity
