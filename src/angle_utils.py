import numpy as np

def calculate_angle_3d(keypoints, p1_idx, p2_idx, p3_idx):
    """
    Calcula o ângulo entre três keypoints 3D (p2 é o vértice).

    Args:
        keypoints (list): Lista de keypoints, onde cada keypoint é uma tupla (x, y, z, visibilidade).
        p1_idx (int): Índice do primeiro ponto.
        p2_idx (int): Índice do ponto do vértice (onde o ângulo é medido).
        p3_idx (int): Índice do terceiro ponto.

    Returns:
        float: O ângulo em graus, ou 0 se os pontos não puderem ser calculados.
    """
    if not keypoints or max(p1_idx, p2_idx, p3_idx) >= len(keypoints):
        return 0.0

    # Extrai as coordenadas 3D dos pontos
    p1 = np.array(keypoints[p1_idx][:3])
    p2 = np.array(keypoints[p2_idx][:3])
    p3 = np.array(keypoints[p3_idx][:3])

    # Cria os vetores a partir dos pontos
    v1 = p1 - p2
    v2 = p3 - p2
    
    # Calcula o produto escalar
    dot_product = np.dot(v1, v2)
    
    # Calcula a magnitude (norma) dos vetores
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    # Evita divisão por zero
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
        
    # Calcula o cosseno do ângulo e o converte para graus
    cosine_angle = dot_product / (norm_v1 * norm_v2)
    # Limita o valor entre -1 e 1 para evitar erros de domínio no arccos
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    
    return np.degrees(angle)