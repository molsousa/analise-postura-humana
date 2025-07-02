"""
Arquivo de configuração principal do projeto de análise de postura.
"""

# Cores e tamanhos para a visualização do esqueleto e feedback.
CONFIG_DESENHO = {
    # Dicionário aninhado para as cores do feedback, mapeando o tipo de feedback para uma cor BGR
    'cores_feedback': {
        'INFO': (255, 255, 255),    
        'CORRETO': (0, 255, 0),    
        'ATENCAO': (0, 255, 255),   
        'ERRO_CRITICO': (0, 0, 255) 
    },
    
    # Configurações de desenho para os landmarks e conexões da pose
    'cor_conexao': (255, 255, 255),
    'raio_landmark': 5,
    'espessura_conexao': 2,
}

# Configurações para o relatório de sessão
CONFIG_RELATORIO = {
    'diretorio_logs': 'logs'
}