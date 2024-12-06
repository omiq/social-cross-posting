import sys
from PIL import Image 
from atproto import Client, client_utils
from atproto import Client, models

def login(handle, password):
    client = Client()
    profile = client.login(handle, password)
    print('Logged in as ', profile.display_name)
    return client

def post(client, message, anchortext='', link=''):

    if link !='':
        text = client_utils.TextBuilder().text(message).link(anchortext, link)
    else:
        text = client_utils.TextBuilder().text(message)
    post = client.send_post(text)
    return post

def get_size(imagefile):
    # get image dimensions
    img = Image.open(imagefile) 
    return img.width, img.height 

def get_user_feed(client, handle):

    print(f'\nProfile Posts of {handle}:\n\n')

    # Get profile's posts. Use pagination (cursor + limit) to fetch all
    profile_feed = client.get_author_feed(actor=handle)
    return profile_feed.feed

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

    link = "https://github.com/omiq/bluesky"
    result = post(client, "I think I will work on a #WordPress plugin that posts newly published articles (after a short delay). Will add to my repo here any experiments I make: ", "Github", link)
    print(result)
    
    # print(client.get_author_feed)
    # post_image(client, "Kara", "./kara.jpg")
    feed = get_user_feed(client, "chrisg.com")
    #for post in feed:
    post = feed[0]
    if(post.post.record.reply==None & post.post.embed != None):
        print('\n\n', post.post.record.text, post.post.embed.images[0].fullsize, post.post.embed.images[0].alt)

