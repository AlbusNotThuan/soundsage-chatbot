from typing import cast
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    PromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable, RunnableConfig, RunnablePassthrough
import chainlit as cl
from conversation_handler import ConversationHandler
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from typing import Dict, Any, Set, List

# Initialize environment and constants
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_PATH = "chroma_data/"

# Initialize conversation handler
conversation_handler = ConversationHandler()

class CustomLangchainCallbackHandler(cl.AsyncLangchainCallbackHandler):
    def __init__(self):
        super().__init__()
        self.run_ids = set()
        self.llm_runs = set()

    async def on_retriever_start(self, *args, **kwargs):
        pass

    async def on_llm_start(self, *args, **kwargs):
        pass

    async def on_chain_start(self, *args, **kwargs):
        pass

    async def on_tool_start(self, *args, **kwargs):
        pass

    async def on_chain_end(self, *args, **kwargs):
        pass

    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        pass

    async def on_llm_new_token(self, token: str, **kwargs):
        pass

    async def on_llm_end(self, response, **kwargs):
        run_id = kwargs.get("run_id", "")
        if run_id in self.llm_runs:
            self.llm_runs.remove(run_id)
            # super().on_llm_end(response, **kwargs)

    async def on_llm_error(self, error: Exception, **kwargs):
        run_id = kwargs.get("run_id", "")
        if run_id in self.llm_runs:
            self.llm_runs.remove(run_id)
            super().on_llm_error(error, **kwargs)
    async def on_retriever_end(self, response, **kwargs):
        pass

system_template = """Use the following pieces of context and chat history to answer questions about music theory, piano playing, and music production.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Previous conversation:
{chat_history}

Context:
{context}

You are an experienced musician with:
- Deep understanding of music theory (harmony, counterpoint, form)
- Advanced piano performance skills
- Extensive knowledge of music production and recording techniques

When answering:
- Explain musical concepts clearly using both technical terms and simple analogies
- Reference standard music notation when relevant
- Suggest specific exercises or practice techniques
- Include DAW-specific advice for production questions
- Link concepts between theory, performance, and production
- Break down complex musical ideas into digestible steps

Remember to:
- Be precise with musical terminology
- Provide concrete, actionable advice
- Consider the student's skill level
- Reference appropriate musical examples
- Explain production concepts in both technical and artistic terms whenever applicable
"""


@cl.on_chat_start
async def on_chat_start():


    await cl.Message(content="Hello there, I am here to assist you on your path of understanding, playing and create music. What would you like to know?").send()

    # Generate new conversation
    conversation_id = conversation_handler.generate_conversation_id()
    cl.user_session.set("conversation_id", conversation_id)
    cl.user_session.set("message_history", [])

    # Initialize model and prompts
    model = ChatOpenAI(
        streaming=True,
        model="gpt-4",
        temperature=0.5,
    )

    # Set up the prompt templates
    review_prompt_template = await setup_prompt_template()
    
    # Initialize vector store
    reviews_vector_db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=OpenAIEmbeddings()
    )
    reviews_retriever = reviews_vector_db.as_retriever(k=10)

    # Create chain
    chain = create_chain(review_prompt_template, model, reviews_retriever)
    cl.user_session.set("chain", chain)

@cl.on_message
async def on_message(message: cl.Message):
    try:
        chain = cl.user_session.get("chain")
        message_history = cl.user_session.get("message_history", [])
        conversation_id = cl.user_session.get("conversation_id")

        # Format history
        history_text = await conversation_handler.format_history(message_history)
        
        msg = cl.Message(content="")
        await msg.send()

        response_text = ""
        async for chunk in chain.astream(
            {
                "question": message.content,
                "chat_history": history_text
            },
            config=RunnableConfig(callbacks=[CustomLangchainCallbackHandler()]),
        ):
            await msg.stream_token(chunk)
            response_text += chunk

        # Update and persist conversation
        message_history.append({"type": "human", "content": message.content})
        message_history.append({"type": "ai", "content": response_text})
        await conversation_handler.save_messages(conversation_id, message_history)
        cl.user_session.set("message_history", message_history)

        await msg.update()
    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()




# Helper functions
async def setup_prompt_template():
    review_system_prompt = SystemMessagePromptTemplate(
        prompt=PromptTemplate(
            input_variables=["context", "chat_history"],
            template=system_template,
        )
    )
    
    review_human_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            input_variables=["question"],
            template="{question}",
        )
    )
    
    return ChatPromptTemplate(
        input_variables=["context", "question", "chat_history"],
        messages=[review_system_prompt, review_human_prompt],
    )

def create_chain(prompt_template, model, retriever):
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
        
    return (
        {
            "context": lambda x: format_docs(retriever.get_relevant_documents(x["question"])),
            "question": RunnablePassthrough(),
            "chat_history": RunnablePassthrough()
        }
        | prompt_template 
        | model 
        | StrOutputParser()
    )