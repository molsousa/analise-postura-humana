# Analise de Postura Humana em Exercícios de Calistenia

Este repositório contém um projeto de análise de pose humana em exercícios de calistenia usando a biblioteca Mediapipe Pose. O objetivo desse projeto é informar ao usuário se o mesmo está fazendo o exercício corretamente a fim de evitar lesões. Inicialmente o algoritmo detecta apenas flexão de braço e agachamento.

A implementação do projeto faz parte de uma pesquisa científica desenvolvida no Laboratório de Computação Gráfica da Universidade do Oeste do Paraná (UNIOESTE). Antes da implementação fora publicado um artigo relacionado no Congresso Latino-Americano de Software Livre e Tecnologia Aberta (LATINOWARE), sendo possível acessar por esse link: [Análise e Orientação de Postura nos Exercícios de Calistenia usando Estimativa de Pose Humana](https://doi.org/10.5753/latinoware.2024.245728).

## Implementação

* O algoritmo foi todo implementado em Python, a biblioteca utilizada foi o Mediapipe Pose, foi utilizado a biblioteca Kalman Filter para auxiliar na detecção de pontos e suavizar o desempenho geral do algoritmo. Para acessar a implementação do filtro Kalman, acesse o link: [Filterpy](https://github.com/rlabbe/filterpy)

* O arquivo [*posture_analysis*](https://github.com/molsousa/analise-postura-humana/blob/main/src/posture_analysis.py) faz a análise geral dos exercícios, toda a orientação dada ao usuário é centralizada nesse arquivo, para as limiares do exercícios, foram criados templates na pasta "[*exercise_templates*](https://github.com/molsousa/analise-postura-humana/tree/main/exercise_templates)", onde tem detalhadamente os ângulos a serem seguidos pelo usuário.

* Os demais arquivos são auxiliares ao principal ([*posture_analysis*](https://github.com/molsousa/analise-postura-humana/blob/main/src/posture_analysis.py)). É possível entender a função principal de cada arquivo acessando o README de cada pasta.

* O algoritmo auxilia o usuário informando se sua posição está ou não correta. Contabiliza as repetições, e ao final, gera um relatório passando as flexões corretas, as flexões com postura incorreta, e a(s) articulação(ões) que decorreu(am) na postura incorreta.

## Arquivos fonte na pasta raiz

- [***main.py***](https://github.com/molsousa/analise-postura-humana/blob/main/main.py)

    **Função:** Este é o script que você executa para iniciar a aplicação. Suas principais responsabilidades são:

    - Interpretar os argumentos de linha de comando (qual exercício e qual vídeo/câmera usar).

    - Inicializar todos os objetos principais: PoseDetector, PostureAnalyzer, KalmanSmoother e Relatorio.

    - Abrir a fonte de vídeo e executar o loop principal que processa frame a frame.

    - Coordenar o fluxo de dados em cada frame: detectar -> suavizar -> analisar.

    - Gerenciar toda a parte de visualização, desenhando o esqueleto e os textos de feedback na tela usando OpenCV.

    - Chamar o método de salvar o relatório ao final da sessão.

- [***config.py***](https://github.com/molsousa/analise-postura-humana/blob/main/config.py)

    **Função:** Este arquivo centraliza constantes e configurações usadas em diferentes partes do projeto. Ele define:

    - As cores (em BGR) para cada tipo de feedback (CORRETO, ATENCAO, ERRO_CRITICO).

    - O nome do diretório onde os relatórios de sessão são salvos (ex: logs).

    - Isso permite alterar a aparência e o comportamento da aplicação facilmente, sem precisar modificar o código principal.

## Como utilizar

* É necessário instalar o Python na sua versão 3.11 e garantir que está acessível nas variáveis de ambiente. Em caso de dúvida da sua versão de Python, executar:

        python --version

* É necessário instalar as bibliotecas opencv, mediapipe e filterpy executando as linhas de código:

        pip install opencv-python
        pip install mediapipe
        pip install filterpy

* É recomendável guardar os vídeos na pasta "[**videos/**](https://github.com/molsousa/analise-postura-humana/tree/main/videos)" a fim de evitar colocar um caminho mais extenso na execução.

* Para a utilização do algoritmo, segue abaixo o comando que deve ser feito no terminal:

        python main.py --exercise exercise_templates/<exercício_desejado> --video videos/<video_desejado>
 
* Caso for desejável utilizar webcam ao invés de um vídeo já gravado, basta apenas apagar o texto posterior a *--video*, exemplo:

        python main.py --exercise exercise_templates/<exercício_desejado>