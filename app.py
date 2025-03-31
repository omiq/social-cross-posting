from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from social_media import SocialMediaPoster

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the social media poster
poster = SocialMediaPoster()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/post', methods=['POST'])
def post():
    try:
        text = request.form.get('text', '').strip()
        if not text:
            return jsonify({'error': 'Please enter some text for your post'})

        # Get selected platforms
        platforms = request.form.getlist('platforms')
        if not platforms:
            return jsonify({'error': 'Please select at least one platform'})

        results = {}
        
        # Handle image upload if present
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                results = poster.post_image(
                    text=text,
                    image_path=filepath,
                    platforms=platforms
                )
                
                # Clean up uploaded file
                os.remove(filepath)
                
        # Handle link if present
        elif request.form.get('link'):
            results = poster.post_link(
                text=text,
                url=request.form['link'],
                platforms=platforms
            )
            
        # Handle text-only post
        else:
            results = poster.post_text(
                text=text,
                platforms=platforms
            )

        # Process results
        success = []
        errors = []
        for platform, result in results.items():
            if 'error' in result:
                errors.append(f"{platform}: {result['error']}")
            else:
                success.append(platform)

        return jsonify({
            'success': success,
            'errors': errors
        })

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True) 