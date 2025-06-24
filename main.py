import cv2
import os
import argparse

from config import CONFIG_ENTRADA, CONFIG_CAMERA
from src.posture_analysis import processar_frame, AnaliseExercicio
from src.report import Relatorio
from src.kalman_filter import LandmarkKalmanFilter
from src.pose_detector import PoseDetector

def main(input_path=None):
    """
    Função principal que executa a aplicação de análise de postura.

    Gerencia a seleção de exercícios, inicialização de fontes de mídia (webcam, vídeo ou imagem),
    e o loop principal de processamento de frames.
    
    Args:
        input_path (str, optional): Caminho para um arquivo de vídeo ou imagem. 
                                    Se fornecido, sobrepõe as configurações em config.py.
    """
    relatorio = Relatorio()
    mapa_exercicios = {'1': 'pushup', '2': 'squat'}
    escolha = ''

    while escolha not in mapa_exercicios:
        print("\nEscolha o exercício para analisar:")
        print("1: Flexão (Pushup)")
        print("2: Agachamento (Squat)")
        escolha = input("Digite o número (1 ou 2): ")

    exercicio_selecionado = mapa_exercicios[escolha]
    print(f"Modo de análise selecionado: {exercicio_selecionado.upper()}")

    # Determina a fonte de entrada
    modo = CONFIG_ENTRADA['modo']
    fonte = input_path
    if not fonte:
        if modo == 'video':
            fonte = CONFIG_ENTRADA['caminho_video']
            if not os.path.exists(fonte):
                print(f"ERRO: Arquivo de vídeo não encontrado em '{fonte}'")
                return
        elif modo == 'image':
             fonte = CONFIG_ENTRADA['caminho_imagem']
             if not os.path.exists(fonte):
                print(f"ERRO: Arquivo de imagem não encontrado em '{fonte}'")
                return
        else: 
            fonte = CONFIG_CAMERA['source']
    else: 
        if any(input_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
            modo = 'image'
        else:
            modo = 'video'


    print(f"Iniciando análise com a fonte: {fonte} (Modo: {modo})")
    print("Pressione 'ESC' na janela da imagem/vídeo para sair.")

    detector_pose = PoseDetector('yolov8s-pose.pt')
    analisador_exercicio = AnaliseExercicio()
    filtro_kalman = LandmarkKalmanFilter()
    
    if modo == 'image':
        frame = cv2.imread(fonte)
        if frame is None:
            print("Erro ao carregar a imagem.")
            return

        frame_processado, _ = processar_frame(
            frame, detector_pose, analisador_exercicio, filtro_kalman, exercicio_selecionado, relatorio
        )
        cv2.imshow(f'Analise de Postura - {exercicio_selecionado.upper()}', frame_processado)
        cv2.waitKey(0) 

    # Lógica para processar vídeo ou webcam
    else:
        cap = cv2.VideoCapture(fonte)
        if modo == 'webcam':
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG_CAMERA['largura'])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG_CAMERA['altura'])
        
        try:
            while cap.isOpened():
                sucesso, frame = cap.read()
                if not sucesso:
                    print("Fim da fonte de vídeo ou falha na captura.")
                    break
                
                frame_processado, _ = processar_frame(
                    frame, detector_pose, analisador_exercicio, filtro_kalman, exercicio_selecionado, relatorio
                )
                
                cv2.imshow(f'Analise de Postura - {exercicio_selecionado.upper()}', frame_processado)
                
                if cv2.waitKey(5) & 0xFF == 27:  # Tecla ESC para sair
                    break
        finally:
            cap.release()
            if relatorio.dados:
                relatorio.salvar()
                print(f"\nRelatório de dados salvo em '{relatorio.arquivo_relatorio}'")

    cv2.destroyAllWindows()
    print("Aplicação finalizada.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Análise de Postura em Exercícios de Calistenia.")
    parser.add_argument(
        '-i', '--input', 
        help="Caminho opcional para o arquivo de vídeo ou imagem a ser analisado."
    )
    args = parser.parse_args()
    main(args.input)