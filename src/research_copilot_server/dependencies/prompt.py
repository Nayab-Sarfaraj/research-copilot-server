from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

user_query_prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a research assistant. Generate accurate and concise research reports."
    ),
    HumanMessagePromptTemplate.from_template(
        "{query}"
    ),
])