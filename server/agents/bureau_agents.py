from langchain_core.prompts import ChatPromptTemplate

classifier_agent_schema = {
    "title": "classifier-bureaus",
    "description": "Description of tags characterizing a given architectural bureau for identification based on potential user-provided tags.",
    "type": "object",
    "properties": {
        "tags": {
            "description": "An array of tags (the number depends on the volume of information; do NOT include unnecessary tags).",
            "type": "array",
            "items": {
                "description": "A tag should consist of 1-3 words that can easily be converted into embeddings.\
Avoid obvious tags like [architecture, urban planning, etc.]; instead, focus on those that distinguish this bureau from others [do NOT include awards or specific projects in the tags].",
                "type": "string",
            },
            "minItems": 1,
            "maxItems": 5,
        }
    },
    "required": ["tags"],
}


writer_agent_schema = {
    "title": "writer-bureau",
    "description": "Analyze architectural bureaus from the BUREAUS block that match the user's request from INPUT. Provide descriptions for each bureau.",
    "type": "object",
    "properties": {
        "bureaus": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"description": "The name of the bureau.", "type": "string"},
                    "description": {
                        "description": "A brief description of the bureau and how it can assist the user with their request.",
                        "type": "string",
                    },
                },
                "required": ["name", "description"],
            },
            "maxItems": 5,
        }
    },
    "required": ["bureaus"],
}


prompt_writer = ChatPromptTemplate.from_messages(
    [("user", "INPUT: {input}"), ("assistant", "BUREAUS: {bureaus}")]
)


def prepare_bureaus(bureaus):
    return "\n---\n".join(
        [
            f"Name: {b['name']}\nYear and Country: {b['year']}, {b['country']}\nDescription: {b['description']}\nProjects: {b['projects']}\nAwards: {b['awards']}"
            for b in bureaus
        ]
    )


def generate_writer_agent(llm):
    return (
        {"input": lambda x: x["input"], "bureaus": lambda x: x["bureaus"]}
        | prompt_writer
        | llm.with_structured_output(writer_agent_schema)
    )


def generate_tags_agent(llm):
    return llm.with_structured_output(classifier_agent_schema)
