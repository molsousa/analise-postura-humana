import math

def calcular_angulo(ponto_a, ponto_b, ponto_c):
    """
    Calcula o ângulo (em graus) formado por três pontos, onde ponto_b é o vértice.

    O cálculo é baseado no produto escalar dos vetores BA e BC. O resultado é
    sempre um ângulo positivo entre 0 e 180 graus.

    Args:
        ponto_a (tuple): Coordenadas (x, y) do primeiro ponto.
        ponto_b (tuple): Coordenadas (x, y) do ponto do vértice.
        ponto_c (tuple): Coordenadas (x, y) do terceiro ponto.

    Returns:
        float: O ângulo calculado em graus. Retorna 0.0 se algum dos vetores
               tiver comprimento zero para evitar divisão por zero.
    """
    # Coordenadas dos pontos
    ax, ay = ponto_a
    bx, by = ponto_b
    cx, cy = ponto_c

    # Vetores BA e BC
    vetor_ba = (ax - bx, ay - by)
    vetor_bc = (cx - bx, cy - by)

    # Produto escalar dos vetores
    produto_escalar = vetor_ba[0] * vetor_bc[0] + vetor_ba[1] * vetor_bc[1]

    # Magnitude (comprimento) dos vetores
    mag_ba = math.sqrt(vetor_ba[0]**2 + vetor_ba[1]**2)
    mag_bc = math.sqrt(vetor_bc[0]**2 + vetor_bc[1]**2)

    # Evita divisão por zero
    if mag_ba == 0 or mag_bc == 0:
        return 0.0

    # Garante que o valor do cosseno esteja em [-1, 1] para evitar erros no acos
    cos_angulo = max(min(produto_escalar / (mag_ba * mag_bc), 1.0), -1.0)
    
    # Converte o ângulo de radianos para graus
    angulo_rad = math.acos(cos_angulo)
    angulo_graus = math.degrees(angulo_rad)

    return angulo_graus

def angulo_no_intervalo(angulo, min_val, max_val):
    """
    Verifica se um ângulo está dentro de um intervalo [min_val, max_val].

    Args:
        angulo (float): O ângulo a ser verificado.
        min_val (float): O valor mínimo do intervalo.
        max_val (float): O valor máximo do intervalo.

    Returns:
        bool: True se o ângulo estiver no intervalo, False caso contrário.
    """
    return min_val <= angulo <= max_val