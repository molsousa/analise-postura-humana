import json
from src.angle_utils import calculate_angle_3d

class PostureAnalyzer:
    """
    Analisa a postura com base em keypoints 3D e um arquivo de configuração de exercício.

    Esta classe calcula ângulos em tempo real e os compara com as regras definidas
    em um arquivo JSON. As regras são baseadas nos princípios biomecânicos do
    documento de análise, incluindo zonas de atenção e erro.
    """
    def __init__(self, exercise_config_path, pose_detector):
        """
        Inicializa o analisador.

        Args:
            exercise_config_path (str): Caminho para o arquivo de configuração do exercício.
            pose_detector (MediaPipePoseDetector): Instância do detector de pose para mapear nomes de articulações.
        """
        self.detector = pose_detector
        with open(exercise_config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.exercise_name = self.config['name']
        self.rules = self.config['rules']
        
        # Mapeia os nomes das articulações para seus índices correspondentes do MediaPipe
        self.angle_definitions = []
        for angle_name, joints in self.config['angle_definitions'].items():
            indices = [self.detector.get_landmark_index(j) for j in joints]
            if None in indices:
                raise ValueError(f"Nome de articulação inválido para o ângulo '{angle_name}'")
            self.angle_definitions.append({'name': angle_name, 'indices': indices})

        # Estado para contagem de repetições
        self.state = "up"
        self.counter = 0
        
        # Estado para feedback de postura
        self.feedback = "Inicie o exercicio."
        self.feedback_type = "INFO"  # Tipos: INFO, CORRETO, ATENCAO, ERRO_CRITICO
        self.is_correct = True

    def _get_keypoint_visibility(self, keypoints, indices):
        """Calcula a visibilidade média para um conjunto de keypoints."""
        if not keypoints: return 0.0
        visibilities = [keypoints[i][3] for i in indices if i < len(keypoints)]
        return sum(visibilities) / len(visibilities) if visibilities else 0.0

    def analyze(self, keypoints, image_shape):
        """
        Executa a análise de um único frame.

        Args:
            keypoints (list): A lista de keypoints 3D (x, y, z, vis) suavizados.
            image_shape (tuple): A forma da imagem (altura, largura), usada se for necessário.

        Returns:
            dict: Um dicionário com os nomes e valores dos ângulos calculados.
        """
        if not keypoints:
            self.feedback = "Nenhuma pessoa detectada."
            self.feedback_type = "ERRO_CRITICO"
            self.is_correct = False
            return {}

        angles = {}
        visibilities = {}
        # Calcula todos os ângulos definidos na configuração
        for angle_def in self.angle_definitions:
            name = angle_def['name']
            indices = angle_def['indices']
            p1_idx, p2_idx, p3_idx = indices
            
            # Utiliza o cálculo de ângulo 3D
            angles[name] = calculate_angle_3d(keypoints, p1_idx, p2_idx, p3_idx)
            visibilities[name] = self._get_keypoint_visibility(keypoints, indices)

        self._run_analysis_logic(angles, visibilities)
        return angles

    def _run_analysis_logic(self, angles, visibilities):
        """
        Aplica a lógica de regras, contagem de repetições e geração de feedback.
        Esta função implementa a lógica hierárquica de feedback do PDF.
        """
        # --- Lógica de Seleção de Lado (Direito/Esquerdo) ---
        main_angle_base_name = self.config['main_angle']
        active_side_prefix = ""
        
        if 'right_' in main_angle_base_name:
            opposite_angle_name = main_angle_base_name.replace('right_', 'left_')
            vis_main = visibilities.get(main_angle_base_name, 0)
            vis_opposite = visibilities.get(opposite_angle_name, -1)

            if vis_main < 0.6 and vis_opposite < 0.6:
                self.feedback = "Posicao nao clara. Fique de lado para a camera."
                self.feedback_type = "ERRO_CRITICO"
                self.is_correct = False
                return
            
            if vis_main >= vis_opposite:
                active_angle_name = main_angle_base_name
                active_side_prefix = "right_"
            else:
                active_angle_name = opposite_angle_name
                active_side_prefix = "left_"
        else:
            active_angle_name = main_angle_base_name

        # --- Avaliação de Regras e Feedback Hierárquico ---
        detected_errors = []
        for rule in self.rules['feedback']:
            angle_to_check_base = rule['angle']
            
            if active_side_prefix and ('right_' in angle_to_check_base or 'left_' in angle_to_check_base):
                inactive_prefix = "left_" if active_side_prefix == "right_" else "right_"
                angle_to_check_name = angle_to_check_base.replace(inactive_prefix, active_side_prefix)
            else:
                angle_to_check_name = angle_to_check_base

            if angle_to_check_name not in angles:
                angle_to_check_name = angle_to_check_base
            
            angle_value = angles.get(angle_to_check_name)
            angle_vis = visibilities.get(angle_to_check_name, 0)

            if angle_value is not None and angle_vis > 0.65:
                verde = rule['zones']['verde']
                amarela = rule['zones']['amarela']

                # 1. Verifica se o ângulo está na zona verde (ideal). Se estiver, está tudo certo para esta regra.
                if verde['min'] <= angle_value <= verde['max']:
                    continue

                # 2. Se não estiver no verde, verifica se está na zona amarela (atenção).
                elif amarela['min'] <= angle_value <= amarela['max']:
                    detected_errors.append({'message': rule['message'], 'criticity': 1}) 
                
                # 3. Se não estiver nem no verde nem no amarelo, é um erro crítico (vermelho).
                else:
                    detected_errors.append({'message': rule['message'], 'criticity': 2}) 

        # --- Geração do Feedback Final ---
        if detected_errors:
            most_critical_error = sorted(detected_errors, key=lambda x: x['criticity'], reverse=True)[0]
            self.feedback = most_critical_error['message']
            self.is_correct = False
            self.feedback_type = "ERRO_CRITICO" if most_critical_error['criticity'] == 2 else "ATENCAO"
        else:
            self.feedback = "Postura Correta!"
            self.is_correct = True
            self.feedback_type = "CORRETO"
        
        # --- Lógica de Contagem de Repetições ---
        main_angle_value = angles.get(active_angle_name)
        if main_angle_value is None: return

        up_threshold = self.rules['state_change']['up_angle']
        down_threshold = self.rules['state_change']['down_angle']

        if self.state == "down" and main_angle_value > up_threshold:
            if self.is_correct:
                self.counter += 1
                self.feedback = f"Repeticao {self.counter} Concluida!"
            else:
                self.feedback += "\n(Corrija a postura para contar)"
            self.state = "up"
        elif self.state == "up" and main_angle_value < down_threshold:
            self.state = "down"