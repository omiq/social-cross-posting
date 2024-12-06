import sys
from atproto import Client, client_utils

def test(handle, password):
    client = Client()
    profile = client.login(handle, password)
    print('Logged in as ', profile.display_name)

    text = client_utils.TextBuilder().text('Testing out the ').link('Python SDK', 'https://atproto.blue')
    post = client.send_post(text)
    client.like(post.uri, post.cid)


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print("Please provide handle and password")
        sys.exit(1)
    handle = sys.argv[1]
    password = sys.argv[2]
    test(handle, password)
