import os
import asyncio
from dotenv import load_dotenv

from livekit import api


load_dotenv(".env.local")


async def make_outbound_call():

    lkapi = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    room_name = "linphone-outbound-call"

    sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")
    sip_call_to = "joshna"

    if not sip_trunk_id:
        print("ERROR: LIVEKIT_SIP_TRUNK_ID is missing")
        await lkapi.aclose()
        return

    print("--------------------------------")
    print("STARTING OUTBOUND CALL")
    print("--------------------------------")
    print("Trunk ID:", sip_trunk_id)
    print("Calling SIP user:", sip_call_to)
    print("Room:", room_name)

    try:

        # -----------------------------------------
        # 1. Dispatch FinAssist into the room
        # -----------------------------------------
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="my-agent",
                metadata='{"outbound_call": true}',
            )
        )

        print("✅ FinAssist dispatched")
        print("Dispatch ID:", dispatch.id)

        # -----------------------------------------
        # 2. Create the SIP participant
        # -----------------------------------------
        participant = await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=sip_trunk_id,
                sip_call_to=sip_call_to,
                room_name=room_name,
                participant_identity="joshna",
                participant_name="Joshna",
                wait_until_answered=True,
            )
        )

        print("--------------------------------")
        print("CALL STARTED")
        print("--------------------------------")
        print("Participant ID:", participant.participant_id)
        print("Room:", room_name)
        print("SIP User:", sip_call_to)
        print("--------------------------------")

    except Exception as e:

        print("--------------------------------")
        print("CALL FAILED")
        print("--------------------------------")
        print("Error:", e)
        print("--------------------------------")

    finally:
        await lkapi.aclose()


if __name__ == "__main__":
    asyncio.run(make_outbound_call())
