import os
import zipfile
from docx import Document
import uuid

def extract_text_and_images(docx_path, image_output_folder='static/images'):
    os.makedirs(image_output_folder, exist_ok=True)
    doc = Document(docx_path)
    text_parts = [p.text for p in doc.paragraphs if p.text.strip()]
    image_tags = []
    with zipfile.ZipFile(docx_path, 'r') as z:
        image_files = [f for f in z.namelist() if f.startswith('word/media/')]
        for img_name in image_files:
            ext = os.path.splitext(img_name)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif']:
                uid = uuid.uuid4().hex
                img_filename = f"{uid}{ext}"
                img_path = os.path.join(image_output_folder, img_filename)
                with open(img_path, 'wb') as f:
                    f.write(z.read(img_name))
                image_tags.append(f'<img src="/static/images/{img_filename}" style="max-width:100%;">')
    combined = ""
    for i, paragraph in enumerate(text_parts):
        combined += f"<p>{paragraph}</p>"
        if i < len(image_tags):
            combined += image_tags[i]
    return combined
