import cv2
import argparse
import json
import mediapipe as mp

from src.posture_analysis import PostureAnalyzer
from src.pose_detector import MediaPipePoseDetector
from src.kalman_smoother import KalmanPointSmoother
from src.report import Log
from config import COLOR_CONFIG

def draw_smoothed_landmarks(image, landmarks, detector, landmarks_to_hide=None):
    if landmarks_to_hide is None:
        landmarks_to_hide = []
    
    hide_indices = {detector.get_landmark_index(name) for name in landmarks_to_hide}

    connections = mp.solutions.pose.POSE_CONNECTIONS
    h, w, _ = image.shape
    pixel_landmarks = []
    for i, lm in enumerate(landmarks):
        if i in hide_indices or lm[3] < 0.1:
            pixel_landmarks.append(None)
        else:
            pixel_landmarks.append((int(lm[0] * w), int(lm[1] * h)))

    if connections:
        for connection in connections:
            start_idx, end_idx = connection
            if start_idx in hide_indices or end_idx in hide_indices:
                continue
            if start_idx < len(pixel_landmarks) and end_idx < len(pixel_landmarks):
                start_point, end_point = pixel_landmarks[start_idx], pixel_landmarks[end_idx]
                if start_point and end_point:
                    cv2.line(image, start_point, end_point, (255, 255, 0), 2)

    for i, point in enumerate(pixel_landmarks):
        if point:
            cv2.circle(image, point, 5, (0, 0, 255), -1)

def main(exercise_config, video_path=0):
    # --- MODO DE DEPURACAO ---
    DEBUG_MODE = True
    
    # --- 1. Inicialização dos Componentes ---
    detector = MediaPipePoseDetector(model_complexity=1, min_detection_confidence=0.4)
    analyzer = PostureAnalyzer(exercise_config_path=exercise_config, pose_detector=detector)
    
    with open(exercise_config, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
        
    filter_params = config_data.get('kalman_filter_params', {'R': 5, 'Q': 0.1})
    smoother = KalmanPointSmoother(
        R=filter_params['R'],
        Q=filter_params['Q'],
        visibility_threshold=0.65
    )
    
    reporter = Log(exercise_config=config_data)
    landmarks_to_hide = config_data.get('landmarks_to_hide', [])

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Erro: Não foi possível abrir o vídeo em {video_path}")
        return

    print(">>> Análise iniciada. Pressione 'q' para sair.")

    # --- 2. Loop Principal de Processamento de Vídeo ---
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Fim do vídeo ou erro na captura.")
            break
        
        raw_keypoints, pose_landmarks_results = detector.detect_pose(frame)
        
        smoothed_keypoints = []
        calculated_angles = {}
        if raw_keypoints:
            smoothed_keypoints = smoother.smooth(raw_keypoints)
            calculated_angles = analyzer.analyze(smoothed_keypoints, frame.shape[:2], reporter)
        else:
            analyzer.analyze([], None, reporter)

        # --- 3. Visualização dos Resultados ---
        if smoothed_keypoints:
             draw_smoothed_landmarks(frame, smoothed_keypoints, detector, landmarks_to_hide)
        
        # --- LÓGICA DO MODO DE DEPURACAO ---
        if DEBUG_MODE and calculated_angles and smoothed_keypoints:
            h, w, _ = frame.shape
            for angle_def in analyzer.angle_definitions:
                angle_name = angle_def['name']
                angle_value = calculated_angles.get(angle_name)
                
                if angle_value is not None:
                    vertex_index = angle_def['indices'][1]
                    vertex_point = smoothed_keypoints[vertex_index]
                    text_pos = (int(vertex_point[0] * w) + 10, int(vertex_point[1] * h))
                    
                    # Cria um rótulo mais curto e único para evitar sobreposição
                    label = angle_name.replace('_', ' ').replace('flexion', '').replace('angle', '')
                    cv2.putText(frame, f"{label.strip()}: {int(angle_value)}", text_pos, 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1, cv2.LINE_AA)

        feedback_color = COLOR_CONFIG['feedback_color'].get(analyzer.feedback_type, (255, 255, 255))

        cv2.putText(frame, f"Exercicio: {analyzer.exercise_name}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Reps: {analyzer.counter}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Posicao: {analyzer.body_orientation}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Feedback:", (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.9, feedback_color, 2, cv2.LINE_AA)
        
        y0, dy = 200, 25
        for i, line in enumerate(analyzer.feedback.split('\n')):
            y = y0 + i * dy
            cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, feedback_color, 2, cv2.LINE_AA)

        cv2.imshow('Analise de Postura', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # --- 4. Finalização ---
    print("Salvando resumo da sessão...")
    reporter.save()
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Análise de Postura em Exercícios de Calistenia.')
    parser.add_argument('--exercise', type=str, required=True, help='Caminho para o arquivo de configuração do exercício (JSON).')
    parser.add_argument('--video', type=str, default="0", help='Caminho para o arquivo de vídeo ou "0" para usar a webcam.')
    
    args = parser.parse_args()
    
    video_input = 0 if args.video == "0" else args.video
    if isinstance(video_input, str) and video_input.isdigit():
        video_input = int(video_input)

    main(args.exercise, video_input)