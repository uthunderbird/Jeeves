from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.language_models import LLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from records.transaction import TransactionRecord

# Pydantic model for structured output with descriptions


output_parser = PydanticOutputParser(pydantic_object=TransactionRecord)

# Split prompt into a valid ChatPromptTemplate
chat_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Hello, you will receive a message related to a user's budget. "
            # "Identify 4 parameters: entity (product/service or source of income), "
            # "quantity of products (default to 1 if unspecified), "
            # "amount of money (convert 'k' or 'к' to thousands), "
            # "and status (Expenses if spent, Income if gained). "
            ""
            "{format_instructions}"
        ),
        (
            "user",
            "{message}",
        ),
    ],
)

chat_prompt_template = chat_prompt_template.partial(
    format_instructions=output_parser.get_format_instructions(),
)


# Chain construction
def make_chain(model: LLM) -> RunnableSerializable:
    return (
        chat_prompt_template
        | model
        | output_parser
    )


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    model = ChatOpenAI(model="gpt-4-turbo-preview")
    chain = make_chain(model)
    # Invoke the chain with a sample text
    result = chain.invoke({'message': "два банана по 1к"})
    print(result.json())
