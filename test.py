import sys
from PIL import Image 
from atproto import Client, client_utils
from atproto import Client, models

def login(handle, password):
    client = Client()
    profile = client.login(handle, password)
    print('Logged in as ', profile.display_name)
    return client

def post(client, message):

    text = client_utils.TextBuilder().text(message) #.link('Python SDK', 'https://atproto.blue')
    post = client.send_post(text)
    return post

def get_size(imagefile):
    # get image dimensions
    img = Image.open(imagefile) 
    return img.width, img.height 

def post_image(client, text, imagefile, alt_text=''):

    # the path to our image file
    with open(imagefile, 'rb') as f:
        img_data = f.read()
  
    # get width and height 
    width, height = get_size(imagefile)

    # Add image aspect ratio to prevent default 1:1 aspect ratio
    # Replace with your desired aspect ratio
    aspect_ratio = models.AppBskyEmbedDefs.AspectRatio(height=height, width=width)
    
    client.send_image(
        text=text,
        image=img_data,
        image_alt=alt_text,
        image_aspect_ratio=aspect_ratio,
    )



if __name__ == '__main__':

    if len(sys.argv) < 3:
        print("Please provide handle and password")
        sys.exit(1)
    handle = sys.argv[1]
    password = sys.argv[2]
    client = login(handle, password)
    # result = post(client, "Another test of the API, will delete")
    # print(client.get_author_feed)
    post_image(client, "Kara", "./kara.jpg")

    
