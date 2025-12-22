"""LangChain agent setup for Paradise voice agent."""

import os
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.tools import StructuredTool, tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
from rag.retriever import create_vector_store, get_retriever
from tools.flights import get_flight_prices
from tools.places import search_places


class ToolCallCallbackHandler(BaseCallbackHandler):
    """Callback handler to log tool calls and agent actions."""
    
    def __init__(self, announcement_callback=None):
        """Initialize with optional announcement callback.
        
        announcement_callback: sync function(text: str) -> None
            Called to queue announcements for async processing.
        """
        super().__init__()
        self.announcement_callback = announcement_callback
    
    def on_agent_action(self, action: AgentAction, **kwargs) -> None:
        """Called when agent decides to use a tool."""
        
        announcement = None
        if action.tool == "retrieve_travel_info":
            query = action.tool_input.get("query", "travel information")
            announcement = f"Let me check my travel archives for information about {query}..."
        elif action.tool == "get_flight_prices":
            departure = action.tool_input.get("departure", "your departure city")
            arrival = action.tool_input.get("arrival", "your destination")
            announcement = f"Let me look up flight prices from {departure} to {arrival} for you..."
        elif action.tool == "search_places":
            query = action.tool_input.get("query", "places")
            location = action.tool_input.get("location", "")
            if location:
                announcement = f"Let me search for some great {query} in {location} for you..."
            else:
                announcement = f"Let me search for some great {query} for you..."
        
        if announcement and self.announcement_callback:
            try:
                self.announcement_callback(announcement)
            except Exception as e:
                pass
    
    def on_agent_finish(self, finish: AgentFinish, **kwargs) -> None:
        """Called when agent finishes."""
        pass
    
    def on_tool_start(self, serialized: dict, input_str: str, **kwargs) -> None:
        """Called when tool starts executing."""
        pass
    
    def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when tool finishes executing."""
        pass


def create_rag_tool(retriever):
    """Create a RAG tool that wraps the retriever for agentic RAG."""
    @tool
    def retrieve_travel_info(query: str) -> str:
        """Retrieve travel information from the travel guide knowledge base.
        
        Use this tool when users ask about travel destinations, places to visit,
        things to do, or need information from the travel archives.
        This searches the uploaded travel PDFs and travel guides.
        
        Args:
            query: The search query about travel destinations, activities, or places
        """
        docs = retriever.invoke(query)
        if not docs:
            return "No relevant travel information found in the archives."
        
        result = "\n\n".join([
            f"Source: {doc.metadata.get('source', 'Travel Guide')}\nContent: {doc.page_content}"
            for doc in docs
        ])
        return result
    
    return retrieve_travel_info


def create_tools():
    """Create LangChain tools for the agent."""
    flight_tool = StructuredTool.from_function(
        func=get_flight_prices,
        name="get_flight_prices",
        description="""Get flight prices between two cities using SerpAPI.
        
        REQUIRED PARAMETERS (ALL must be provided before calling):
        - departure: Departure city/airport code (REQUIRED - ask user if not provided)
        - arrival: Arrival city/airport code (REQUIRED - ask user if not provided)
        - date: Departure date in YYYY-MM-DD format (REQUIRED - ask user if not provided)
        
        DO NOT call this tool if any required parameter is missing. Ask the user for missing information first.
        DO NOT infer or assume cities or dates. Only use information explicitly stated by the user.
        
        DATE RANGE HANDLING:
        - If user provides date range (e.g., "December 3rd to December 6th"):
          → Extract BOTH dates: date="2026-12-03", return_date="2026-12-06", flight_type="round-trip"
        - If user provides single date:
          → Use date="2026-12-03", flight_type="one-way" (default)
          → OR ask user "One-way or round trip?" if unsure
        - If user wants round trip but only gave one date:
          → Ask "What's your return date?" BEFORE calling this tool
        
        Examples of when to call:
        - User: "I need flights from [city] to [city] on [date]" → CALL IMMEDIATELY (all info provided)
        - User: "Flights from [city] to [city], [date] to [date]" → CALL IMMEDIATELY (round-trip, all info provided)
        - User: "I'm going to [city]" → DON'T call yet (missing departure and date) - ASK for missing info
        
        Parameters: 
        - departure (city/airport code, REQUIRED)
        - arrival (city/airport code, REQUIRED) 
        - date (YYYY-MM-DD, REQUIRED, outbound date)
        - return_date (YYYY-MM-DD, optional, for round trips)
        - flight_type ("one-way" or "round-trip", optional, auto-detected from dates)
        - currency (default: USD)""",
    )
    
    places_tool = StructuredTool.from_function(
        func=search_places,
        name="search_places",
        description="""Search for places like cafes, restaurants, hotels, or attractions using Google Places API.
        
        IMMEDIATELY call this tool when:
        - User confirms a destination and asks about places to visit, eat, or stay
        - User asks for places in a specific location → CALL NOW
        - User confirms destination and asks for suggestions → CALL NOW
        
        REQUIRED: location parameter should be provided. If user hasn't specified location, ask "Which city are you looking for places in?" before calling.
        Extract location from conversation context only if explicitly mentioned by the user.
        
        Examples of when to call:
        - User: "What are good restaurants in [city]?" → CALL IMMEDIATELY (location provided)
        - User: "I'm going to [city], where should I stay?" → CALL IMMEDIATELY (location provided)
        - User: "Show me cafes" (without location) → ASK for location first, then call
        
        Parameters: query (search query like "restaurants", "cafes", "hotels"), location (required - ask user if not provided), place_type (optional: cafe, restaurant, hotel, tourist_attraction), max_results (default: 5)""",
    )
    
    return [flight_tool, places_tool]


def create_paradise_agent(llm: ChatOpenAI, use_rag: bool = True, use_tools: bool = True, announcement_callback=None):
    """Create a LangChain agent with Paradise persona, optional RAG, and tools."""
    
    system_prompt = """You are Paradise, a chill travel planning buddy. Keep responses EXTREMELY SHORT.

CRITICAL: NEVER assume or infer missing information. ALWAYS ask the user.

RESPONSE RULES:
- 1 sentence max. 2 sentences ONLY if absolutely necessary.
- NO lists, NO bullet points, NO long explanations.
- When you have multiple results, say: "Found 5 hotels. Want the top 3?" then wait for user response.
- After providing info, IMMEDIATELY ask a follow-up question.
- Speak like texting a friend: "Got it!", "Sure!", "Let me check...", "Nice!", "Cool!"

REQUIRED INFORMATION CHECKLIST:
- Before calling get_flight_prices: MUST have departure city, arrival city, AND date
  → If missing departure: "Where are you departing from?"
  → If missing arrival: "Where are you going?"
  → If missing date: "What are your travel dates?"
- Before calling search_places: MUST have location
  → If missing: "Which city are you looking for places in?"

TOOL USAGE - BE PROACTIVE BUT COMPLETE:
- When user gives ALL required info → IMMEDIATELY call tool
- When user gives PARTIAL info → Ask for missing pieces BEFORE calling tool
- DO NOT infer cities, dates, or any information from context unless explicitly stated
- DO NOT use examples from tool descriptions as actual data - those are just examples

EXAMPLES OF GOOD VS BAD:
❌ BAD: "Here are some hotel options: 1. Hilton Kyoto - 4.5 stars, 416 Shimomaruyacho. 2. ORIENTAL HOTEL KYOTO ROKUJO - 4.2 stars..."
✅ GOOD: "Found 5 great hotels. Want me to share the top 3?"

❌ BAD: "Flights info didn't come through, but here are some hotel options..."
✅ GOOD: "Flight search needs your return date. Is this a round trip?"

❌ BAD: "I found several flight options for you. The cheapest one is $850 with 2 stops..."
✅ GOOD: "Found flights starting at $850. Want details?"

FOLLOW-UP QUESTIONS (ALWAYS ASK AFTER PROVIDING INFO):
- After flight search: "Want me to check hotels next?"
- After hotel results: "Need restaurant recommendations too?"
- After any info: "Anything else you need?"
- If missing info: "What's your [missing info]?" (e.g., "What's your return date?")

MEMORY:
- ALWAYS remember what user told you earlier (destination, dates, preferences)
- Reference previous conversation: "You mentioned [city] earlier..."
- But DO NOT assume - if user hasn't explicitly stated something, ask

WORKFLOW:
1. Destination? → Use search_places if confirmed (ask for location if missing)
2. Dates + cities? → Use get_flight_prices immediately (ask for missing info first)
3. Things to do? → Use retrieve_travel_info
4. After every response → Ask a follow-up question"""

    tools = create_tools() if use_tools else []
    
    if use_rag:
        index_name = os.getenv("PINECONE_INDEX_NAME", "paradise-travel-index")
        vector_store = create_vector_store(index_name)
        retriever = get_retriever(vector_store, k=4)
        
        rag_tool = create_rag_tool(retriever)
        if use_tools:
            tools = [rag_tool] + tools
        else:
            tools = [rag_tool]
        
        if tools:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            agent = create_openai_tools_agent(llm, tools, prompt)
            callback_handler = ToolCallCallbackHandler(announcement_callback=announcement_callback)
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                callbacks=[callback_handler],
            )
            
            return agent_executor
        else:
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=memory,
                verbose=True,
            )
            
            chain.combine_docs_chain.llm_chain.prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ])
            
            return chain
    else:
        if use_tools and tools:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            agent = create_openai_tools_agent(llm, tools, prompt)
            callback_handler = ToolCallCallbackHandler()
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                callbacks=[callback_handler],
            )
            return agent_executor
        else:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ])
            
            chain = prompt | llm
            return chain


async def get_agent_response(chain, user_input: str, chat_history: list = None, use_rag: bool = True, use_tools: bool = True, announcement_callback=None):
    """Get response from the agent."""
    if isinstance(chain, AgentExecutor):
        if chat_history is None:
            chat_history = []
        
        formatted_history = []
        for msg in chat_history:
            if msg["role"] == "user":
                formatted_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_history.append(AIMessage(content=msg["content"]))
        
        result = await chain.ainvoke({
            "input": user_input,
            "chat_history": formatted_history,
        })
        return result.get("output", str(result))
    elif use_rag:
        result = await chain.ainvoke({"question": user_input})
        return result["answer"]
    else:
        if chat_history is None:
            chat_history = []
        
        formatted_history = []
        for msg in chat_history:
            if msg["role"] == "user":
                formatted_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_history.append(AIMessage(content=msg["content"]))
        
        response = await chain.ainvoke({
            "input": user_input,
            "chat_history": formatted_history,
        })
        
        return response.content

