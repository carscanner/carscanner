import json


def save_token_on_refresh(access_token, refresh_token):
    with open('insecure-tokens.txt', 'wt') as token_file:
        tokens = {'access_token': access_token, 'refresh_token': refresh_token}
        json.dump(tokens, token_file)


# ex. read saved token from file
def load_token_on_start():
    try:
        with open('insecure-tokens.txt', 'r') as token_file:
            return json.load(token_file)
    except:
        return {'access_token': None, 'refresh_token': None}


from allegro_api.configuration import Configuration as ApiConfiguration


def main():

    configuration = ApiConfiguration()
    # api = auto_refresh(allegro_api, configuration)

    configuration.access_token = load_token_on_start().access_token
    configuration.host = 'https://api.allegro.pl'

