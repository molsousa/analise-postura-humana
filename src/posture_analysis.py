import cv2
import json
import os

from config import CONFIG_DESENHO, MODEL_CONFIG
from src.angle_utils import calcular_angulo, angulo_no_intervalo
from src.pose_detector import COCO_KEYPOINTS, COCO_POSE_CONNECTIONS

def obter_ponto(landmarks, nome_keypoint):
    """
    Extrai as coordenadas (x, y) de um landmark pelo nome.

    Args:
        landmarks (np.array): Array de landmarks da pose.
        nome_keypoint (str): Nome do keypoint (ex: 'right_shoulder').

    Returns:
        tuple: Coordenadas (x, y) ou None se o ponto não for válido.
    """
    idx = COCO_KEYPOINTS.get(nome_keypoint)
    if idx is None or landmarks is None or idx >= len(landmarks):
        return None
    
    lm = landmarks[idx]
    # Confere se o ponto tem confiança suficiente
    if lm[2] > MODEL_CONFIG['limiar_deteccao']:
        return (int(lm[0]), int(lm[1]))
    return None

def calcular_angulos_corpo(landmarks):
    """
    Calcula um dicionário com todos os ângulos corporais relevantes para os exercícios.

    Args:
        landmarks (np.array): Array de landmarks da pose.

    Returns:
        dict: Dicionário mapeando nomes de ângulos para seus valores em graus.
    """
    angulos = {}
    pontos = {kp: obter_ponto(landmarks, kp) for kp in COCO_KEYPOINTS}

    # Ângulo do cotovelo direito
    if all(pontos[kp] for kp in ['right_shoulder', 'right_elbow', 'right_wrist']):
        angulos['angulo_cotovelo_dir'] = calcular_angulo(pontos['right_shoulder'], pontos['right_elbow'], pontos['right_wrist'])
    
    # Ângulo do quadril direito
    if all(pontos[kp] for kp in ['right_shoulder', 'right_hip', 'right_knee']):
        angulos['angulo_quadril_dir'] = calcular_angulo(pontos['right_shoulder'], pontos['right_hip'], pontos['right_knee'])

    # Ângulo do joelho direito
    if all(pontos[kp] for kp in ['right_hip', 'right_knee', 'right_ankle']):
        angulos['angulo_joelho_dir'] = calcular_angulo(pontos['right_hip'], pontos['right_knee'], pontos['right_ankle'])
        
    # Ângulo de alinhamento da coluna
    if all(pontos[kp] for kp in ['right_shoulder', 'right_hip', 'right_ankle']):
        angulos['angulo_alinhamento_corpo'] = calcular_angulo(pontos['right_shoulder'], pontos['right_hip'], pontos['right_ankle'])
        
    # Simetria de ombros e quadris 
    if pontos['right_shoulder'] and pontos['left_shoulder']:
        angulos['simetria_ombros'] = abs(pontos['right_shoulder'][1] - pontos['left_shoulder'][1])
    if pontos['right_hip'] and pontos['left_hip']:
        angulos['simetria_quadris'] = abs(pontos['right_hip'][1] - pontos['left_hip'][1])
        
    return angulos

def carregar_regras_exercicio(nome_exercicio):
    """
    Carrega as regras de análise para um exercício específico de um arquivo JSON.

    Args:
        nome_exercicio (str): O nome do exercício (ex: 'pushup').

    Returns:
        dict: Dicionário com as regras do exercício ou None se o arquivo não for encontrado.
    """
    
    caminho_arquivo = f'exercise_templates/{nome_exercicio}.json'
    if not os.path.exists(caminho_arquivo):
        print(f"AVISO: Arquivo de regras '{caminho_arquivo}' não encontrado.")
        return None
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        return json.load(f)

class AnaliseExercicio:
    """
    Gerencia o estado e a lógica da análise de exercícios de forma genérica.

    Esta classe carrega as regras de um arquivo JSON correspondente ao exercício
    selecionado e as aplica aos ângulos corporais calculados a cada frame.
    """
    def __init__(self):
        self.exercicio_atual = None
        self.regras_exercicio = None
        self.fase_movimento = None 
        self.historico_feedback = {}

    def _obter_feedback_estavel(self, novas_msgs):
        """
        Filtra mensagens de feedback para evitar que pisquem na tela.

        Uma mensagem só é retornada se ela persistir por um número mínimo de frames,
        evitando alertas intermitentes e melhorando a experiência do usuário.

        Args:
            novas_msgs (list): Lista de mensagens de feedback geradas no frame atual.

        Returns:
            list: Lista de mensagens de feedback consideradas estáveis.
        """
        msgs_estaveis = []
        for msg in novas_msgs:
            self.historico_feedback[msg] = self.historico_feedback.get(msg, 0) + 1
        
        # Limpa contadores de mensagens que não apareceram mais
        keys_a_remover = [k for k in self.historico_feedback if k not in novas_msgs]
        for k in keys_a_remover:
            del self.historico_feedback[k]

        # Só mostra a mensagem se ela persistir por 3 frames
        for msg, contador in self.historico_feedback.items():
            if contador >= 3:
                msgs_estaveis.append(msg)
        return msgs_estaveis

    def analisar_forma(self, exercicio_selecionado, angulos):
        """
        Analisa a forma do exercício com base nas regras carregadas.

        Args:
            exercicio_selecionado (str): Nome do exercício atual.
            angulos (dict): Dicionário com os ângulos corporais calculados.

        Returns:
            dict: Dicionário contendo o texto de feedback e os pontos/conexões problemáticos.
        """
        if exercicio_selecionado != self.exercicio_atual:
            self.reset(exercicio_selecionado)

        if not self.regras_exercicio:
            return {"texto": f"Erro: Regras para '{exercicio_selecionado}' não carregadas.", 
                    "landmarks_problema": set(), "conexoes_problema": set()}

        landmarks_problema = set()
        conexoes_problema = set()
        msgs_feedback = []

        # 1. Determinar a fase do movimento
        self._determinar_fase(angulos)
        
        # 2. Aplicar regras de validação
        for regra in self.regras_exercicio['regras_validacao']:
            angulo_a_verificar = angulos.get(regra['angulo'])
            if angulo_a_verificar is None:
                continue

            # Verifica se a regra se aplica à fase atual do movimento
            if 'fase' in regra and self.fase_movimento != regra['fase']:
                continue

            limite_valido = regra['limite']
            if not angulo_no_intervalo(angulo_a_verificar, *limite_valido):
                msgs_feedback.append(regra['feedback'])
                landmarks_problema.update(regra['landmarks_associados'])
                for p1, p2 in zip(regra['landmarks_associados'][:-1], regra['landmarks_associados'][1:]):
                    conexoes_problema.add(tuple(sorted((p1, p2))))

        # 3. Gerar texto de feedback
        feedback_estavel = self._obter_feedback_estavel(msgs_feedback)
        texto_feedback = f"{self.exercicio_atual.upper()}: "
        texto_feedback += " | ".join(feedback_estavel) if feedback_estavel else "FORMA CORRETA"
            
        return {
            "texto": texto_feedback, 
            "landmarks_problema": landmarks_problema,
            "conexoes_problema": conexoes_problema
        }

    def _determinar_fase(self, angulos):
        """Determina a fase atual do movimento (ascendente/descendente)."""
        regra_fase = self.regras_exercicio['regra_fase']
        angulo_chave = angulos.get(regra_fase['angulo'])
        if angulo_chave is None:
            return

        if angulo_chave < regra_fase['limiar_descendente']:
            self.fase_movimento = 'descendente'
        elif angulo_chave > regra_fase['limiar_ascendente']:
            self.fase_movimento = 'ascendente'
            
    def reset(self, novo_exercicio):
        """Reseta o estado da análise para um novo exercício."""
        self.exercicio_atual = novo_exercicio
        self.regras_exercicio = carregar_regras_exercicio(novo_exercicio)
        self.fase_movimento = None
        self.historico_feedback.clear()

def desenhar_feedback(frame, texto_feedback, fase_movimento):
    """Desenha o texto de feedback e o indicador de fase no frame."""
    # Divide o texto em linhas se houver múltiplos feedbacks
    linhas = texto_feedback.split(" | ")
    
    y_pos = 40
    for i, linha in enumerate(linhas):
        posicao_texto = (20, y_pos + i * 30)
        (w, h), _ = cv2.getTextSize(linha, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        cv2.rectangle(frame, (posicao_texto[0]-10, posicao_texto[1]-h-5), (posicao_texto[0]+w+10, posicao_texto[1]+10), (0,0,0,0.5), -1)
        cv2.putText(frame, linha, posicao_texto, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Adiciona indicador de fase
    if fase_movimento:
        fase_texto = f"FASE: {fase_movimento.upper()}"
        cv2.putText(frame, fase_texto, (20, frame.shape[0] - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 255, 0), 2)

def desenhar_esqueleto(frame, landmarks, landmarks_problema, conexoes_problema):
    """Desenha os landmarks e as conexões do esqueleto no frame."""
    if landmarks is None:
        return

    # Desenha todas as conexões
    for p1_idx, p2_idx in COCO_POSE_CONNECTIONS:
        nome_p1 = next((k for k, v in COCO_KEYPOINTS.items() if v == p1_idx), None)
        nome_p2 = next((k for k, v in COCO_KEYPOINTS.items() if v == p2_idx), None)
        
        if landmarks[p1_idx][2] > MODEL_CONFIG['limiar_deteccao'] and landmarks[p2_idx][2] > MODEL_CONFIG['limiar_deteccao']:
            p1 = (int(landmarks[p1_idx][0]), int(landmarks[p1_idx][1]))
            p2 = (int(landmarks[p2_idx][0]), int(landmarks[p2_idx][1]))
            
            conexao = tuple(sorted((nome_p1, nome_p2)))
            is_problem = conexao in conexoes_problema
            
            cor = CONFIG_DESENHO['cor_erro'] if is_problem else CONFIG_DESENHO['cor_conexao']
            espessura = CONFIG_DESENHO['espessura_erro'] if is_problem else CONFIG_DESENHO['espessura_conexao']
            cv2.line(frame, p1, p2, cor, espessura)

    # Desenha os landmarks
    for nome_key, idx in COCO_KEYPOINTS.items():
        if landmarks[idx][2] > MODEL_CONFIG['limiar_deteccao']:
            ponto = (int(landmarks[idx][0]), int(landmarks[idx][1]))
            is_problem = nome_key in landmarks_problema
            
            cor = CONFIG_DESENHO['cor_erro'] if is_problem else CONFIG_DESENHO['cor_correto']
            tamanho = CONFIG_DESENHO['raio_landmark_erro'] if is_problem else CONFIG_DESENHO['raio_landmark']
            cv2.circle(frame, ponto, tamanho, cor, cv2.FILLED)
            
def processar_frame(frame, detector, analisador, filtro_kalman, exercicio_selecionado, relatorio):
    """
    Orquestra o pipeline de processamento para um único frame.
    
    Aplica detecção de pose, filtragem, análise de forma e desenho dos resultados.

    Returns:
        tuple: Uma tupla contendo o frame processado (imagem) e os dados de feedback (dict).
    """
    landmarks_detectados = detector.detectar(frame)
    landmarks_filtrados = filtro_kalman.aplicar(landmarks_detectados)

    if landmarks_filtrados is None or landmarks_filtrados.size == 0:
        cv2.putText(frame, "Nenhuma pessoa detectada", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return frame, None

    angulos = calcular_angulos_corpo(landmarks_filtrados)
    dados_feedback = analisador.analisar_forma(exercicio_selecionado, angulos)
    
    if dados_feedback and relatorio:
        relatorio.adicionar_dados(exercicio_selecionado, angulos, dados_feedback["texto"])

    desenhar_esqueleto(frame, landmarks_filtrados, dados_feedback["landmarks_problema"], dados_feedback["conexoes_problema"])
    desenhar_feedback(frame, dados_feedback["texto"], analisador.fase_movimento)
    
    return frame, dados_feedback