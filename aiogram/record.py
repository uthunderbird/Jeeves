import os

from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class Record(BaseModel):
    original_message: str = Field(description='input record message')
    product: str = Field(description='entity')
    price: int = Field(description='price')
    quantity: int = Field(description='quantity')
    status: str = Field(description='status')
    amount: int = Field(description='amount')
    timestamp: str = Field(description='timestamp')

load_dotenv()

OPENAI_MODEL = 'gpt-4'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PROMPT_RECORD_INFO = """
        system" "Hello, in the end of this prompt you will get a message,
         "it's going contain text about user's budget. "
         "You should identify 4 parameters in this text: "
         "first is entity (product or service if it's about spending money) "
         "or source if it's about gaining money, "
         "second is the quantity of products, "
         "third is the amount of money gained or spent on this product, "
         "fourth is status gained/spent. "
         "Your answer should be like this: "
         "Product: (here should be the product or service you identified from the message "
         "or source of money if it was gained) "
         "Quantity: (here should be quantity of products or if there is no quantity "
         "you should fill 1 in here) "
         "Price: here should be unit price of a product or service of money mentioned in the message, but "
         "don't mention the currency, only number, it's possible that there will "
         "be slang expressions like 'k' referring to number a thousand, keep it in "
         "mind and save it as a number. For example if there is '2k' or  '2к' it "
         "means that you should write 2000 "
         "Status: (here should be status you got from the message, whether it was"
         "spent or gained, if spent - write 'Expenses', if gained - write 'Income' "
         "Amount: (there should be a sum here, the sum is equal to the quantity multiplied by the price)
         "Return it in dict format
         user message - {record_message},
         {format_instructions}
    """


def main():
    parser = PydanticOutputParser(pydantic_object=Record)

    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name=OPENAI_MODEL)
    message = HumanMessagePromptTemplate.from_template(
        template=PROMPT_RECORD_INFO,
    )
    chat_prompt = ChatPromptTemplate.from_messages([message])

    record = input("Enter your message: ")

    print("Generating response...")
    chat_prompt_with_values = chat_prompt.format_prompt(
        record_message=record, format_instructions=parser.get_format_instructions()
    )
    output = llm(chat_prompt_with_values.to_messages())
    record_message = parser.parse(output.content)

    print(f"product: {record_message.product}\nqty: {record_message.quantity}\nmessage: {record_message.original_message}\nprice: {record_message.price}\nstatus: {record_message.status}")


if __name__ == "__main__":
    main()
