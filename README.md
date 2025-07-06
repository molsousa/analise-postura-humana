# Analise de Postura Humana em Exercícios de Calistenia

Este repositório contém um projeto de análise de pose humana em exercícios de calistenia usando a biblioteca Mediapipe Pose. O objetivo desse projeto é informar ao usuário se o mesmo está fazendo o exercício corretamente a fim de evitar lesões. Inicialmente o algoritmo detecta apenas flexão de braço e agachamento.

## Implementação

O algoritmo foi todo implementado em Python, a biblioteca utilizada foi o Mediapipe Pose, foi utilizado a biblioteca OneEuroFilter para auxiliar na detecção de pontos e suavizar o desempenho geral do algoritmo.

O arquivo *posture_analysis* faz a análise geral dos exercícios, toda a orientação dada ao usuário é centralizada nesse arquivo, para as limiares do exercícios, foram criados templates na pasta "*exercise_templates*", onde tem detalhadamente os ângulos a serem seguidos pelo usuário.

Os demais arquivos são auxiliares ao principal (*posture_analysis*).

## Como utilizar

É necessário instalar o Python na sua versão 3.11.

Também é necessário instalar as bibliotecas openCV, mediapipe e OneEuroFilter.

É recomendável guardar os vídeos na pasta "**videos/**" a fim de evitar colocar um caminho mais extenso na execução.

Para a utilização do algoritmo, segue abaixo o comando que deve ser feito no terminal:

    python main.py --exercise exercise_templates/<exercício_desejado> --video videos/<video_desejado>
 