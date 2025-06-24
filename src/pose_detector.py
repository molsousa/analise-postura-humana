from ultralytics import YOLO
import numpy as np

# Mapeamento dos keypoints do COCO para facilitar a leitura do código
COCO_KEYPOINTS = {
    'nose': 0, 'left_eye': 1, 'right_eye': 2, 'left_ear': 3, 'right_ear': 4,
    'left_shoulder': 5, 'right_shoulder': 6, 'left_elbow': 7, 'right_elbow': 8,
    'left_wrist': 9, 'right_wrist': 10, 'left_hip': 11, 'right_hip': 12,
    'left_knee': 13, 'right_knee': 14, 'left_ankle': 15, 'right_ankle': 16
}

# Conexões para desenhar o esqueleto no padrão COCO
COCO_POSE_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),  # Cabeça
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10), # Tronco e braços
    (11, 12), (5, 11), (6, 12), # Quadris
    (11, 13), (13, 15), (12, 14), (14, 16) # Pernas
]

class PoseDetector:
    """
    Encapsula o modelo YOLOv8-Pose para uma detecção de pose simplificada.

    Esta classe carrega o modelo de detecção de pose pré-treinado e fornece
    um método simples para detectar os keypoints em um único frame de imagem.
    """
    def __init__(self, model_path='yolov8s-pose.pt'):
        """
        Inicializa o detector de pose carregando o modelo YOLO.

        Args:
            model_path (str): Caminho para o arquivo do modelo YOLO (.pt).
        """
        self.model = YOLO(model_path)

    def detectar(self, frame):
        """
        Detecta poses no frame e retorna os keypoints da pessoa principal.

        Args:
            frame (np.array): A imagem (frame de vídeo) no formato OpenCV (BGR).

        Returns:
            np.array: Um array NumPy de shape (17, 3) contendo as coordenadas (x, y)
                      e a confiança para cada um dos 17 keypoints da primeira pessoa
                      detectada. Retorna None se nenhuma pessoa for detectada.
        """
        results = self.model(frame, verbose=False)
        
        # Verifica se alguma pose foi detectada
        if not results or not results[0].keypoints or results[0].keypoints.shape[0] == 0:
            return None

        # Estratégia simples: assume que a primeira pessoa detectada é o alvo.
        # Para cenários mais complexos, um tracker de objetos poderia ser usado
        # para seguir uma pessoa específica entre os frames.
        keypoints_tensor = results[0].keypoints.cpu()
        person_keypoints = keypoints_tensor.data[0]
        
        return person_keypoints.numpy()