import cv2
import json
import mediapipe as mp
import numpy as np
from src.posture_analysis import PostureAnalyzer
from src.pose_detector import MediaPipePoseDetector
from src.kalman_smoother import KalmanPointSmoother
from src.report import Log

class CameraManager:
    """
    Gerencia a captura e processamento, separando dados de lógica de apresentação.
    """
    def __init__(self, exercise_config_path, video_source=0):
        self.video_source = video_source
        self.cap = cv2.VideoCapture(video_source)
        
        # Inicializa Detector e Analisador
        self.detector = MediaPipePoseDetector(model_complexity=1, min_detection_confidence=0.4)
        self.analyzer = PostureAnalyzer(exercise_config_path=exercise_config_path, pose_detector=self.detector)
        
        with open(exercise_config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            
        filter_params = config_data.get('kalman_filter_params', {'R': 5, 'Q': 0.1})
        self.smoother = KalmanPointSmoother(R=filter_params['R'], Q=filter_params['Q'])
        
        self.reporter = Log(exercise_config=config_data)
        self.landmarks_to_hide = config_data.get('landmarks_to_hide', [])
        
        # Status inicial
        self.current_status = {
            "reps": 0,
            "phase": "INICIANDO",
            "feedback": "Aguardando...",
            "feedback_type": "INFO",
            "last_rep_time": 0 # Adicionado para efeito visual no frontend se desejar
        }

    def get_frame(self):
        success, frame = self.cap.read()
        if not success:
            if isinstance(self.video_source, str):
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                success, frame = self.cap.read()
            if not success: return None

        raw_keypoints, _ = self.detector.detect_pose(frame)
        smoothed_keypoints = []

        if raw_keypoints:
            smoothed_keypoints = self.smoother.smooth(raw_keypoints)
            self.analyzer.analyze(smoothed_keypoints, frame.shape[:2], self.reporter)
        else:
            self.analyzer.analyze([], None, self.reporter)

        # ATUALIZAÇÃO DO STATUS: Aqui garantimos que os dados vão separados para o HTML
        self.current_status = {
            "reps": self.analyzer.counter,         # Dado Numérico
            "phase": self.analyzer.movement_phase, # Dado de Estado
            "feedback": self.analyzer.feedback,    # Dado Qualitativo (Texto de Correção)
            "feedback_type": self.analyzer.feedback_type # Dado de Estilo (Cor)
        }

        if smoothed_keypoints:
            self._draw_skeleton(frame, smoothed_keypoints)

        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()

    def _draw_skeleton(self, image, landmarks):
        h, w, _ = image.shape
        hide_index = {self.detector.get_landmark_index(name) for name in self.landmarks_to_hide}
        connections = mp.solutions.pose.POSE_CONNECTIONS
        pixel_landmarks = []
        for i, lm in enumerate(landmarks):
            if i in hide_index or lm[3] < 0.1: pixel_landmarks.append(None)
            else: pixel_landmarks.append((int(lm[0] * w), int(lm[1] * h)))
        if connections:
            for connection in connections:
                start, end = connection
                if start in hide_index or end in hide_index: continue
                if start < len(pixel_landmarks) and end < len(pixel_landmarks):
                    p1, p2 = pixel_landmarks[start], pixel_landmarks[end]
                    if p1 and p2: cv2.line(image, p1, p2, (255, 255, 0), 2)
        for p in pixel_landmarks:
            if p: cv2.circle(image, p, 5, (0, 0, 255), -1)

    def get_final_report(self):
        self.reporter.save()
        return self.reporter.get_report_content()
    
    def __del__(self):
        if self.cap.isOpened(): self.cap.release()