import numpy as np
from filterpy.kalman import KalmanFilter
import mediapipe as mp

# Obtém os nomes dos landmarks para fácil acesso
PoseLandmark = mp.solutions.pose.PoseLandmark

class KalmanPointFilter:
    """ Gerencia um Filtro de Kalman para um único ponto 3D. (Sem alterações aqui) """
    def __init__(self, R=5, Q=0.1):
        self.kf = KalmanFilter(dim_x=6, dim_z=3)
        dt = 1.0
        self.kf.F = np.array([[1,0,0,dt,0,0], [0,1,0,0,dt,0], [0,0,1,0,0,dt],
                              [0,0,0,1,0,0], [0,0,0,0,1,0], [0,0,0,0,0,1]], dtype=float)
        self.kf.H = np.array([[1,0,0,0,0,0], [0,1,0,0,0,0], [0,0,1,0,0,0]], dtype=float)
        self.kf.R *= R
        self.kf.Q = np.eye(6) * Q
        self.kf.x = np.zeros((6, 1))

    def update(self, point):
        self.kf.update(np.array(point[:3]).reshape(3, 1))

    def predict(self):
        self.kf.predict()
        return self.kf.x[:3].flatten()

class KalmanPointSmoother:
    """
    Aplica o Filtro de Kalman com uma heurística de simetria para suavizar e prever
    a posição de uma lista de pontos 3D de uma pose humana.
    """
    def __init__(self, visibility_threshold=0.65):
        self.filters = {}
        self.visibility_threshold = visibility_threshold
        
        # --- Mapeamento de pontos simétricos ---
        self.symmetric_pairs = {
            PoseLandmark.LEFT_SHOULDER: PoseLandmark.RIGHT_SHOULDER,
            PoseLandmark.LEFT_ELBOW: PoseLandmark.RIGHT_ELBOW,
            PoseLandmark.LEFT_WRIST: PoseLandmark.RIGHT_WRIST,
            PoseLandmark.LEFT_HIP: PoseLandmark.RIGHT_HIP,
            PoseLandmark.LEFT_KNEE: PoseLandmark.RIGHT_KNEE,
            PoseLandmark.LEFT_ANKLE: PoseLandmark.RIGHT_ANKLE,
            PoseLandmark.LEFT_HEEL: PoseLandmark.RIGHT_HEEL,
            PoseLandmark.LEFT_FOOT_INDEX: PoseLandmark.RIGHT_FOOT_INDEX
        }
        # Adiciona o mapeamento reverso automaticamente
        self.symmetric_pairs.update({v: k for k, v in self.symmetric_pairs.items()})

    def smooth(self, points):
        if not points:
            return []

        smoothed_points = []
        
        # Armazena a visibilidade de cada ponto para a lógica de simetria
        visibilities = [p[3] for p in points]

        for i, point in enumerate(points):
            px, py, pz, visibility = point

            if i not in self.filters:
                self.filters[i] = KalmanPointFilter()
                self.filters[i].kf.x[:3] = np.array([[px], [py], [pz]])

            # --- LÓGICA DE SIMETRIA APLICADA ANTES DA PREDIÇÃO ---
            if visibility < self.visibility_threshold:
                # O ponto atual está ocluído, vamos tentar usar seu par simétrico
                symmetric_partner_idx = self.symmetric_pairs.get(i)
                
                if symmetric_partner_idx is not None and visibilities[symmetric_partner_idx] > self.visibility_threshold:
                    # O par simétrico está visível! Vamos copiar sua velocidade.
                    partner_filter = self.filters[symmetric_partner_idx]
                    current_filter = self.filters[i]
                    
                    # Copia o vetor de velocidade (vx, vy, vz) do par para o filtro atual
                    partner_velocity = partner_filter.kf.x[3:]
                    current_filter.kf.x[3:] = partner_velocity

            # 1. Etapa de PREDIÇÃO: Sempre predizemos o próximo estado
            predicted_pos = self.filters[i].predict()

            # 2. Etapa de ATUALIZAÇÃO: Apenas se a medição for confiável
            if visibility > self.visibility_threshold:
                self.filters[i].update(point)
                final_pos = self.filters[i].kf.x[:3].flatten()
            else:
                # Se o ponto está ocluído, usamos a predição (que agora pode ter sido
                # influenciada pela velocidade do seu par simétrico).
                final_pos = predicted_pos

            smoothed_points.append((*final_pos, visibility))
            
        return smoothed_points