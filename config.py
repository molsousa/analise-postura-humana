"""
Arquivo de configuração principal do projeto de análise de postura.
"""

# Cores e tamanhos para a visualização do esqueleto e feedback.
COLOR_CONFIG = {
    # Dicionário aninhado para as cores do feedback, mapeando o tipo de feedback para uma cor BGR
    'feedback_color': {
        'INFO': (255, 255, 255),    
        'CORRETO': (0, 255, 0),    
        'ATENCAO': (0, 255, 255),   
        'ERRO_CRITICO': (0, 0, 255) 
    },
    
    # Configurações de desenho para os landmarks e conexões da pose
    'conection_color': (255, 255, 255), # Cores da conexão
    'landmark_radius': 5,                # Raio
    'connection_thickness': 2,          # Espessura da conexão
}

# Configurações para o relatório de sessão
LOG_CONFIG = {
    'dir_logs': 'logs'
}