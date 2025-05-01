from flask import Flask, render_template, request
import os
from food_classifier import load_model, get_class_labels, predict_food_class

app = Flask(__name__)

# Load model and class labels
model = load_model('food_model.pth')
# Load consistent class labels from file
with open("class_labels.txt", "r") as f:
    class_labels = [line.strip() for line in f.readlines()]

# Upload folder setup
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        predicted_label = predict_food_class(filepath, model, class_labels)
        return render_template('index.html', filename=file.filename, prediction=predicted_label)

if __name__ == '__main__':
    app.run(debug=True)
