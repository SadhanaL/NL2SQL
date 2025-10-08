from langchain_openai import ChatOpenAI

def get_llm():
    """
    Instantiate and return a configured ChatOpenAI language model.

    Returns
    -------
    ChatOpenAI
        An instance of ChatOpenAI using the GPT-4.1 model, temperature 0.0,
        and response format set to JSON object.
    """
    llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0
)
    return llm
