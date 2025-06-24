"""
Arquivo de configuração principal do projeto de análise de postura.
"""

# Modo: 'webcam', 'video' ou 'image'.
CONFIG_ENTRADA = {
    'modo': 'video',  # Opções: 'video', 'webcam', 'image'
    'caminho_video': 'videos/video2.mp4', # Usado no modo 'video'
    'caminho_imagem': 'images/squat_test.jpg' # Usado no modo 'image'
}

# Parâmetros para o modelo de detecção de pose (YOLOv8) e filtro.
MODEL_CONFIG = {
    'limiar_deteccao': 0.6,      # Confiança mínima para um keypoint ser considerado válido.
    'limiar_rastreamento': 0.5   # Confiança mínima para o filtro de Kalman usar a medição.
}

# Usado apenas no modo 'webcam'.
CONFIG_CAMERA = {
    'source': 0,      
    'largura': 1280,
    'altura': 720,
}

# Cores e tamanhos para a visualização do esqueleto e feedback.
CONFIG_DESENHO = {
    'cor_correto': (0, 255, 0),         # Verde
    'cor_erro': (0, 0, 255),            # Vermelho
    'cor_conexao': (255, 255, 255),     # Branco
    'raio_landmark': 7,
    'raio_landmark_erro': 10,
    'espessura_conexao': 3,
    'espessura_erro': 5 
}

CONFIG_RELATORIO = {
    'diretorio_logs': 'logs',
    'arquivo_dados': 'logs/dados_sessao.csv'
}