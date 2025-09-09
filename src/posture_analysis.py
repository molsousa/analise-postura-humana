import json
import time
import numpy as np
from src.angle_utils import calculate_angle_3d, calculate_segment_angle_horizontal

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

        self.rep_state = "up"
        self.counter = 0
        self.qualidade_da_rep_atual = True
        self.erros_na_rep_atual = set()

        self.feedback = "Inicie o exercicio."
        self.feedback_type = "INFO"
        self.rep_complete_feedback_end_time = 0
        self.movement_phase = "INICIANDO"

    def _get_keypoint_visibility(self, keypoints, indices):
        if not keypoints: return 0.0
        visibilities = [keypoints[i][3] for i in indices if i < len(keypoints)]
        return sum(visibilities) / len(visibilities) if visibilities else 0.0

    def _analyze_squat_phase(self, angles, visibilities):
        """
        Analisa e retorna a fase atual do movimento de agachamento com regras refinadas.
        """
        STAND_THRESHOLD = 160 # Ângulo do joelho para ser considerado em pé

        # Intervalos de ângulo para a fase "AGACHADO"
        SQUATTED_KNEE_MIN, SQUATTED_KNEE_MAX = 40, 90 # Aumentei um pouco o max para dar mais flexibilidade
        SQUATTED_HIP_MIN, SQUATTED_HIP_MAX = 20, 70   # Mesmo motivo acima

        # Determina qual lado do corpo está mais visível para usar como referência
        vis_joelho_dir = visibilities.get('right_knee_flexion', 0)
        vis_joelho_esq = visibilities.get('left_knee_flexion', 0)
        
        if vis_joelho_dir > vis_joelho_esq:
            knee_angle = angles.get('right_knee_flexion')
            hip_angle = angles.get('right_hip_flexion')
        else:
            knee_angle = angles.get('left_knee_flexion')
            hip_angle = angles.get('left_hip_flexion')

        if knee_angle is None or hip_angle is None:
            return "INDETERMINADO"

        # 1. Checa se está na posição "EM PE"
        if knee_angle > STAND_THRESHOLD:
            return "EM PE"
        
        # 2. Checa se está na posição "AGACHADO" com as novas regras precisas
        is_knee_in_range = SQUATTED_KNEE_MIN <= knee_angle <= SQUATTED_KNEE_MAX
        is_hip_in_range = SQUATTED_HIP_MIN <= hip_angle <= SQUATTED_HIP_MAX
        is_hip_deeper_than_knee = hip_angle < knee_angle

        if is_knee_in_range and is_hip_in_range and is_hip_deeper_than_knee:
            return "AGACHADO"
        
        # 3. Se não for nenhum dos anteriores, está em transição
        return "TRANSICAO"


    def analyze(self, keypoints, image_shape, reporter):
        if not keypoints:
            self.feedback = "Nenhuma pessoa detectada."
            self.feedback_type = "ERRO_CRITICO"
            self.movement_phase = "INDETERMINADO"
            return {}

        angles = {}
        visibilities = {}
        for angle_def in self.angle_definitions:
            name = angle_def['name']
            indices = angle_def['indices']
            p1_idx, p2_idx, p3_idx = indices
            angles[name] = calculate_angle_3d(keypoints, p1_idx, p2_idx, p3_idx)
            visibilities[name] = self._get_keypoint_visibility(keypoints, indices)

        if self.exercise_name == "Agachamento":
            self.movement_phase = self._analyze_squat_phase(angles, visibilities)
        else:
            self.movement_phase = self.detect_body_orientation(keypoints, image_shape)

        main_angle_value, active_angle_name = self._get_active_main_angle(angles, visibilities)
        posture_feedback, posture_type = self._get_posture_feedback(keypoints, angles, visibilities, active_angle_name)
        
        current_phase = self.movement_phase
        if current_phase == 'AGACHADO' and posture_type in ['ATENCAO', 'ERRO_CRITICO']:
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
    
    def detect_body_orientation(self, keypoints, image_shape, vert_threshold=0.6):
        if not keypoints or image_shape is None:
            return "INDETERMINADO"
        h, w = image_shape[:2]
        idx_ombro_esq = self.detector.get_landmark_index('LEFT_SHOULDER')
        idx_ombro_dir = self.detector.get_landmark_index('RIGHT_SHOULDER')
        idx_quadril_esq = self.detector.get_landmark_index('LEFT_HIP')
        idx_quadril_dir = self.detector.get_landmark_index('RIGHT_HIP')
        max_idx = max(idx_ombro_esq, idx_ombro_dir, idx_quadril_esq, idx_quadril_dir)
        if max_idx >= len(keypoints):
             return "INDETERMINADO"
        pontos = {'ombro_esq': keypoints[idx_ombro_esq] if keypoints[idx_ombro_esq][3] > 0.5 else None,
                  'ombro_dir': keypoints[idx_ombro_dir] if keypoints[idx_ombro_dir][3] > 0.5 else None,
                  'quadril_esq': keypoints[idx_quadril_esq] if keypoints[idx_quadril_esq][3] > 0.5 else None,
                  'quadril_dir': keypoints[idx_quadril_dir] if keypoints[idx_quadril_dir][3] > 0.5 else None}
        if pontos['ombro_esq'] and pontos['ombro_dir']:
            ponto_superior = (np.array(pontos['ombro_esq'][:2]) + np.array(pontos['ombro_dir'][:2])) / 2
        elif pontos['ombro_esq']:
            ponto_superior = np.array(pontos['ombro_esq'][:2])
        elif pontos['ombro_dir']:
            ponto_superior = np.array(pontos['ombro_dir'][:2])
        else:
            return "INDETERMINADO"
        if pontos['quadril_esq'] and pontos['quadril_dir']:
            ponto_inferior = (np.array(pontos['quadril_esq'][:2]) + np.array(pontos['quadril_dir'][:2])) / 2
        elif pontos['quadril_esq']:
            ponto_inferior = np.array(pontos['quadril_esq'][:2])
        elif pontos['quadril_dir']:
            ponto_inferior = np.array(pontos['quadril_dir'][:2])
        else:
            return "INDETERMINADO"
        delta_x = abs(ponto_superior[0] - ponto_inferior[0]) * w
        delta_y = abs(ponto_superior[1] - ponto_inferior[1]) * h
        if delta_x + delta_y == 0:
            return "INDETERMINADO"
        verticality_ratio = delta_y / (delta_x + delta_y)
        if verticality_ratio > vert_threshold:
            return "EM PE (Orientacao)"
        else:
            return "HORIZONTAL (FLEXAO)"

    def _get_active_main_angle(self, angles, visibilities):
        main_angle_base_name = self.config['main_angle']
        active_angle_name = main_angle_base_name
        opposite_angle_name = None
        if 'right_' in main_angle_base_name: opposite_angle_name = main_angle_base_name.replace('right_', 'left_')
        elif 'left_' in main_angle_base_name: opposite_angle_name = main_angle_base_name.replace('left_', 'right_')
        if opposite_angle_name and opposite_angle_name in visibilities:
            vis_main = visibilities.get(main_angle_base_name, 0)
            vis_opposite = visibilities.get(opposite_angle_name, 0)
            if vis_opposite > vis_main: active_angle_name = opposite_angle_name
        return angles.get(active_angle_name), active_angle_name

    def _update_rep_counter(self, main_angle_value, reporter):
        if main_angle_value is None: return
        up_threshold = self.rules['state_change']['up_angle']
        down_threshold = self.rules['state_change']['down_angle']
        if self.rep_state == 'up' and main_angle_value < down_threshold:
            self.rep_state = 'down'
            self.qualidade_da_rep_atual = True
            self.erros_na_rep_atual.clear()
        elif self.rep_state == 'down' and main_angle_value > up_threshold:
            self.counter += 1
            reporter.save_rep(self.counter, self.qualidade_da_rep_atual, self.erros_na_rep_atual)
            self.rep_state = 'up'
            self.rep_complete_feedback_end_time = time.time() + 2
    
    def _get_posture_feedback(self, keypoints, angles, visibilities, active_angle_name):
        active_side_prefix = "right_" if "right_" in active_angle_name else "left_" if "left_" in active_angle_name else ""
        
        current_phase = self.movement_phase

        for rule in self.rules['feedback']:
            rule_type = rule.get('type', 'zone')

            apply_when = rule.get('apply_when')
            if apply_when and current_phase != apply_when and apply_when != "both":
                continue
            
            if rule_type == 'zone':
                angle_to_check_name = rule['angle']
                if active_side_prefix and ('right_' in angle_to_check_name or 'left_' in angle_to_check_name):
                    inactive_prefix = "left_" if active_side_prefix == "right_" else "right_"
                    angle_to_check_name = rule['angle'].replace(inactive_prefix, active_side_prefix)
                angle_value = angles.get(angle_to_check_name)
                angle_vis = visibilities.get(angle_to_check_name, 0)
                if angle_value is not None and angle_vis > 0.65:
                    verde = rule['zones']['verde']
                    if not (verde['min'] <= angle_value <= verde['max']):
                        if 'amarela' in rule['zones']:
                            amarela = rule['zones']['amarela']
                            if amarela['min'] <= angle_value <= amarela['max']: return rule['message'], "ATENCAO"
                        return rule['message'], "ERRO_CRITICO"
            elif rule_type == 'segment_parallelism':
                s1_p1_idx = self.detector.get_landmark_index(rule['segment1'][0])
                s1_p2_idx = self.detector.get_landmark_index(rule['segment1'][1])
                s2_p1_idx = self.detector.get_landmark_index(rule['segment2'][0])
                s2_p2_idx = self.detector.get_landmark_index(rule['segment2'][1])
                angle1 = calculate_segment_angle_horizontal(keypoints, s1_p1_idx, s1_p2_idx)
                angle2 = calculate_segment_angle_horizontal(keypoints, s2_p1_idx, s2_p2_idx)
                if angle1 is not None and angle2 is not None:
                    difference = abs(angle1 - angle2)
                    if difference > 180: difference = 360 - difference
                    if abs(difference - 180) < difference: difference = abs(difference-180)
                    if difference > rule['max_difference']: return rule['message'], "ATENCAO"
            elif rule_type == 'vertical_comparison':
                lm1_name, lm2_name = rule['landmark1'], rule['landmark2']
                if active_side_prefix:
                    lm1_name = lm1_name.replace('right_', active_side_prefix)
                    lm2_name = lm2_name.replace('right_', active_side_prefix)
                lm1_idx = self.detector.get_landmark_index(lm1_name)
                lm2_idx = self.detector.get_landmark_index(lm2_name)
                vis1 = keypoints[lm1_idx][3]
                vis2 = keypoints[lm2_idx][3]
                if vis1 > 0.65 and vis2 > 0.65:
                    y1 = keypoints[lm1_idx][1]
                    y2 = keypoints[lm2_idx][1]
                    if rule['condition'] == 'is_below_or_level':
                        if y1 < y2:
                            return rule['message'], "ATENCAO"
            elif rule_type == 'angle_offset':
                base_angle_name = rule['base_angle']
                offset_angle_name = rule['offset_angle']
                if active_side_prefix:
                    base_angle_name = base_angle_name.replace('right_', active_side_prefix)
                    offset_angle_name = offset_angle_name.replace('right_', active_side_prefix)
                base_angle_val = angles.get(base_angle_name)
                offset_angle_val = angles.get(offset_angle_name)
                vis1 = visibilities.get(base_angle_name, 0)
                vis2 = visibilities.get(offset_angle_name, 0)
                if base_angle_val is not None and offset_angle_val is not None and vis1 > 0.65 and vis2 > 0.65:
                    offset = base_angle_val - offset_angle_val
                    expected = rule['expected_offset_range']
                    if not (expected['min'] <= offset <= expected['max']):
                        return rule['message'], "ATENCAO"

        return "Postura Correta!", "CORRETO"