

import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL2, ADMINS, CHANNEL_ID, CHANNEL_ID2
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait

async def is_subscribed(filter, client, update):
    """Check if the user is subscribed to the required channels."""
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True

    # List of channels to check subscription
    channels = [FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL2]

    for channel in channels:
        if channel:
            try:
                member = await client.get_chat_member(chat_id=channel, user_id=user_id)
                if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                    return False
            except UserNotParticipant:
                return False

    return True

async def encode(string):
    """Encode a string to base64."""
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    """Decode a base64 string."""
    base64_string = base64_string.strip("=")  # Remove any trailing '=' characters
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    return string_bytes.decode("ascii")

async def get_messages(client, message_ids):
    """Retrieve multiple messages from a channel."""
    messages = []
    total_messages = 0
    while total_messages < len(message_ids):
        temp_ids = message_ids[total_messages:total_messages + 200]
        try:
            msgs = await client.get_messages(chat_id=client.db_channel.id, message_ids=temp_ids)
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(chat_id=client.db_channel.id, message_ids=temp_ids)
        except Exception as e:
            # Optionally log the exception
            pass
        
        messages.extend(msgs)
        total_messages += len(temp_ids)
    
    # Retrieve messages from the second database channel
    if client.db_channel2:
        try:
            msgs = await client.get_messages(chat_id=client.db_channel2.id, message_ids=temp_ids)
            messages.extend(msgs)
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(chat_id=client.db_channel2.id, message_ids=temp_ids)
            messages.extend(msgs)

    return messages

async def get_message_id(client, message):
    """Extract message ID from forwarded message or a link."""
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        elif message.forward_from_chat.id == client.db_channel2.id:
            return message.forward_from_message_id
        return 0
    elif message.forward_sender_name or not message.text:
        return 0

    pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
    matches = re.match(pattern, message.text)
    if matches:
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
            elif f"-100{channel_id}" == str(client.db_channel2.id):
                return msg_id
        elif channel_id == client.db_channel.username:
            return msg_id
        elif channel_id == client.db_channel2.username:
            return msg_id
    return 0

def get_readable_time(seconds: int) -> str:
    """Convert seconds to a readable time format."""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    for count in range(4):
        if seconds == 0:
            break
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        time_list.append(f"{int(result)}{time_suffix_list[count]}")
        seconds = int(remainder)

    if len(time_list) == 4:
        up_time = f"{time_list.pop()}, "
    else:
        up_time = ""

    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

subscribed = filters.create(is_subscribed)