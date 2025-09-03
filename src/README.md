# Implementação

Essa pasta contém todos os arquivos necessários para a lógica de implementação do algoritmo, são arquivos que executam a lógica de detecção de pontos-chave, filtro de suavização e relatório de análise de postura.

## Arquivos fonte

- ***angle_utils.py***

    **Função:** Utilitário Matemático. 
    
    - Um módulo simples que contém a função calculate_angle_3d.

    - Calcula o ângulo em graus entre três pontos 3D no espaço.

    - Vantagem: Isola a matemática vetorial do resto da lógica de análise, mantendo o código mais limpo e organizado.

- ***kalman_smoother.py***

    **Função:** Filtro Avançado de Pontos-Chave.
    
    - Este é um dos componentes mais importantes para a qualidade da detecção. Ele recebe os pontos-chave brutos do PoseDetector e os aprimora.

    - Suaviza o tremor ("jitter") natural das detecções.

    - Estima a posição de pontos-chave que estão obstruídos (invisíveis para a câmera).

    - Implementa uma heurística de simetria para que membros obstruídos se movam de forma realista junto com seus pares visíveis.

    - Aplica amortecimento de velocidade para evitar que pontos obstruídos se "percam" e derivem pela tela.

- ***pose_detector.py***

    **Função:** Encapsulamento do MediaPipe Pose.
    Esta classe funciona como um "wrapper" para a biblioteca MediaPipe Pose. Sua função é isolar toda a lógica de detecção de pose em um único lugar.

    - Recebe uma imagem e retorna a lista de pontos-chave (landmarks) 3D detectados.

    - Vantagem: Se no futuro quisermos trocar o MediaPipe por outro modelo de estimação de pose, apenas este arquivo precisará ser modificado, mantendo o resto do projeto intacto.

- ***posture_analysis.py***

    **Função:** Esta é a classe que contém a lógica de negócio principal do projeto.

    - Carrega e interpreta as regras do exercício a partir de um arquivo .json.

    - Implementa a máquina de estados (up/down) para contar as repetições, focando apenas no lado do corpo mais visível.

    - Analisa os ângulos corporais em tempo real e compará-los com as regras para gerar feedback de postura (ex: "Mantenha o corpo reto!").

    - Detecta a orientação geral do corpo (horizontal/flexão vs. vertical/em pé).

    - Coleta os erros de uma repetição e comunicá-los ao Relatorio ao final de cada ciclo.

- ***report.py***

    **Função:** Gerador de Resumo da Sessão
    
    - Esta classe é responsável por criar o relatório final legível para o usuário.

    - Recebe dados consolidados de cada repetição (se foi correta, quais erros ocorreram) do PostureAnalyzer.

    - Ao final da sessão, ele agrega todas essas informações para gerar um arquivo .txt com:

    - Estatísticas gerais (total de reps, % de acerto).

    - Uma lista dos erros de postura mais comuns.

    - Dicas sobre quais partes do corpo focar para corrigir esses erros.

