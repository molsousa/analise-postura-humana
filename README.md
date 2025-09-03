# Analise de Postura Humana em Exercícios de Calistenia

Este repositório contém um projeto de análise de pose humana em exercícios de calistenia usando a biblioteca Mediapipe Pose. O objetivo desse projeto é informar ao usuário se o mesmo está fazendo o exercício corretamente a fim de evitar lesões. Inicialmente o algoritmo detecta apenas flexão de braço e agachamento.

## Implementação

* O algoritmo foi todo implementado em Python, a biblioteca utilizada foi o Mediapipe Pose, foi utilizado a biblioteca Kalman Filter para auxiliar na detecção de pontos e suavizar o desempenho geral do algoritmo.

* O arquivo *posture_analysis* faz a análise geral dos exercícios, toda a orientação dada ao usuário é centralizada nesse arquivo, para as limiares do exercícios, foram criados templates na pasta "*exercise_templates*", onde tem detalhadamente os ângulos a serem seguidos pelo usuário.

* Os demais arquivos são auxiliares ao principal (*posture_analysis*). É possível entender a função principal de cada arquivo acessando o README de cada pasta.

* O algoritmo auxilia o usuário informando se sua posição está ou não correta. Contabiliza as repetições, e ao final, gera um relatório passando as flexões corretas, as flexões com postura incorreta, e a(s) articulação(ões) que decorreu(am) na postura incorreta.

## Arquivos fonte
- ***main.py***

    **Função:** Este é o script que você executa para iniciar a aplicação. Suas principais responsabilidades são:

    - Interpretar os argumentos de linha de comando (qual exercício e qual vídeo/câmera usar).

    - Inicializar todos os objetos principais: PoseDetector, PostureAnalyzer, KalmanSmoother e Relatorio.

    - Abrir a fonte de vídeo e executar o loop principal que processa frame a frame.

    - Coordenar o fluxo de dados em cada frame: detectar -> suavizar -> analisar.

    - Gerenciar toda a parte de visualização, desenhando o esqueleto e os textos de feedback na tela usando OpenCV.

    - Chamar o método de salvar o relatório ao final da sessão.

- ***report.py***

    **Função:** Este arquivo centraliza constantes e configurações usadas em diferentes partes do projeto. Ele define:

    - As cores (em BGR) para cada tipo de feedback (CORRETO, ATENCAO, ERRO_CRITICO).

    - O nome do diretório onde os relatórios de sessão são salvos (ex: logs).

    - Isso permite alterar a aparência e o comportamento da aplicação facilmente, sem precisar modificar o código principal.

## Como utilizar

* É necessário instalar o Python na sua versão 3.11.

* É necessário instalar as bibliotecas openCV, mediapipe.

* É recomendável guardar os vídeos na pasta "**videos/**" a fim de evitar colocar um caminho mais extenso na execução.

* Para a utilização do algoritmo, segue abaixo o comando que deve ser feito no terminal:

       python main.py --exercise exercise_templates/<exercício_desejado> --video videos/<video_desejado>
 
