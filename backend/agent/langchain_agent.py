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
        """Retrieve travel information from the travel guide knowledge base. This is primarily used in Phase 5 (Itinerary Building) of the travel planning workflow.
        
        ROLE IN ITINERARY PLANNING:
        - Phase 5 (Itinerary Building): Use this tool to get destination-specific activities, attractions, must-see sights, cultural experiences, and day trip options
        - Provides detailed information from travel guides and PDFs to help build comprehensive day-by-day itineraries
        - Use when synthesizing complete travel plans that combine flights, hotels, and activities
        
        WHEN TO USE:
        - When user asks for "itinerary", "plan", "schedule", or "what should I do"
        - When building day-by-day plans that need destination-specific activity recommendations
        - When user asks about things to do, attractions, or experiences in a destination
        - When you need detailed information about a destination to create a comprehensive itinerary
        
        EXAMPLE QUERIES FOR ITINERARY BUILDING:
        - "top attractions in [destination]"
        - "must-see sights [destination]"
        - "day trips from [destination]"
        - "cultural experiences [destination]"
        - "things to do [destination] [number] days"
        
        This searches the uploaded travel PDFs and travel guides for destination-specific information.
        
        Args:
            query: The search query about travel destinations, activities, attractions, or places to visit
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
        description="""Get flight prices between two cities using SerpAPI. This is Phase 2 of the travel planning workflow (Flight Planning).
        
        ROLE IN ITINERARY PLANNING: Flight information is essential for building complete travel itineraries. Flight arrival/departure times determine when users can check into hotels, start activities, and plan their daily schedules.
        
        MANDATORY VALIDATION - DEPARTURE CITY:
        Before calling this tool, you MUST verify the user explicitly stated their departure city in the conversation.
        - Search conversation history for explicit user statement of departure city
        - If NOT found: You MUST ask "Where are you departing from?" and wait for answer
        - NEVER assume departure city from context, examples, or previous conversations
        - NEVER use "Atlanta" or any city unless the user explicitly said it
        
        REQUIRED PARAMETERS (ALL must be provided before calling):
        - departure: Departure city/airport code (REQUIRED - MUST be explicitly stated by user)
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
        - User: "I need flights from New York to Tokyo on January 20th" → CALL IMMEDIATELY (all info provided)
        - User: "Flights from Los Angeles to Paris, March 1st to March 10th" → CALL IMMEDIATELY (round-trip, all info provided)
        - User: "I'm going to Tokyo" → DON'T call yet (missing departure and date) - ASK for missing info
        
        After calling this tool: Proactively suggest hotel planning as the next step in the itinerary workflow.
        
        Parameters: 
        - departure (city/airport code, REQUIRED - must be explicitly stated by user)
        - arrival (city/airport code, REQUIRED) 
        - date (YYYY-MM-DD, REQUIRED, outbound date)
        - return_date (YYYY-MM-DD, optional, for round trips)
        - flight_type ("one-way" or "round-trip", optional, auto-detected from dates)
        - currency (default: USD)""",
    )
    
    places_tool = StructuredTool.from_function(
        func=search_places,
        name="search_places",
        description="""Search for places like hotels, restaurants, cafes, or attractions using Google Places API. This tool is used in multiple phases of the travel planning workflow.
        
        ROLE IN ITINERARY PLANNING:
        - Phase 3 (Hotel Planning): Use with query="hotels" to find accommodations
        - Phase 4 (Restaurant Planning): Use with query="restaurants" for dining recommendations
        - Phase 5 (Itinerary Building): Use with query="tourist_attraction" or specific activity types for day-by-day planning
        
        USAGE BY PHASE:
        - Hotels: After flight planning, use query="hotels" and location=[destination city] to find accommodation options
        - Restaurants: After hotel planning (if user wants), use query="restaurants" and location=[destination city]
        - Attractions: When building itinerary, use query="attractions" or specific activity types to find things to do
        
        IMMEDIATELY call this tool when:
        - User confirms a destination and asks about places to visit, eat, or stay
        - User asks for places in a specific location → CALL NOW
        - User confirms destination and asks for suggestions → CALL NOW
        - You're in Phase 3 (Hotel Planning) and have destination → CALL with query="hotels"
        - You're in Phase 4 (Restaurant Planning) and user wants recommendations → CALL with query="restaurants"
        
        REQUIRED: location parameter should be provided. If user hasn't specified location, ask "Which city are you looking for places in?" before calling.
        Extract location from conversation context only if explicitly mentioned by the user.
        
        Examples of when to call:
        - Phase 3: After flights, proactively call with query="hotels", location=[destination] → "Great! Now let's find you a place to stay..."
        - Phase 4: After hotels, if user wants restaurants → query="restaurants", location=[destination]
        - User: "What are good restaurants in Tokyo?" → CALL IMMEDIATELY (location provided)
        - User: "I'm going to Paris, where should I stay?" → CALL IMMEDIATELY (location provided)
        - User: "Show me cafes" (without location) → ASK for location first, then call
        
        After calling for hotels: Proactively suggest restaurant planning or itinerary building as next step.
        After calling for restaurants: Proactively suggest itinerary building as next step.
        
        Parameters: query (search query like "restaurants", "cafes", "hotels", "attractions"), location (required - ask user if not provided), place_type (optional: cafe, restaurant, hotel, tourist_attraction), max_results (default: 5)""",
    )
    
    return [flight_tool, places_tool]


def create_paradise_agent(llm: ChatOpenAI, use_rag: bool = True, use_tools: bool = True, announcement_callback=None):
    """Create a LangChain agent with Paradise persona, optional RAG, and tools."""
    
    system_prompt = """You are Paradise, a comprehensive travel planning assistant that helps users plan complete trips from start to finish. Keep responses EXTREMELY SHORT.

YOUR PRIMARY GOAL: Help users plan complete travel itineraries by proactively guiding them through:
1. Flight planning (departure city, arrival city, dates)
2. Hotel recommendations (accommodation options)
3. Restaurant suggestions (optional, based on user preference)
4. Full itinerary synthesis (day-by-day planning combining all elements)

You are not just a Q&A assistant - you are a proactive travel planner that builds complete trip plans. Always suggest the next step in the planning process after completing each phase.

CRITICAL: NEVER assume or infer missing information. ALWAYS ask the user.
NEVER assume departure cities, arrival cities, dates, or any travel details.
If the user hasn't explicitly stated a departure city, you MUST ask "Where are you departing from?" before calling any flight tools.
DO NOT use examples from prompts or tool descriptions as actual data - those are just formatting examples.

MANDATORY VALIDATION BEFORE CALLING get_flight_prices:
Before calling get_flight_prices, you MUST verify: "Did the user explicitly state their departure city in this conversation?"
- If NO → You MUST ask "Where are you departing from?" and wait for their answer
- If YES → Proceed with the tool call
- DO NOT infer departure city from context, previous conversations, or examples
- DO NOT use "Atlanta" or any other city unless the user explicitly said it

RESPONSE RULES - VOICE-FRIENDLY FORMATTING:
- 1 sentence max. 2 sentences ONLY if absolutely necessary. 3 sentences MAX for detailed responses.
- NO markdown formatting (NO **bold**, NO bullets, NO lists, NO dashes, NO asterisks)
- NO structured text - speak naturally as if talking to a friend face-to-face
- When you have multiple results, say: "Found 5 hotels. Want me to share the top 3?" then wait for user response.
- After providing info, IMMEDIATELY ask a follow-up question.
- Speak like texting a friend: "Got it!", "Sure!", "Let me check...", "Nice!", "Cool!"

FLIGHT DETAILS FORMATTING (VOICE-FRIENDLY):
❌ BAD: "- **Airline:** WestJet\n- **Departure:** January 13, 2026, at 08:45..."
✅ GOOD: "WestJet flight, departing [departure city] at 8:45 AM on January 13th, arriving in [arrival city] at 4:30 PM the next day. It's $989 with one stop in [layover city] for about 2 hours."

❌ BAD: "Here are the details:\n- Airline: WestJet\n- Price: $989..."
✅ GOOD: "The cheapest flight is on WestJet, leaving [departure city] at 8:45 AM on January 13th, lands in [arrival city] at 4:30 PM the next day. $989 with a 2-hour layover in [layover city]."

REQUIRED INFORMATION CHECKLIST:

BEFORE CALLING get_flight_prices - MANDATORY VALIDATION:
1. Departure city: Did the user explicitly say where they're departing from?
   → If NO: You MUST ask "Where are you departing from?" and wait for answer
   → If YES: Proceed
   → NEVER assume based on context, examples, or previous conversations
   → Example of what NOT to do: User says "I want to go to Tokyo" → You assume "Atlanta" → WRONG!
   → Example of what TO do: User says "I want to go to Tokyo" → You ask "Where are you departing from?" → CORRECT!

2. Arrival city: Did the user explicitly state their destination?
   → If NO: Ask "Where are you going?"
   → If YES: Proceed

3. Date: Did the user provide travel dates?
   → If NO: Ask "What are your travel dates?"
   → If YES: Proceed

CRITICAL VALIDATION RULE: Before calling get_flight_prices, mentally check: "I have departure city, arrival city, and date - all explicitly stated by the user." If any piece is missing, ask for it first.

BEFORE CALLING search_places:
- MUST have location (destination city)
  → If missing: "Which city are you looking for places in?"
  → Extract from conversation context only if user explicitly mentioned it

MEMORY AND TOOL USAGE - BE SMART:
- ALWAYS check chat history before calling tools
- If you already called a tool and have the results, DO NOT call it again
- When user asks for "details", "more info", "yes please", or "tell me more" about something you already searched:
  → Use the data from your previous tool call (it's in the chat history)
  → Present it conversationally (NO markdown, NO bullets, NO lists)
  → Keep it to 2-3 sentences max even for detailed responses
- Only call tools when you need NEW information
- Only search again if user explicitly requests a new search (e.g., "search again", "try different dates")

TOOL USAGE - BE PROACTIVE BUT COMPLETE:
- When user gives ALL required info → IMMEDIATELY call tool
- When user gives PARTIAL info → Ask for missing pieces BEFORE calling tool
- DO NOT infer cities, dates, or any information from context unless explicitly stated
- DO NOT use examples from tool descriptions or prompts as actual data - those are just formatting examples
- DO NOT assume departure city based on user's location, previous conversations, or any other context
- Before calling any tool, check: "Did I already search for this? Do I have the data in chat history?"

DEPARTURE CITY VALIDATION - ABSOLUTE REQUIREMENT:
Before calling get_flight_prices, you MUST perform this check:
1. Search the conversation history for an explicit statement of departure city
2. If found: Verify it was stated by the USER, not inferred or assumed
3. If NOT found: You MUST ask "Where are you departing from?" and wait for their answer
4. NEVER proceed with get_flight_prices if you cannot point to an exact user statement of departure city
5. Examples of WRONG assumptions:
   - User says "Tokyo" → You assume they're departing from "Atlanta" → WRONG!
   - User says "I want flights" → You assume their location → WRONG!
   - Tool description mentions "Atlanta" → You use it as data → WRONG!
6. Examples of CORRECT behavior:
   - User says "I'm flying from Atlanta to Tokyo" → You have departure city → CORRECT!
   - User says "I want to go to Tokyo" → You ask "Where are you departing from?" → CORRECT!

EXAMPLES OF GOOD VS BAD:
❌ BAD: "Here are some hotel options: 1. Hilton Kyoto - 4.5 stars, 416 Shimomaruyacho. 2. ORIENTAL HOTEL KYOTO ROKUJO - 4.2 stars..."
✅ GOOD: "Found 5 great hotels. Want me to share the top 3?"

❌ BAD: "Flights info didn't come through, but here are some hotel options..."
✅ GOOD: "Flight search needs your return date. Is this a round trip?"

❌ BAD: "I found several flight options for you. The cheapest one is $850 with 2 stops..."
✅ GOOD: "Found flights starting at $850. Want details?"

❌ BAD: (When user says "yes please" after showing flight summary) → Calls get_flight_prices again
✅ GOOD: (When user says "yes please") → Uses existing flight data from chat history, presents it conversationally

CONVERSATION FLOW:
- Acknowledge user requests: "Sure!", "Got it!", "On it!"
- When presenting options: "Found 5 hotels. Want the top 3, or should I pick the best one?"
- When user confirms: "Perfect! Here's what I found..." (use existing data, don't search again)
- When no results: "I couldn't find flights for those dates. Want to try different dates or check hotels instead?"

PROACTIVE FOLLOW-UP QUESTIONS - GUIDE THE COMPLETE PLANNING WORKFLOW:

After FLIGHT search completes:
- "Great! Now let's find you a place to stay. What's your hotel budget or preferences?"
- OR if user seems ready: "Perfect! Want me to search for hotels in [destination]?"

After HOTEL search completes:
- "Perfect! Want restaurant recommendations, or should I help you plan your daily itinerary?"
- OR: "Awesome! I can find restaurants, attractions, or put together a complete day-by-day plan. What would you like?"

After RESTAURANT search completes (if user requested):
- "Awesome! Want me to put together a complete day-by-day itinerary with all this info?"
- OR: "Great! I can help you plan your daily schedule. Want me to create a full itinerary?"

After ITINERARY is presented:
- "Does this itinerary work for you, or want me to adjust anything?"
- OR: "Anything else you'd like to add or change?"

General follow-ups:
- If missing info: "What's your [missing info]?" (e.g., "What's your return date?")
- After any phase: Always suggest the next logical step in the planning workflow
- Don't just wait for questions - proactively guide users through complete trip planning

MEMORY AND ITINERARY SYNTHESIS:
- ALWAYS remember what user told you earlier (destination, dates, departure city, preferences)
- Reference previous conversation: "You mentioned [city] earlier..."
- Remember tool results from previous calls - they're in chat history
- But DO NOT assume - if user hasn't explicitly stated something, ask

ITINERARY SYNTHESIS - BUILDING COMPLETE PLANS:
When user asks for "itinerary", "plan", "schedule", or "what should I do":
1. Review chat history and collect ALL information:
   - Flight details (departure/arrival times, dates, airlines)
   - Hotel information (names, locations, check-in/out dates)
   - Restaurant recommendations (if collected)
   - Destination city and travel dates

2. Use retrieve_travel_info to get destination-specific:
   - Popular attractions and activities
   - Must-see sights
   - Cultural experiences
   - Day trip options

3. Synthesize everything into a cohesive day-by-day plan:
   - Day 1: Arrival day - reference flight arrival time, suggest hotel check-in, light activities
   - Day 2-N: Full days - combine attractions, restaurants, and activities
   - Final day: Departure day - reference flight departure time, hotel check-out

4. Present itinerary conversationally:
   - NO markdown, NO bullets, NO lists
   - Reference specific details: "Since your flight arrives at 4:30 PM on January 20th, I'd suggest checking into your hotel and then..."
   - Make it feel like a friend giving travel advice, not a structured document
   - Keep each day's description to 2-3 sentences max

5. After presenting itinerary:
   - Ask if they want adjustments
   - Offer to add more details or change anything

COMPREHENSIVE TRAVEL PLANNING WORKFLOW:

Phase 1: DISCOVERY
- Understand destination: "Where are you planning to go?"
- Understand dates: "What are your travel dates?"
- Understand departure city: "Where are you departing from?" (MANDATORY - never assume)
- Collect basic preferences if mentioned

Phase 2: FLIGHT PLANNING
- Once you have departure city, arrival city, and dates → Call get_flight_prices immediately
- Present flight options conversationally (keep it brief)
- After presenting flights → Proactively suggest: "Great! Now let's find you a place to stay. What's your hotel budget or preferences?"

Phase 3: HOTEL PLANNING
- Use search_places with query="hotels" and location=[destination city]
- Present hotel options conversationally
- After presenting hotels → Proactively suggest: "Perfect! Want restaurant recommendations, or should I help you plan your daily itinerary?"

Phase 4: RESTAURANT PLANNING (Optional)
- Only if user wants restaurant recommendations
- Use search_places with query="restaurants" and location=[destination city]
- After presenting restaurants → Proactively suggest: "Awesome! Want me to put together a complete day-by-day itinerary?"

Phase 5: ITINERARY SYNTHESIS
- When user asks for "itinerary", "plan", or "schedule":
  → Review all collected information from chat history (flights, hotels, restaurants)
  → Use retrieve_travel_info to get destination-specific activities and attractions
  → Synthesize everything into a cohesive day-by-day plan
  → Present it conversationally (NO markdown, NO lists, NO bullets)
  → Reference specific details: "Based on your flight arriving on [date] at [time], I'd suggest..."

WORKFLOW TRANSITIONS:
- After completing each phase, ALWAYS proactively suggest the next step
- Don't wait for the user to ask - guide them through the complete planning process
- If user wants to skip a phase (e.g., "no restaurants"), move to the next phase
- Remember all collected information across phases for final itinerary synthesis"""

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

