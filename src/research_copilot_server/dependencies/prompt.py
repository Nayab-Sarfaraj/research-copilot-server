from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

user_query_prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(
        content="You are a research assistant. Generate accurate and concise research reports."
    ),
    HumanMessage(content="{query}")
])