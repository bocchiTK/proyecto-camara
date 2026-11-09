import os
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No se seleccionó ninguna imagen'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    img = cv2.imread(filepath)
    if img is None:
        return jsonify({'error': 'No se pudo leer la imagen'}), 400

    # Lectura de parámetros de los Sliders
    grayscale = request.form.get('grayscale') == 'true'
    blur_val = int(request.form.get('blur', 0))
    brightness = int(request.form.get('brightness', 0))
    exposure = float(request.form.get('exposure', 0))
    contrast = int(request.form.get('contrast', 0))
    highlights = int(request.form.get('highlights', 0))
    shadows = int(request.form.get('shadows', 0))
    vignette_val = int(request.form.get('vignette', 0))
    saturation = float(request.form.get('saturation', 0))
    warmth = int(request.form.get('warmth', 0))
    hue = int(request.form.get('hue', 0))
    sharpness = int(request.form.get('sharpness', 0))

    img_proc = img.astype(np.float32)

    if brightness != 0:
        img_proc += brightness
    if exposure != 0:
        factor = 2 ** (exposure / 50.0)
        img_proc *= factor

    if contrast != 0:
        factor = (259 * (contrast + 255)) / (255 * (259 - contrast))
        img_proc = factor * (img_proc - 128) + 128

    if highlights != 0 or shadows != 0:
        gray_tmp = cv2.cvtColor(np.clip(img_proc, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        norm_gray = gray_tmp / 255.0

        if highlights != 0:
            h_mask = np.power(norm_gray, 2)[:, :, np.newaxis]
            img_proc += (highlights * h_mask)

        if shadows != 0:
            s_mask = np.power(1.0 - norm_gray, 2)[:, :, np.newaxis]
            img_proc += (shadows * s_mask)

    img_proc = np.clip(img_proc, 0, 255).astype(np.uint8)

    if saturation != 0 or hue != 0 or warmth != 0:
        hsv = cv2.cvtColor(img_proc, cv2.COLOR_BGR2HSV).astype(np.float32)

        if hue != 0:
            hsv[:, :, 0] = (hsv[:, :, 0] + hue) % 180

        if saturation != 0:
            sat_factor = 1.0 + (saturation / 100.0)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_factor, 0, 255)

        img_proc = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        if warmth != 0:
            b, g, r = cv2.split(img_proc.astype(np.float32))
            r = np.clip(r + warmth, 0, 255)
            b = np.clip(b - warmth, 0, 255)
            img_proc = cv2.merge([b, g, r]).astype(np.uint8)

    if sharpness > 0:
        amount = sharpness / 50.0
        kernel = np.array([[0, -amount, 0],
                           [-amount, 1 + 4 * amount, -amount],
                           [0, -amount, 0]])
        img_proc = cv2.filter2D(img_proc, -1, kernel)

    if blur_val > 0:
        k_size = blur_val * 2 + 1
        img_proc = cv2.GaussianBlur(img_proc, (k_size, k_size), 0)

    if vignette_val > 0:
        h, w = img_proc.shape[:2]
        kernel_x = cv2.getGaussianKernel(w, w * (1.1 - vignette_val / 100.0))
        kernel_y = cv2.getGaussianKernel(h, h * (1.1 - vignette_val / 100.0))
        kernel_2d = kernel_y * kernel_x.T
        mask = kernel_2d / kernel_2d.max()

        if len(img_proc.shape) == 3:
            mask = np.repeat(mask[:, :, np.newaxis], 3, axis=2)
        img_proc = (img_proc * mask).astype(np.uint8)

    if grayscale:
        img_proc = cv2.cvtColor(img_proc, cv2.COLOR_BGR2GRAY)

    processed_filename = f"proc_{filename}"
    processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
    cv2.imwrite(processed_path, img_proc)

    avg_brightness = float(np.mean(img_proc))
    std_contrast = float(np.std(img_proc))
    pred_class = "Imagen Normal / Equilibrada"
    if avg_brightness > 160:
        pred_class = "Alta Exposición / Muy Brillante"
    elif avg_brightness < 70:
        pred_class = "Baja Exposición / Sombría"

    return jsonify({
        'processed_image_url': f'/static/uploads/{processed_filename}',
        'brightness': round(avg_brightness, 2),
        'contrast_metric': round(std_contrast, 2),
        'prediction': pred_class
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)