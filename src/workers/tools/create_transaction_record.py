from langchain_core.language_models import LLM
from langchain_core.tools import StructuredTool
from pydantic.v1 import BaseModel
from pydantic.v1 import Field

from workers.chains.transaction_structurer import make_chain as make_structurer_chain


class CreateRecordSchema(BaseModel):
    user_message_text: str = Field(
        description='user message with information that should be parsed'
    )


def make_tool(model: LLM):
    def parse_record(text: str) -> dict:
        """Useful to transform raw string about financial operations into structured JSON"""
        chain = make_structurer_chain(model)
        return chain.invoke({'message': text}).model_dump()

    return StructuredTool.from_function(
        func=parse_record,
        name='parse_record',
        return_direct=True,
        description="""Useful to transform raw string about financial operations into structured JSON""",
        args_schema=CreateRecordSchema,
    )
