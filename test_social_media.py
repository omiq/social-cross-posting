from social_media import SocialMediaPoster
import time

def main():
    # Initialize the poster
    poster = SocialMediaPoster()
    
    # Test 1: Text post with image
    print("\nTest 1: Posting image with caption...")
    try:
        result = poster.post_image(
            "This is a test of my social media cross-posting Python script",
            "./kara.jpg",
            alt_text="A photo of Kara"
        )
        print("Image post results:", result)
    except Exception as e:
        print(f"Error posting image: {e}")
    
    # Wait a bit between posts to avoid rate limits
    time.sleep(5)
    
    # Test 2: Link post
    print("\nTest 2: Posting link...")
    try:
        result = poster.post_link(
            "This is a test of my social media cross-posting Python script",
            "https://github.com/omiq/bluesky"
        )
        print("Link post results:", result)
    except Exception as e:
        print(f"Error posting link: {e}")
    
    # Wait a bit between posts
    time.sleep(5)
    
    # Test 3: Text-only post
    print("\nTest 3: Posting text only...")
    try:
        result = poster.post_text(
            "This is test 3 of my social media cross-posting Python script"
        )
        print("Text post results:", result)
    except Exception as e:
        print(f"Error posting text: {e}")

if __name__ == "__main__":
    main() 