import ui
import photos
import tempfile
import os
from social_media_pythonista import SocialMediaPoster

class SocialMediaUI:
    def __init__(self):
        self.poster = SocialMediaPoster()
        self.selected_image = None
        
        # Create main view
        self.view = ui.View()
        self.view.name = 'Social Media Poster'
        self.view.background_color = 'white'
        
        # Text input
        self.text_input = ui.TextView()
        self.text_input.frame = (10, 10, self.view.width - 20, 100)
        self.text_input.border_width = 1
        self.text_input.border_color = '#cccccc'
        self.text_input.corner_radius = 5
        self.text_input.placeholder = 'Enter your post text here...'
        self.view.add_subview(self.text_input)
        
        # Link input
        self.link_input = ui.TextField()
        self.link_input.frame = (10, 120, self.view.width - 20, 40)
        self.link_input.border_width = 1
        self.link_input.border_color = '#cccccc'
        self.link_input.corner_radius = 5
        self.link_input.placeholder = 'Optional: Enter a link...'
        self.view.add_subview(self.link_input)
        
        # Image selection button
        self.image_button = ui.Button(title='Select Image')
        self.image_button.frame = (10, 170, self.view.width - 20, 40)
        self.image_button.action = self.select_image
        self.image_button.background_color = '#007AFF'
        self.image_button.tint_color = 'white'
        self.image_button.corner_radius = 5
        self.view.add_subview(self.image_button)
        
        # Image preview
        self.image_preview = ui.ImageView()
        self.image_preview.frame = (10, 220, self.view.width - 20, 200)
        self.image_preview.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
        self.image_preview.border_width = 1
        self.image_preview.border_color = '#cccccc'
        self.image_preview.corner_radius = 5
        self.image_preview.hidden = True
        self.view.add_subview(self.image_preview)
        
        # Platform selection
        y = 430
        self.platform_switches = {}
        platforms = ['bluesky', 'mastodon']
        for platform in platforms:
            switch = ui.Switch()
            switch.frame = (10, y, self.view.width - 20, 40)
            switch.title = platform.capitalize()
            switch.value = True
            self.platform_switches[platform] = switch
            self.view.add_subview(switch)
            y += 50
            
        # Post button
        self.post_button = ui.Button(title='Post')
        self.post_button.frame = (10, y, self.view.width - 20, 40)
        self.post_button.action = self.post_content
        self.post_button.background_color = '#34C759'
        self.post_button.tint_color = 'white'
        self.post_button.corner_radius = 5
        self.view.add_subview(self.post_button)
        
        # Status label
        self.status_label = ui.Label()
        self.status_label.frame = (10, y + 50, self.view.width - 20, 40)
        self.status_label.text_alignment = ui.ALIGN_CENTER
        self.status_label.text_color = '#666666'
        self.view.add_subview(self.status_label)
        
    def select_image(self, sender):
        """Handle image selection from photo library"""
        def handle_image(image):
            if image:
                # Get the image data
                image_data = image.get_image()
                
                # Save to temporary file
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, 'selected_image.jpg')
                
                # Save the image data
                with open(temp_path, 'wb') as f:
                    f.write(image_data)
                
                self.selected_image = temp_path
                self.image_preview.image = image
                self.image_preview.hidden = False
                
        photos.pick_image(handle_image)
        
    def post_content(self, sender):
        """Handle posting content to selected platforms"""
        text = self.text_input.text.strip()
        if not text:
            self.status_label.text = 'Please enter some text for your post'
            return
            
        # Get selected platforms
        platforms = [p for p, switch in self.platform_switches.items() if switch.value]
        if not platforms:
            self.status_label.text = 'Please select at least one platform'
            return
            
        try:
            # Handle different types of posts
            if self.selected_image:
                # Image post
                results = self.poster.post_image(
                    text=text,
                    image_path=self.selected_image,
                    platforms=platforms
                )
            elif self.link_input.text.strip():
                # Link post
                results = self.poster.post_link(
                    text=text,
                    url=self.link_input.text.strip(),
                    platforms=platforms
                )
            else:
                # Text-only post
                results = self.poster.post_text(
                    text=text,
                    platforms=platforms
                )
                
            # Show results
            success = []
            errors = []
            for platform, result in results.items():
                if 'error' in result:
                    errors.append(f"{platform}: {result['error']}")
                else:
                    success.append(platform)
                    
            if success:
                self.status_label.text = f"Posted successfully to: {', '.join(success)}"
            if errors:
                self.status_label.text += f"\nErrors: {', '.join(errors)}"
                
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"

def main():
    ui_view = SocialMediaUI()
    ui_view.view.present('sheet')

if __name__ == '__main__':
    main() 