import uuid

from googletrans import Translator


def create_uuid() -> str:
    return str(uuid.uuid4())


def format_email_to_key(email: str) -> str:
    return email.replace("@", "_").replace(".", "_")


def capitalize_text(text: str) -> str:
    return " ".join(word.capitalize() for word in text.split())


async def translate_text(text: str, src='en', dest='pt') -> str:
    try:
        async with Translator() as translator:
            result = await translator.translate(text, src=src, dest=dest)
            return result.text
    except:
        return text
