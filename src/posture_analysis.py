import json
import time
from src.angle_utils import calculate_angle_3d

class PostureAnalyzer:
    """
    Analisa a postura com base em keypoints 3D e um arquivo de configuração de exercício.
    Implementa lógicas separadas e robustas para contagem de repetições e feedback de postura.
    """
    def __init__(self, exercise_config_path, pose_detector):
        self.detector = pose_detector
        with open(exercise_config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.exercise_name = self.config['name']
        self.rules = self.config['rules']
        
        self.angle_definitions = []
        for angle_name, joints in self.config['angle_definitions'].items():
            indices = [self.detector.get_landmark_index(j) for j in joints]
            if None in indices:
                raise ValueError(f"Nome de articulação inválido para o ângulo '{angle_name}'")
            self.angle_definitions.append({'name': angle_name, 'indices': indices})

        # --- LÓGICA DE CONTAGEM DE REPETIÇÕES (INDEPENDENTE) ---
        self.rep_state = "up"  # Pode ser 'up' ou 'down'
        self.counter = 0

        # --- LÓGICA DE FEEDBACK (POSTURA + REPETIÇÃO TEMPORÁRIA) ---
        self.feedback = "Inicie o exercicio."
        self.feedback_type = "INFO"
        self.rep_complete_feedback_end_time = 0  # Timestamp para esconder a msg "Repetição X!"

    def _get_keypoint_visibility(self, keypoints, indices):
        if not keypoints: return 0.0
        visibilities = [keypoints[i][3] for i in indices if i < len(keypoints)]
        return sum(visibilities) / len(visibilities) if visibilities else 0.0

    def analyze(self, keypoints, image_shape):
        if not keypoints:
            self.feedback = "Nenhuma pessoa detectada."
            self.feedback_type = "ERRO_CRITICO"
            return {}

        angles = {}
        visibilities = {}
        for angle_def in self.angle_definitions:
            name = angle_def['name']
            indices = angle_def['indices']
            p1_idx, p2_idx, p3_idx = indices
            angles[name] = calculate_angle_3d(keypoints, p1_idx, p2_idx, p3_idx)
            visibilities[name] = self._get_keypoint_visibility(keypoints, indices)

        # 1. Determina o ângulo principal baseado no lado mais visível
        main_angle_value, active_angle_name = self._get_active_main_angle(angles, visibilities)

        # 2. Atualiza o contador de repetições (lógica agora é independente)
        self._update_rep_counter(main_angle_value)
        
        # 3. Atualiza o feedback de postura em tempo real
        posture_feedback, posture_type = self._get_posture_feedback(angles, visibilities, active_angle_name)

        # 4. Decide qual feedback mostrar na tela
        if time.time() < self.rep_complete_feedback_end_time:
            self.feedback = f"Repeticao {self.counter}!"
            self.feedback_type = "CORRETO"
        else:
            self.feedback = posture_feedback
            self.feedback_type = posture_type
            
        return angles

    def _get_active_main_angle(self, angles, visibilities):
        """Identifica o ângulo principal (ex: cotovelo) do lado mais visível para a câmera."""
        main_angle_base_name = self.config['main_angle']
        active_angle_name = main_angle_base_name
        
        opposite_angle_name = None
        if 'right_' in main_angle_base_name:
            opposite_angle_name = main_angle_base_name.replace('right_', 'left_')
        elif 'left_' in main_angle_base_name:
            opposite_angle_name = main_angle_base_name.replace('left_', 'right_')
        
        if opposite_angle_name:
            vis_main = visibilities.get(main_angle_base_name, 0)
            vis_opposite = visibilities.get(opposite_angle_name, 0)
            if vis_opposite > vis_main:
                active_angle_name = opposite_angle_name
        
        return angles.get(active_angle_name), active_angle_name

    def _update_rep_counter(self, main_angle_value):
        """Máquina de estados simples e robusta que APENAS conta o movimento mecânico."""
        if main_angle_value is None:
            return

        up_threshold = self.rules['state_change']['up_angle']
        down_threshold = self.rules['state_change']['down_angle']

        # Transição: UP -> DOWN
        if self.rep_state == 'up' and main_angle_value < down_threshold:
            self.rep_state = 'down'
        
        # Transição: DOWN -> UP (Conta a repetição)
        elif self.rep_state == 'down' and main_angle_value > up_threshold:
            self.counter += 1
            self.rep_state = 'up'
            self.rep_complete_feedback_end_time = time.time() + 2  # Mostra msg por 2 seg

    def _get_posture_feedback(self, angles, visibilities, active_angle_name):
        """Verifica todas as regras de postura e retorna o feedback apropriado."""
        active_side_prefix = "right_" if "right_" in active_angle_name else "left_" if "left_" in active_angle_name else ""

        for rule in self.rules['feedback']:
            angle_to_check_name = rule['angle']
            if active_side_prefix and ('right_' in angle_to_check_name or 'left_' in angle_to_check_name):
                inactive_prefix = "left_" if active_side_prefix == "right_" else "right_"
                angle_to_check_name = rule['angle'].replace(inactive_prefix, active_side_prefix)

            angle_value = angles.get(angle_to_check_name)
            angle_vis = visibilities.get(angle_to_check_name, 0)

            if angle_value is not None and angle_vis > 0.65:
                verde = rule['zones']['verde']
                amarela = rule['zones']['amarela']
                
                if not (verde['min'] <= angle_value <= verde['max']):
                    if amarela['min'] <= angle_value <= amarela['max']:
                        return rule['message'], "ATENCAO"
                    else:
                        return rule['message'], "ERRO_CRITICO"
        
        return "Postura Correta!", "CORRETO"