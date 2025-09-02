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

        # --- LÓGICA DE CONTAGEM DE REPETIÇÕES ---
        self.rep_state = "up"
        self.counter = 0
        self.qualidade_da_rep_atual = True
        self.erros_na_rep_atual = set() # Armazena os erros da rep atual

        # --- LÓGICA DE FEEDBACK ---
        self.feedback = "Inicie o exercicio."
        self.feedback_type = "INFO"
        self.rep_complete_feedback_end_time = 0

    def _get_keypoint_visibility(self, keypoints, indices):
        if not keypoints: return 0.0
        visibilities = [keypoints[i][3] for i in indices if i < len(keypoints)]
        return sum(visibilities) / len(visibilities) if visibilities else 0.0

    def analyze(self, keypoints, image_shape, reporter):
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

        main_angle_value, active_angle_name = self._get_active_main_angle(angles, visibilities)
        posture_feedback, posture_type = self._get_posture_feedback(angles, visibilities, active_angle_name)
        
        if self.rep_state == 'down' and posture_type in ['ATENCAO', 'ERRO_CRITICO']:
            self.qualidade_da_rep_atual = False
            self.erros_na_rep_atual.add(posture_feedback)

        self._update_rep_counter(main_angle_value, reporter)
        
        if time.time() < self.rep_complete_feedback_end_time:
            self.feedback = f"Repeticao {self.counter}!"
            self.feedback_type = "CORRETO"
        else:
            self.feedback = posture_feedback
            self.feedback_type = posture_type
            
        return angles

    def _get_active_main_angle(self, angles, visibilities):
        """Identifica o ângulo principal do lado mais visível para a câmera."""
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

    def _update_rep_counter(self, main_angle_value, reporter):
        """Máquina de estados que conta o movimento e chama o relatório ao final."""
        if main_angle_value is None:
            return

        up_threshold = self.rules['state_change']['up_angle']
        down_threshold = self.rules['state_change']['down_angle']

        if self.rep_state == 'up' and main_angle_value < down_threshold:
            self.rep_state = 'down'
            self.qualidade_da_rep_atual = True
            self.erros_na_rep_atual.clear()

        elif self.rep_state == 'down' and main_angle_value > up_threshold:
            reporter.registrar_repeticao(self.qualidade_da_rep_atual, self.erros_na_rep_atual)
            
            self.counter += 1
            self.rep_state = 'up'
            self.rep_complete_feedback_end_time = time.time() + 2

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