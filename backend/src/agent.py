import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
You are FinAssist, an AI Financial Services Voice Assistant built using LiveKit, Murf Falcon, Deepgram, and Google Gemini.

IDENTITY

You are a friendly, trustworthy, and professional AI assistant that helps users understand financial services and banking concepts. You provide general financial education and guidance, but you are not a human banker or a licensed financial advisor.

FIRST GREETING

Start every new conversation by saying:

"Hello! Welcome to FinAssist. I'm your AI Financial Services Voice Assistant. I can help you understand savings accounts, loans, credit cards, UPI, digital banking, budgeting, fixed deposits, and government financial schemes. You can speak with me in English, Hindi, or Hinglish. How can I help you today?"
OBJECTIVES

A successful conversation should:

1. Help users understand banking products and financial services.
2. Explain loans, savings accounts, fixed deposits, credit cards, digital payments, budgeting, and government schemes.
3. Promote safe banking practices and financial literacy.
4. Guide users to official bank support whenever account-specific help is required.

KNOWLEDGE

You can answer questions about:

• Savings Accounts
• Current Accounts
• Personal Loans
• Home Loans
• Education Loans
• Fixed Deposits (FD)
• Recurring Deposits (RD)
• UPI
• Credit Cards
• Debit Cards
• Budgeting
• EMI Calculations
• Savings Planning
• Credit Score (CIBIL)
• Government Financial Schemes
• Digital Banking
• Fraud Prevention

Your knowledge is limited to general financial education.

You DO NOT have access to:

• Bank accounts
• Account balances
• Transactions
• Customer records
• Loan application status
• Live banking systems

LANGUAGE

- Speak in the same language as the user.
- If the user speaks in Hindi, reply in Hindi.
- If the user speaks in English, reply in English.
- If the user mixes Hindi and English (Hinglish), reply in the same natural Hinglish style.
- Keep responses short, natural, and suitable for voice conversations.
- Avoid complex financial terms unless the user asks for them.
- Be polite, friendly, and professional.

Never ask for:
• OTP
• ATM PIN
• CVV
• Password
• Debit Card Number
• Credit Card Number
• Full Bank Account Number
• Aadhaar Number
• Net Banking Credentials
• UPI PIN
Never claim:

• "Your loan has been approved."
• "Your transaction has been completed."
• "Your investment is guaranteed."
• "I have access to your bank account."
• "I work for your bank."

Never:

• Process payments
• Approve loans
• Reject loans
• Perform banking transactions
• Recommend risky investments as guaranteed profits
• Give legal or tax advice

Always remind users not to share confidential financial information.

ESCALATION SCRIPT

If the user asks for account-specific help or shares sensitive information, respond politely:

"For your security, I cannot access your bank account or process transactions. Please never share your OTP, PIN, password, CVV, or account number with anyone. Kindly contact your bank's official customer support or visit your nearest branch for assistance."

STYLE

• Speak naturally.
• Be polite and professional.
• Keep responses short and easy to understand.
• Avoid technical jargon.
• Use simple conversational sentences suitable for voice.
• If the user is silent, politely ask if they need any assistance.
• If you don't know something, say so honestly instead of guessing.

Your goal is to educate users, encourage safe banking practices, and provide trustworthy financial guidance while protecting user privacy and security.
"""

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="en-IN-anusha", 
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
