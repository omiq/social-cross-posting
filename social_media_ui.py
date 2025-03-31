import ui
import photos
import tempfile
import os
from social_media import SocialMediaPoster
from PIL import Image
import io

class SocialMediaUI:
    def __init__(self):
        self.poster = SocialMediaPoster()
        self.selected_image = None
        self.setup_ui()
        
    def setup_ui(self):
        # Create main view
        self.view = ui.View()
        self.view.name = 'Social Media Poster'
        self.view.background_color = 'white'
        
        # Create text input
        self.text_input = ui.TextView()
        self.text_input.frame = (10, 10, self.view.width - 20, 100)
        self.text_input.border_width = 1
        self.text_input.border_color = '#cccccc'
        self.text_input.corner_radius = 5
        self.text_input.placeholder = 'Enter your post text here...'
        self.view.add_subview(self.text_input)
        
        # Create link input
        self.link_input = ui.TextField()
        self.link_input.frame = (10, 120, self.view.width - 20, 40)
        self.link_input.border_width = 1
        self.link_input.border_color = '#cccccc'
        self.link_input.corner_radius = 5
        self.link_input.placeholder = 'Optional: Enter a link...'
        self.view.add_subview(self.link_input)
        
        # Create image button
        self.image_button = ui.Button(title='Select Image')
        self.image_button.frame = (10, 170, self.view.width - 20, 40)
        self.image_button.action = self.select_image
        self.image_button.background_color = '#007AFF'
        self.image_button.tint_color = 'white'
        self.image_button.corner_radius = 5
        self.view.add_subview(self.image_button)
        
        # Create selected image preview
        self.image_preview = ui.ImageView()
        self.image_preview.frame = (10, 220, 100, 100)
        self.image_preview.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
        self.image_preview.hidden = True
        self.view.add_subview(self.image_preview)
        
        # Create platform checkboxes
        self.platforms = {
            'bluesky': ui.Switch(),
            'mastodon': ui.Switch(),
            'facebook': ui.Switch(),
            'linkedin': ui.Switch(),
            'instagram': ui.Switch(),
            'threads': ui.Switch()
        }
        
        y = 330
        for platform, switch in self.platforms.items():
            # Create label
            label = ui.Label()
            label.text = platform.title()
            label.frame = (10, y, 100, 30)
            self.view.add_subview(label)
            
            # Position switch
            switch.frame = (120, y, 50, 30)
            switch.value = True  # Default to checked
            self.view.add_subview(switch)
            
            y += 40
        
        # Create post button
        self.post_button = ui.Button(title='Post')
        self.post_button.frame = (10, y + 10, self.view.width - 20, 40)
        self.post_button.action = self.post_content
        self.post_button.background_color = '#34C759'
        self.post_button.tint_color = 'white'
        self.post_button.corner_radius = 5
        self.view.add_subview(self.post_button)
        
        # Create status label
        self.status_label = ui.Label()
        self.status_label.frame = (10, y + 60, self.view.width - 20, 40)
        self.status_label.text_alignment = ui.ALIGN_CENTER
        self.view.add_subview(self.status_label)
        
    def select_image(self, sender):
        # Show photo picker
        photos.pick_image(media_type='image', completion=self.handle_image_selection)
        
    def handle_image_selection(self, image):
        if image:
            # Store the image
            self.selected_image = image
            
            # Show preview
            self.image_preview.image = image
            self.image_preview.hidden = False
            
            # Resize preview if needed
            preview_size = 100
            aspect_ratio = image.size[1] / image.size[0]
            if aspect_ratio > 1:
                width = preview_size
                height = int(preview_size * aspect_ratio)
            else:
                height = preview_size
                width = int(preview_size / aspect_ratio)
            self.image_preview.frame = (10, 220, width, height)
            
    def post_content(self, sender):
        # Get selected platforms
        selected_platforms = [platform for platform, switch in self.platforms.items() if switch.value]
        
        if not selected_platforms:
            self.status_label.text = 'Please select at least one platform'
            return
            
        # Get text content
        text = self.text_input.text.strip()
        if not text:
            self.status_label.text = 'Please enter some text'
            return
            
        # Get link
        link = self.link_input.text.strip()
        
        # Post based on content type
        try:
            if self.selected_image:
                # Save image to temporary file
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    self.selected_image.save(temp_file.name, 'JPEG')
                    temp_path = temp_file.name
                
                # Post image
                result = self.poster.post_image(
                    text=text,
                    image_path=temp_path,
                    platforms=selected_platforms
                )
                
                # Clean up temp file
                os.unlink(temp_path)
                
            elif link:
                # Post link
                result = self.poster.post_link(
                    text=text,
                    url=link,
                    platforms=selected_platforms
                )
                
            else:
                # Post text only
                result = self.poster.post_text(
                    text=text,
                    platforms=selected_platforms
                )
            
            # Show results
            success_count = sum(1 for r in result.values() if 'error' not in r)
            self.status_label.text = f'Posted successfully to {success_count} platforms'
            
        except Exception as e:
            self.status_label.text = f'Error: {str(e)}'

def main():
    ui_view = SocialMediaUI()
    ui_view.view.present('sheet')
    
if __name__ == '__main__':
    main() 