"""temp-mail.io helper for creating inboxes and fetching messages."""

import random
from typing import List, Optional

from multipledispatch import dispatch
from requests import get, post

from autowebx.account import generate_username

_DOMAINS_CACHE: Optional[List[str]] = None


def domains() -> List[str]:
    """Return a cached list of available temp-mail domains.

    Falls back to a small built-in list if the API is unreachable.
    """
    global _DOMAINS_CACHE
    if _DOMAINS_CACHE is not None:
        return _DOMAINS_CACHE
    try:
        response = get("https://api.internal.temp-mail.io/api/v4/domains").json()
        _DOMAINS_CACHE = [domain["name"] for domain in response.get("domains", [])]
        if not _DOMAINS_CACHE:
            raise ValueError("Empty domains list")
    except Exception:
        _DOMAINS_CACHE = ["tempmail.dev", "mail.tm"]
    return _DOMAINS_CACHE


class Email:
    @dispatch(str, str)
    def __init__(self, name: str = generate_username(), domain: str = None):
        if domain is None:
            domain = random.choice(domains())
        payload = {"name": name, "domain": domain}
        response = post('https://api.internal.temp-mail.io/api/v3/email/new', json=payload).json()
        self.address = response['email']
        self.token = response['token']

    @dispatch(int, int)
    def __init__(self, min_name_length: int = 10, max_name_length: int = 10):
        payload = {"min_name_length": min_name_length, "max_name_length": max_name_length}
        response = post('https://api.internal.temp-mail.io/api/v3/email/new', json=payload).json()
        self.address = response['email']
        self.token = response['token']

    @dispatch()
    def __init__(self):
        self.__init__(10, 10)

    def get_messages(self):
        return get_messages(self.address)


def get_messages(email: str):
    response = get(f'https://api.internal.temp-mail.io/api/v3/email/{email}/messages').json()
    messages = [Message(message['id'], message['body_text'], message['body_html']) for message in response]
    return messages[0] if len(messages) == 1 else messages


class Message:
    def __init__(self, id_: str, body_text: str, body_html: str):
        self.id = id_
        self.body_text = body_text
        self.body_html = body_html

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return other is Message and self.id == other.id
