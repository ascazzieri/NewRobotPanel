import uuid

def create():
    return uuid.uuid4().hex.upper()