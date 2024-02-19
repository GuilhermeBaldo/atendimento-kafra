from typing import List

from langchain.agents import initialize_agent, load_tools, AgentType, AgentExecutor
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain_community.document_loaders.base import Document
from langchain_community.document_loaders import ApifyDatasetLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.schema.vectorstore import VectorStoreRetriever

from atendimento_kafra.chat.messages.chat_message_repository import ChatMessageRepository
from atendimento_kafra.chat.models import MessageSender, ChatMessage
from atendimento_kafra import settings

def _create_bro_wiki_retriever() -> VectorStoreRetriever:
    loader = ApifyDatasetLoader(
        dataset_id="ef4x5emShPlFoGFPl",
        dataset_mapping_function=lambda dataset_item: Document(
            page_content=dataset_item["text"], metadata={"source": dataset_item["url"]}
        ),
    )
    vectorstore = VectorstoreIndexCreator().from_loaders([loader])

    return vectorstore.vectorstore.as_retriever()

def _get_bro_wiki_tool() -> Tool:
    return create_retriever_tool(
        _create_bro_wiki_retriever(),
        "bro_wiki_retriever",
        "Procura e retorna informações sobre bRO (Brazilian Ragnarok Online) na sua wiki.",
    )

browiki_tool = _get_bro_wiki_tool()

class AgentFactory:

    def __init__(self):
        self.chat_message_repository = ChatMessageRepository()

    async def create_agent(
        self,
        tool_names: List[str],
        chat_id: str = None,
        streaming=False,
        callback_handlers: List[BaseCallbackHandler] = None,
    ) -> AgentExecutor:
        # Instantiate the OpenAI LLM
        llm = ChatOpenAI(
            temperature=0,
            openai_api_key=settings.openai_api_key,
            streaming=streaming,
            callbacks=callback_handlers,
        )

        # Load the Tools that the Agent will use
        tools = load_tools(tool_names, llm=llm)

        tools.append(browiki_tool)

        # Load the memory and populate it with any previous messages
        memory = await self._load_agent_memory(chat_id)

        # Initialize and return the agent
        return initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
            agent_kwargs={
                'system_message': """
Você é uma funcionária Kafra, seu papel é responder perguntas de jogadores sobre o jogo Ragnarok Online.

Você deve sempre se apresentar na primeira interação.

Você pode utilizar apenas informações da sua wiki para isso.

Suas respostas devem ser completas, esclarescendo ao máximo o tópico perguntado pelo jogador.
""",
                #'human_message':SUFFIX,
                #'template_tool_response':TEMPLATE_TOOL_RESPONSE,
            }
        )

    async def _load_agent_memory(
        self,
        chat_id: str = None,
    ) -> ConversationBufferMemory:
        if not chat_id:
            return ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # Create the conversational memory for the agent
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # Load the messages for the chat_id from the DB
        chat_messages: List[ChatMessage] = await self.chat_message_repository.get_chat_messages(chat_id)

        # Add the messages to the memory
        for message in chat_messages:
            if message.sender == MessageSender.USER.value:
                # Add user message to the memory
                memory.chat_memory.add_user_message(message.content)
            elif message.sender == MessageSender.AI.value:
                # Add AI message to the memory
                memory.chat_memory.add_ai_message(message.content)

        return memory
