from research_copilot_server.dependencies.model  import model
from research_copilot_server.dependencies.prompt import user_query_prompt_template
from research_copilot_server.schema.report import model_output

async def generate_response(query: str):
    prompt = user_query_prompt_template.invoke({
        "query": query
    })

    structured_model = (
        model
        .with_structured_output(model_output)
        .with_retry(
            stop_after_attempt=3,
            wait_exponential_jitter=True,
        )
    )

    result = await structured_model.ainvoke(prompt)

    return result