import logging
import json
import os
logger = logging.getLogger("agent")
from memory import init_db, get_user, save_user
from livekit.agents import function_tool, RunContext



from dotenv import load_dotenv
from livekit import rtc, api
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
SCHEME_DATA = {
    "education_support": {
        "name": "Education Support Scheme",
        "min_age": 18,
        "max_age": 30,
        "student_required": True,
        "income_limit": 500000,
        "last_updated": "August 10, 2026",
    }
}

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
When the user asks about eligibility for the Education Support Scheme
and provides their age, student status, and annual income, use the
check_scheme_eligibility tool immediately.

Do not ask for their name, state, region, or other unnecessary
information when these three details are provided.

Do not request sensitive personal information.
MEMORY & PRIVACY

FinAssist can remember limited, non-sensitive information between conversations.

IMPORTANT:
Never save information automatically.

Before saving any personal information, clearly ask the user:

"Would you like me to remember this information for future conversations?"

Only call the save_user_memory tool if the user clearly says yes.

If the user says no, do not save anything.

If the user is unsure, do not save anything.

You may remember only safe information such as:

- Name
- Preferred language
- Government schemes the user has asked about
- General financial goal such as saving for education or planning a budget

NEVER save:

- Bank account numbers
- Aadhaar numbers
- OTPs
- ATM PINs
- CVV
- Passwords
- Debit card numbers
- Credit card numbers
- Net banking credentials
- Transaction details
- Loan account numbers

If a user provides sensitive information, do not store it.
Politely remind them never to share confidential financial information.

RETURNING USERS

At the beginning of a conversation, use the lookup_user tool when a user ID is available.

If a saved user is found, greet them by name.

For example:

"Welcome back, Joshna! How can I help you today?"

Do not reveal sensitive stored information.

If no user is found, continue normally and ask for the user's name when appropriate.
DAY 5 FINANCIAL ELIGIBILITY TOOL

FinAssist has a tool called check_scheme_eligibility.

Use this tool when a user asks whether they may meet the basic
eligibility conditions for the Education Support Scheme.

Before calling the tool, collect the required information:

- Age
- Whether the user is currently a student
- Approximate annual household income

Do not ask for bank account numbers, Aadhaar numbers, OTPs, PINs,
CVVs, passwords, card numbers, or other sensitive financial
information.

The tool uses a local demo dataset.

Always make it clear that the result is a preliminary educational
check and NOT official scheme approval.

Always mention that the dataset has an update date.

If the tool fails, do not guess an eligibility result.

Instead say:

"I'm unable to check the eligibility information right now.
I don't want to guess or provide incorrect financial information.
Please try again later or verify the details with the official
scheme provider."

You are FinAssist, a friendly and helpful AI financial assistance voice agent.

Your task today is to make an OUTBOUND phone call to a user.

The purpose of the call is to proactively remind the user about an important
financial scheme, benefit, application, or deadline that may require their
attention.

OUTBOUND CALL OBJECTIVE:
1. Introduce yourself as FinAssist.
2. Tell the user that you are calling regarding an important financial
   assistance update.
3. Confirm that you are speaking with the intended user.
4. Briefly explain the reason for the call.
5. Inform the user if a financial scheme or application deadline is approaching.
6. Ask whether they need help understanding the next steps.
7. Answer their questions clearly and simply.
8. End the call politely.

IMPORTANT BEHAVIOR:
- Keep the conversation short and natural.
- Speak clearly and professionally.
- Do not overwhelm the user with financial terminology.
- Never claim that the user is definitely eligible for a scheme unless the
  available information confirms it.
- Never ask for passwords, OTPs, PINs, CVV numbers, or full banking credentials.
- Never pretend to be a government officer, bank employee, or human.
- If you do not know an answer, honestly say that you do not have that
  information.
- Do not make promises about loan approval, money transfers, or guaranteed
  benefits.
- Respect the user's decision if they do not want to continue the call.
- If the user says they are busy, offer to end the call politely.

EXAMPLE OPENING:

"Hello! This is FinAssist, an AI financial assistance agent.
I'm calling to remind you about an important financial assistance update.
Do you have a minute to talk?"

If the user agrees:

"I wanted to let you know that an important scheme or application deadline
may be approaching. I can explain the information and help you understand
what steps you may need to take."

If the user asks for more information:

"Sure. I can explain the available information, but I cannot guarantee
eligibility or approval. Would you like me to explain the next steps?"

ENDING:

"Thank you for your time. I hope the information was helpful.
Have a great day!"


"""

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
    @function_tool
    async def check_scheme_eligibility(
        self,
        context: RunContext,
        age: int,
        is_student: bool,
        annual_income: float,
    ) -> str:
        """Check basic eligibility for the Education Support Scheme.

        Use this tool when the user asks whether they may be eligible
        for the Education Support Scheme and provides their age,
        student status, and annual income.

        This is a preliminary check using a local demo dataset.
        It is not an official approval or government decision.

        Args:
            age: User's age in years.
            is_student: Whether the user is currently a student.
            annual_income: User's approximate annual household income
                in Indian rupees.
        """

        try:
            scheme = SCHEME_DATA["education_support"]

            age_ok = (
                scheme["min_age"] <= age <= scheme["max_age"]
            )

            student_ok = is_student

            income_ok = annual_income <= scheme["income_limit"]

            if age_ok and student_ok and income_ok:
                result = (
                    f"Based on the information provided, you meet the "
                    f"basic conditions in the {scheme['name']} demo dataset. "
                    f"This information was last updated on "
                    f"{scheme['last_updated']}. "
                    f"This is only a preliminary check and is not official "
                    f"scheme approval."
                )
            else:
                reasons = []

                if not age_ok:
                    reasons.append(
                        f"the demo age range is "
                        f"{scheme['min_age']} to {scheme['max_age']} years"
                    )

                if not student_ok:
                    reasons.append(
                        "the scheme requires the applicant to be a student"
                    )

                if not income_ok:
                    reasons.append(
                        f"the demo income limit is ₹{scheme['income_limit']:,} "
                        "per year"
                    )

                result = (
                    f"Based on the information provided, you do not meet "
                    f"all the basic conditions in the {scheme['name']} "
                    f"demo dataset. The reason is: "
                    + "; ".join(reasons)
                    + f". The information was last updated on "
                    f"{scheme['last_updated']}. "
                    f"This is not an official eligibility decision."
                )

            logger.info(
                "Scheme eligibility checked for age=%s, student=%s",
                age,
                is_student,
            )

            return result

        except Exception as e:
            logger.error("Eligibility check failed: %s", e)

            return (
                "I'm unable to check the eligibility information right now. "
                "I don't want to guess or provide incorrect financial "
                "information. Please try again later or verify the details "
                "with the official scheme provider."
            )

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
    # -----------------------------------------
    # DAY 6 - OUTBOUND CALL
    # -----------------------------------------
    dial_info = json.loads(ctx.job.metadata or "{}")
    phone_number = dial_info.get("phone_number")

    participant = None

    if phone_number:
        try:
            sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")

            if not sip_trunk_id:
                logger.error("LIVEKIT_SIP_TRUNK_ID is missing")
                return

            participant_identity = f"sip-{phone_number}"

            await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=sip_trunk_id,
                    sip_call_to=phone_number,
                    room_name=ctx.room.name,
                    participant_identity=participant_identity,
                    participant_name="FinAssist User",
                    wait_until_answered=True,
                )
            )

            participant = await ctx.wait_for_participant(
                identity=participant_identity
            )

            logger.info(
                "Outbound call connected to %s",
                phone_number,
            )

        except Exception as e:
            logger.error(
                "Outbound call failed: %s",
                e,
            )
            return

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
        participant=participant,
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
# Start the session
    if participant:
        await session.start(
            agent=Assistant(),
            room=ctx.room,
            participant=participant,
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
    else:
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
        
    # Make FinAssist speak immediately after the call is answered
    if participant:
        await session.generate_reply(
            instructions="""
            The outbound phone call has been answered.

            Immediately greet the person.

            Say:
            "Hello! This is FinAssist, an AI financial assistance agent.
            I'm calling to remind you about an important financial assistance
            update. Do you have a minute to talk?"

            Keep the greeting short and natural.
            """
        )
       
    
    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
