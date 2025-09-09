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
            index = [self.detector.get_landmark_index(j) for j in joints]

            if None in index:
                raise ValueError(f"Nome de articulação inválido para o ângulo '{angle_name}'")
            
            self.angle_definitions.append({'name': angle_name, 'index': index})

        # --- LÓGICA DE CONTAGEM DE REPETIÇÕES ---
        self.rep_state = "up"
        self.counter = 0
        self.rep_quality = True
        self.actual_rep_errors = set()

        # --- LÓGICA DE FEEDBACK E ESTADO ---
        self.feedback = "Inicie o exercicio."
        self.feedback_type = "INFO"
        self.rep_complete_feedback_end_time = 0
        self.movement_phase = "INICIANDO"

    def _get_keypoint_visibility(self, keypoints, index):
        if not keypoints: return 0.0
        visibilities = [keypoints[i][3] for i in index if i < len(keypoints)]
        return sum(visibilities) / len(visibilities) if visibilities else 0.0

    def _analyze_squat_phase(self, angles, visibilities):
        """
        Analisa e retorna a fase atual do movimento de agachamento com regras refinadas.
        """
        STAND_THRESHOLD = 160 
        SQUATTED_KNEE_MIN, SQUATTED_KNEE_MAX = 40, 90
        SQUATTED_HIP_MIN, SQUATTED_HIP_MAX = 20, 70

        right_knee_vis = visibilities.get('right_knee_flexion', 0)
        left_knee_vis = visibilities.get('left_knee_flexion', 0)
        
        if right_knee_vis > left_knee_vis:
            knee_angle = angles.get('right_knee_flexion')
            hip_angle = angles.get('right_hip_flexion')

        else:
            knee_angle = angles.get('left_knee_flexion')
            hip_angle = angles.get('left_hip_flexion')

        if knee_angle is None or hip_angle is None:
            return "INDETERMINADO"

        if knee_angle > STAND_THRESHOLD:
            return "EM PE"
        
        is_knee_in_range = SQUATTED_KNEE_MIN <= knee_angle <= SQUATTED_KNEE_MAX
        is_hip_in_range = SQUATTED_HIP_MIN <= hip_angle <= SQUATTED_HIP_MAX
        is_hip_deeper_than_knee = hip_angle < knee_angle

        if is_knee_in_range and is_hip_in_range and is_hip_deeper_than_knee:
            return "AGACHADO"
        
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
            index = angle_def['index']
            p1_idx, p2_idx, p3_idx = index
            angles[name] = calculate_angle_3d(keypoints, p1_idx, p2_idx, p3_idx)
            visibilities[name] = self._get_keypoint_visibility(keypoints, index)

        if self.exercise_name == "Agachamento":
            self.movement_phase = self._analyze_squat_phase(angles, visibilities)

        else:
            self.movement_phase = self.detect_body_orientation(keypoints, image_shape)

        main_angle_value, active_angle_name = self._get_active_main_angle(angles, visibilities)
        posture_feedback, posture_type = self._get_posture_feedback(keypoints, angles, visibilities, active_angle_name)
        
        # Verificação de erro funciona para qualquer exercício na fase de descida.
        if self.rep_state == 'down' and posture_type in ['ATENCAO', 'ERRO_CRITICO']:
            self.rep_quality = False
            self.actual_rep_errors.add(posture_feedback)

        self._update_rep_counter(main_angle_value, reporter)
        
        if time.time() < self.rep_complete_feedback_end_time:
            self.feedback = f"Repeticao {self.counter}!"
            self.feedback_type = "CORRETO"

        else:
            self.feedback = posture_feedback
            self.feedback_type = posture_type
            
        return angles
    
    def detect_body_orientation(self, keypoints, image_shape, vert_threshold=0.6):
        """
        Determina se o corpo está em uma posição vertical (em pé) ou horizontal (flexão).
        Retorna "EM_PE", "HORIZONTAL (FLEXAO)" ou "INDETERMINADO".
        """
        if not keypoints or image_shape is None:
            return "INDETERMINADO"
        
        h, w = image_shape[:2]
        left_shoulder_idx = self.detector.get_landmark_index('LEFT_SHOULDER')
        right_shoulder_idx = self.detector.get_landmark_index('RIGHT_SHOULDER')
        left_hip_idx = self.detector.get_landmark_index('LEFT_HIP')
        right_hip_idx = self.detector.get_landmark_index('RIGHT_HIP')
        max_idx = max(left_shoulder_idx, right_shoulder_idx, left_hip_idx, right_hip_idx)

        if max_idx >= len(keypoints):
             return "INDETERMINADO"
        
        joint_points = {'left_shoulder': keypoints[left_shoulder_idx] if keypoints[left_shoulder_idx][3] > 0.5 else None,
                  'right_shoulder': keypoints[right_shoulder_idx] if keypoints[right_shoulder_idx][3] > 0.5 else None,
                  'left_hip': keypoints[left_hip_idx] if keypoints[left_hip_idx][3] > 0.5 else None,
                  'right_hip': keypoints[right_hip_idx] if keypoints[right_hip_idx][3] > 0.5 else None}
        
        if joint_points['left_shoulder'] and joint_points['right_shoulder']:
            superior_point = (np.array(joint_points['left_shoulder'][:2]) + np.array(joint_points['right_shoulder'][:2])) / 2

        elif joint_points['left_shoulder']:
            superior_point = np.array(joint_points['left_shoulder'][:2])

        elif joint_points['right_shoulder']:
            superior_point = np.array(joint_points['right_shoulder'][:2])

        else:
            return "INDETERMINADO"
        
        if joint_points['left_hip'] and joint_points['right_hip']:
            inferior_point = (np.array(joint_points['left_hip'][:2]) + np.array(joint_points['right_hip'][:2])) / 2

        elif joint_points['left_hip']:
            inferior_point = np.array(joint_points['left_hip'][:2])

        elif joint_points['right_hip']:
            inferior_point = np.array(joint_points['right_hip'][:2])

        else:
            return "INDETERMINADO"
        
        delta_x = abs(superior_point[0] - inferior_point[0]) * w
        delta_y = abs(superior_point[1] - inferior_point[1]) * h
        
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
            self.rep_quality = True
            self.actual_rep_errors.clear()
            
        elif self.rep_state == 'down' and main_angle_value > up_threshold:
            self.counter += 1
            reporter.save_rep(self.counter, self.rep_quality, self.actual_rep_errors)
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
                    green = rule['zones']['green']
                    if not (green['min'] <= angle_value <= green['max']):
                        if 'yellow' in rule['zones']:
                            yellow = rule['zones']['yellow']
                            if yellow['min'] <= angle_value <= yellow['max']: return rule['message'], "ATENCAO"
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