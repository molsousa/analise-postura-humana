import cv2
import argparse
import numpy as np

from src.posture_analysis import PostureAnalyzer
from src.pose_detector import MediaPipePoseDetector
from src.point_smoother import PointSmoother
from src.report import Relatorio
from config import CONFIG_DESENHO

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
    # O PointSmoother (OneEuroFilter) é ideal para suavizar o jitter dos landmarks em tempo real.
    smoother = PointSmoother(min_cutoff=1.0, beta=0.8, d_cutoff=1.0) 
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
        # Detecta os keypoints (landmarks) no frame atual. Retorna os pontos brutos e os resultados do MediaPipe.
        raw_keypoints, pose_landmarks_results = detector.detect_pose(frame)
        
        # Prossegue apenas se uma pose for detectada.
        if raw_keypoints:
            # --- 2.2. Suavização dos Keypoints ---
            # Aplica o filtro One-Euro para reduzir o ruído e a instabilidade dos pontos detectados.
            # Este filtro opera em 3D, preservando todas as informações espaciais.
            smoothed_keypoints = smoother.smooth(raw_keypoints)

            # --- 2.3. Análise da Postura ---
            # O analisador calcula os ângulos com base nos pontos suavizados e aplica as regras do PDF.
            image_shape = frame.shape[:2]
            calculated_angles = analyzer.analyze(smoothed_keypoints, image_shape)

            # --- 2.4. Geração de Relatório ---
            # Adiciona os dados do frame atual (ângulos, feedback, etc.) ao relatório da sessão.
            if calculated_angles:
                reporter.adicionar_dados(
                    exercicio=analyzer.exercise_name,
                    angulos=calculated_angles,
                    feedback_text=analyzer.feedback,
                    feedback_type=analyzer.feedback_type # 'CORRETO', 'ATENCAO', 'ERRO'
                )
        else:
            # Se nenhum keypoint for detectado, reseta a análise.
            analyzer.analyze([], None)

        # --- 3. Visualização dos Resultados ---
        # Desenha os landmarks e conexões da pose no frame.
        detector.draw_landmarks(frame, pose_landmarks_results)
        
        # Define a cor do texto de feedback com base na correção da postura.
        feedback_color = CONFIG_DESENHO['cores_feedback'].get(analyzer.feedback_type, (255, 255, 255))

        # Exibe as informações na tela.
        cv2.putText(frame, f"Exercicio: {analyzer.exercise_name}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Reps: {analyzer.counter}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Feedback:", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.9, feedback_color, 2, cv2.LINE_AA)
        
        # Quebra o feedback em múltiplas linhas se for muito longo.
        y0, dy = 180, 25
        for i, line in enumerate(analyzer.feedback.split('\n')):
            y = y0 + i * dy
            cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, feedback_color, 2, cv2.LINE_AA)


        cv2.imshow('Analise de Postura', frame)

        # Condição de parada: pressionar a tecla 'q'.
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