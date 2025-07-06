import cv2
import numpy as np

class LandmarkKalmanFilter:
    """
    Aplica um Filtro de Kalman para suavizar a detecção de landmarks de pose.
    """
    def __init__(self, num_landmarks):
        """Inicializa a lista de filtros, um para cada landmark."""
        self.num_landmarks = num_landmarks
        self.filtros = [self._criar_filtro() for _ in range(self.num_landmarks)]

    def _criar_filtro(self):
        """
        Cria e configura uma única instância do Filtro de Kalman do OpenCV.
        """
        kalman = cv2.KalmanFilter(4, 2)
        kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
        kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.05
        kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.01
        return kalman

    def aplicar(self, landmarks):
        """
        Aplica o filtro de Kalman aos landmarks detectados em um frame.
        """
        if landmarks is None or len(landmarks) != self.num_landmarks:
            return None

        landmarks_filtrados = np.zeros_like(landmarks)
        limiar_confianca = 0.5 

        for i, lm in enumerate(landmarks):
            filtro = self.filtros[i]
            
            predicao = filtro.predict()

            if lm[2] > limiar_confianca:
                medicao = np.array([lm[0], lm[1]], dtype=np.float32)
                filtro.correct(medicao)
            
            estado_corrigido = filtro.statePost
            landmarks_filtrados[i] = (estado_corrigido[0, 0], estado_corrigido[1, 0], lm[2])
            
        return landmarks_filtrados