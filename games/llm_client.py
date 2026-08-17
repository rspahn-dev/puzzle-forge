import anthropic


def get_client(api_key):
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)
