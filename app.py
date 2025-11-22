from flask import Flask, render_template, Response, jsonify
from src.camera_manager import CameraManager

app = Flask(__name__)

# Configuração Global (Pode ser melhorado para aceitar via argumento)
EXERCISE_CONFIG = "exercise_templates/pushup.json"
VIDEO_SOURCE = 0 # Use 0 para webcam, ou caminho do arquivo "videos/teste.mp4"

# Instância global do gerenciador de câmera
camera_manager = CameraManager(EXERCISE_CONFIG, VIDEO_SOURCE)

@app.route('/')
def index():
    """Rota principal que carrega a página HTML."""
    return render_template('index.html')

def gen_frames():
    """Função geradora para streaming de vídeo."""
    while True:
        frame_bytes = camera_manager.get_frame()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            break

@app.route('/video_feed')
def video_feed():
    """Rota que fornece o fluxo de vídeo MJPEG."""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    """API JSON que retorna os dados atuais (reps, feedback) para o JS atualizar a tela."""
    return jsonify(camera_manager.current_status)

@app.route('/finish_workout')
def finish_workout():
    """Finaliza o treino e retorna o relatório."""
    report = camera_manager.get_final_report()
    return jsonify({"report": report})

if __name__ == '__main__':
    # host='0.0.0.0' permite acesso por outros dispositivos na mesma rede (Wi-Fi)
    app.run(host='0.0.0.0', port=5000, debug=True)