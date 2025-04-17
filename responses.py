# from random import choice, randint

def get_response(user_input: str) -> str:
    # raise NotImplementedError('Code is missing')
    lowered: str = user_input.lower()

    if lowered == '':
        return 'Test'
    elif 'hello' in lowered:
        return "hi"