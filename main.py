import cv2
import argparse

from src.posture_analysis import PostureAnalyzer
from src.pose_detector import MediaPipePoseDetector
from src.kalman_smoother import KalmanPointSmoother
from src.report import Relatorio
from config import CONFIG_DESENHO
import mediapipe as mp

def draw_smoothed_landmarks(image, landmarks):
    """Desenha os landmarks suavizados (uma lista de tuplas) na imagem."""
    
    # Obtém as conexões padrão do MediaPipe Pose
    connections = mp.solutions.pose.POSE_CONNECTIONS
    
    # Converte os landmarks de coordenadas normalizadas para pixels
    h, w, _ = image.shape
    pixel_landmarks = []
    for lm in landmarks:
        # Ignora pontos com visibilidade muito baixa para não poluir a tela
        if lm[3] > 0.1: # lm[3] é a visibilidade
            pixel_landmarks.append((int(lm[0] * w), int(lm[1] * h)))
        else:
            # Adiciona um placeholder para manter os índices corretos
            pixel_landmarks.append(None)

    # Desenha as conexões
    if connections:
        for connection in connections:
            start_idx = connection[0]
            end_idx = connection[1]
            if start_idx < len(pixel_landmarks) and end_idx < len(pixel_landmarks):
                start_point = pixel_landmarks[start_idx]
                end_point = pixel_landmarks[end_idx]
                if start_point and end_point:
                    cv2.line(image, start_point, end_point, (255, 255, 0), 2) # Cor Ciano

    # Desenha os landmarks (pontos)
    for point in pixel_landmarks:
        if point:
            cv2.circle(image, point, 5, (0, 0, 255), -1)

def main(exercise_config, video_path=0):
    """
    Função principal para executar a análise de postura em tempo real.

    Args:
        exercise_config (str): Caminho para o arquivo de configuração JSON do exercício.
        video_path (str or int): Caminho para o arquivo de vídeo ou ID da webcam (padrão: 0).
    """
    # --- 1. Inicialização dos Componentes ---
    detector = MediaPipePoseDetector(model_complexity=1, min_detection_confidence=0.4)
    analyzer = PostureAnalyzer(exercise_config_path=exercise_config, pose_detector=detector)
    
    smoother = KalmanPointSmoother(visibility_threshold=0.65)
    
    reporter = Relatorio()

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
        
        # --- 2.1. Detecção de Pose ---
        raw_keypoints, pose_landmarks_results = detector.detect_pose(frame)
        
        if raw_keypoints:
            # --- 2.2. Suavização e Predição dos Keypoints ---
            # Aplica o filtro de Kalman para suavizar e estimar pontos ocluídos.
            smoothed_keypoints = smoother.smooth(raw_keypoints)

            # --- 2.3. Análise da Postura ---
            image_shape = frame.shape[:2]
            calculated_angles = analyzer.analyze(smoothed_keypoints, image_shape)

            # --- 2.4. Geração de Relatório ---
            if calculated_angles:
                reporter.adicionar_dados(
                    exercicio=analyzer.exercise_name,
                    angulos=calculated_angles,
                    feedback_text=analyzer.feedback,
                    feedback_type=analyzer.feedback_type
                )
        else:
            analyzer.analyze([], None)

        # --- 3. Visualização dos Resultados ---
        
        if 'smoothed_keypoints' in locals() and smoothed_keypoints:
             draw_smoothed_landmarks(frame, smoothed_keypoints)
        
        feedback_color = CONFIG_DESENHO['cores_feedback'].get(analyzer.feedback_type, (255, 255, 255))

        cv2.putText(frame, f"Exercicio: {analyzer.exercise_name}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Reps: {analyzer.counter}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Feedback:", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.9, feedback_color, 2, cv2.LINE_AA)
        
        y0, dy = 180, 25
        for i, line in enumerate(analyzer.feedback.split('\n')):
            y = y0 + i * dy
            cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, feedback_color, 2, cv2.LINE_AA)

        cv2.imshow('Analise de Postura', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # --- 4. Finalização ---
    print("Salvando relatório da sessão...")
    reporter.salvar()
    print(f"Relatório salvo em: {reporter.arquivo_relatorio}")
    
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