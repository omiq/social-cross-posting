import pip
import sys

def install_requirements():
    requirements = [
        'atproto>=0.0.31',
        'Mastodon.py>=1.8.1',
        'facebook-business>=19.0.0',
        'linkedin-api>=2.0.0',
        'instagram-private-api>=1.6.0',
        'Pillow>=10.0.0',
        'requests>=2.31.0',
        'beautifulsoup4>=4.12.0',
        'python-dotenv>=1.0.0'
    ]
    
    for req in requirements:
        print(f"Installing {req}...")
        try:
            pip.main(['install', req])
            print(f"Successfully installed {req}")
        except Exception as e:
            print(f"Error installing {req}: {e}")

if __name__ == '__main__':
    install_requirements()