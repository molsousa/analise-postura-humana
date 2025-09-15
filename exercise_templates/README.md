# Implementação

Está pasta contém os arquivos .json que define como cada exercício irá funcionar durante a detecção. Com isso, não é necessário alterar o códigos dos demais arquivos Python quando se trata do ângulo correto dos exercícios e feedback personalizado ao usuário.

## Arquivos

### [***pushup.json***](https://github.com/molsousa/analise-postura-humana/blob/main/exercise_templates/pushup.json): 

Este arquivo define as regras para o exercício Flexão de Braço. Ele instrui o PostureAnalyzer - classe contida em [*pose_detector.py*](https://github.com/molsousa/analise-postura-humana/blob/main/src/pose_detector.py) - sobre o que medir e como julgar a performance.

**Detalhamento das Seções:**

- "*name*"

    Função: Simplesmente o nome do exercício que será exibido na tela e nos relatórios.

- "*main_angle*"

    Função: Define qual ângulo é o principal para contar as repetições. No caso da flexão, o movimento de dobrar e esticar o cotovelo é o que define uma repetição. O código é inteligente o suficiente para usar o "left_elbow_angle" se o lado esquerdo estiver mais visível para a câmera.

- "*angle_definitions*"

    Função: Um dicionário que define todos os ângulos que queremos monitorar durante este exercício. Cada chave é um nome para o ângulo, e o valor é uma lista de três pontos-chave (landmarks) do MediaPipe. O ponto do meio é sempre o vértice do ângulo.

- "*right_elbow_angle*" e "left_elbow_angle": Medem a flexão dos cotovelos.

- "*body_line_angle*": Mede o alinhamento do corpo, verificando se o ombro, quadril e tornozelo formam uma linha reta. É crucial para a postura correta.

- "*rules*"

    Função: Contém a lógica principal de como o exercício é avaliado.

- "*state_change*": Define os limiares (thresholds) para a máquina de estados que conta as repetições.

- "*down_angle*": Para o sistema considerar que você iniciou a descida (state = 'down'), o ângulo do cotovelo precisa ser menor que o valor em graus apontado.

- "*up_angle*": Para o sistema contar a repetição e considerar que você voltou à posição inicial (state = 'up'), o ângulo do cotovelo precisa ser maior que o valor em graus apontado.

- "*feedback*": Uma lista de regras para o feedback de postura em tempo real.

    A única regra aqui verifica o "*body_line_angle*".

- "*message*": "Mantenha o corpo reto!": A mensagem que será exibida se a postura estiver incorreta.

- "*zones*": Define o que é uma postura correta. Se o ângulo sair da "zona verde" ("min", "max"), o feedback de erro é acionado. Um ângulo de 180 graus pode representar um corpo perfeitamente reto.

### [***squat.json***](https://github.com/molsousa/analise-postura-humana/blob/main/exercise_templates/squat.json):

Este arquivo define as regras para o exercício Agachamento.

**Detalhamento das Seções:**

- "*name*"

    Função: O nome do exercício a ser exibido.

- "*main_angle*"

    Função: Para o agachamento, o ângulo principal que define a repetição é o da flexão do joelho.

- "*angle_definitions*"

    Função: Define os ângulos a serem monitorados.

- "*right_knee_flexion*" e "*left_knee_flexion*": Medem a profundidade do agachamento pela flexão dos joelhos.

- "*right_ankle_dorsiflexion*" e "*left_ankle_dorsiflexion*": Medem a flexão do tornozelo. Um ângulo correto aqui geralmente indica que o usuário está mantendo os calcanhares no chão e tem boa mobilidade.

- "*rules*"

    Função: Contém as regras de avaliação.

- "*state_change*": Define os limiares para a contagem.

- "*down_angle*": O ângulo do joelho precisa ser menor que o valor em graus apontado graus (down_angle deve ser menor que up_angle) para iniciar a fase de descida.

- "*up_angle*": O ângulo do joelho precisa ser maior que o valor em graus apontado (quase em pé) para finalizar a repetição.

- "*feedback*": Lista de regras de postura.

    Primeira Regra (Profundidade):

    Verifica o ângulo do joelho ("right_knee_flexion").

- "*message*": "Profundidade insuficiente. Agache mais.": É exibida se o ângulo não estiver na zona correta.

- "*zones*": A "zona verde" ("min", "max") define um agachamento de boa profundidade. Se, durante a descida, o ângulo do joelho do usuário permanecer acima de 120 graus, o erro será acionado.