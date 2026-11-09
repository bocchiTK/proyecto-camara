document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const lampToggle = document.getElementById('lampToggle');
    const lampImage = document.getElementById('lampImage');

    const imgLight = "/static/imagenes/encendido.png";
    const imgDark = "/static/imagenes/apagado.png";

    // Cargar estado inicial guardado (por defecto oscuro)
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        body.classList.remove('dark-mode');
        lampImage.src = imgLight;
    } else {
        body.classList.add('dark-mode');
        lampImage.src = imgDark;
    }

    // Evento al hacer clic en la lámpara para alternar tema y cambiar imagen
    lampToggle.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        const isDark = body.classList.contains('dark-mode');

        if (isDark) {
            lampImage.src = imgDark;
            localStorage.setItem('theme', 'dark');
        } else {
            lampImage.src = imgLight;
            localStorage.setItem('theme', 'light');
        }
    });

    // Procesamiento en tiempo real con Sliders y OpenCV
    const sliders = ['brightness', 'exposure', 'contrast', 'highlights', 'shadows', 'vignette', 'saturation', 'warmth', 'hue', 'sharpness', 'blur'];
    const imageInput = document.getElementById('imageInput');
    const fileName = document.getElementById('fileName');
    const resultImg = document.getElementById('resultImg');
    const placeholderText = document.getElementById('placeholderText');
    const mlResults = document.getElementById('mlResults');
    const downloadBtn = document.getElementById('downloadBtn');

    let timeoutId = null;

    async function processImage() {
        if (!imageInput.files[0]) return;

        const formData = new FormData();
        formData.append('image', imageInput.files[0]);

        sliders.forEach(id => {
            formData.append(id, document.getElementById(id).value);
        });
        formData.append('grayscale', document.getElementById('grayscale').checked);

        try {
            const res = await fetch('/process', { method: 'POST', body: formData });
            if (!res.ok) throw new Error('Error al procesar la imagen');

            const data = await res.json();

            resultImg.src = data.processed_image_url + '?t=' + new Date().getTime();
            resultImg.style.display = 'block';
            placeholderText.style.display = 'none';

            downloadBtn.href = data.processed_image_url;
            downloadBtn.style.display = 'block';

            document.getElementById('brightnessVal').textContent = data.brightness;
            document.getElementById('contrastVal').textContent = data.contrast_metric;
            document.getElementById('predictionVal').textContent = data.prediction;
            mlResults.style.display = 'grid';

        } catch (err) {
            console.error(err);
        }
    }

    imageInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            fileName.textContent = file.name;
            
            const reader = new FileReader();
            reader.onload = function(event) {
                resultImg.src = event.target.result;
                resultImg.style.display = 'block';
                placeholderText.style.display = 'none';
            };
            reader.readAsDataURL(file);

            processImage();
        }
    });

    sliders.forEach(id => {
        const input = document.getElementById(id);
        const display = document.getElementById('val' + id.charAt(0).toUpperCase() + id.slice(1));
        
        if (input && display) {
            input.addEventListener('input', (e) => {
                display.textContent = e.target.value;
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    processImage();
                }, 50); 
            });
        }
    });

    const grayscaleCheck = document.getElementById('grayscale');
    if (grayscaleCheck) {
        grayscaleCheck.addEventListener('change', () => {
            processImage();
        });
    }
});