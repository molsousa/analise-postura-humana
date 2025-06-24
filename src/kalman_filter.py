import cv2
import numpy as np

from config import MODEL_CONFIG

NUM_LANDMARKS = 17 

class LandmarkKalmanFilter:
    """
    Aplica um Filtro de Kalman para suavizar a detecção de landmarks de pose.

    Cria um filtro de Kalman independente para cada um dos 17 landmarks do corpo,
    reduzindo o "tremor" (jitter) nas posições detectadas entre frames consecutivos
    e fornecendo uma estimativa mais estável da pose.
    """
    def __init__(self):
        """Inicializa a lista de filtros, um para cada landmark."""
        self.filtros = [self._criar_filtro() for _ in range(NUM_LANDMARKS)]

    def _criar_filtro(self):
        """
        Cria e configura uma única instância do Filtro de Kalman do OpenCV.

        O filtro é configurado para um modelo de movimento de velocidade constante.

        Returns:
            cv2.KalmanFilter: Uma instância configurada do filtro de Kalman.
        """
        kalman = cv2.KalmanFilter(4, 2)  # 4 estados (x, y, vx, vy), 2 medições (x, y)
        
        # Matriz de medição [H]: relaciona o estado com a medição.
        kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        
        # Matriz de transição [A]: prediz o próximo estado a partir do atual.
        kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
        
        # Covariância do ruído do processo [Q]: incerteza do modelo de movimento.
        kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.05
        
        # Covariância do ruído da medição [R]: incerteza do detector de pose.
        kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.01
        
        return kalman

    def aplicar(self, landmarks):
        """
        Aplica o filtro de Kalman aos landmarks detectados em um frame.

        Para cada landmark, o método primeiro prediz sua nova posição com base no
        estado anterior e, em seguida, corrige essa predição usando a medição atual
        (se a detecção for confiável).

        Args:
            landmarks (np.array): Array de shape (17, 3) com (x, y, confiança)
                                  vindo do detector de pose.

        Returns:
            np.array: Array de landmarks suavizados com o mesmo shape, ou None se a
                      entrada for None.
        """
        if landmarks is None:
            return None

        landmarks_filtrados = np.zeros_like(landmarks)
        limiar_confianca = MODEL_CONFIG['limiar_rastreamento']

        for i, lm in enumerate(landmarks):
            filtro = self.filtros[i]
            
            # 1. Prediz a próxima posição do landmark
            predicao = filtro.predict()

            # 2. Corrige o estado se a detecção atual for confiável
            if lm[2] > limiar_confianca:
                medicao = np.array([lm[0], lm[1]], dtype=np.float32)
                filtro.correct(medicao)
            
            # O estado posterior (statePost) é a nossa melhor estimativa da posição
            estado_corrigido = filtro.statePost
            landmarks_filtrados[i] = (estado_corrigido[0, 0], estado_corrigido[1, 0], lm[2])
            
        return landmarks_filtrados