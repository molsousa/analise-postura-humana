import csv
import os
from datetime import datetime
from config import CONFIG_RELATORIO

class Relatorio:
    """
    Gera um relatório em formato CSV com os dados da análise de postura.

    Esta classe coleta dados de cada frame processado (timestamp, exercício,
    ângulos e feedback) e os salva em um arquivo CSV ao final da execução.
    """
    def __init__(self):
        """Inicializa a lista de dados e o caminho do arquivo de relatório."""
        self.dados = []
        self.diretorio_logs = CONFIG_RELATORIO['diretorio_logs']
        self.arquivo_relatorio = CONFIG_RELATORIO['arquivo_dados']
        self._criar_diretorio_log()
    
    def _criar_diretorio_log(self):
        """Cria o diretório para salvar o relatório, se ele não existir."""
        os.makedirs(self.diretorio_logs, exist_ok=True)
    
    def adicionar_dados(self, exercicio, angulos, feedback):
        """
        Adiciona uma nova linha de dados (de um frame) para ser salva no relatório.

        Args:
            exercicio (str): Nome do exercício sendo analisado.
            angulos (dict): Dicionário de ângulos calculados para o frame.
            feedback (str): O texto de feedback gerado para o frame.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        linha = {
            'timestamp': timestamp,
            'exercicio': exercicio,
            'feedback': feedback
        }
        # Adiciona cada ângulo como uma coluna separada para facilitar a análise
        for nome_angulo, valor_angulo in angulos.items():
            linha[nome_angulo] = f"{valor_angulo:.2f}"
            
        self.dados.append(linha)
    
    def salvar(self):
        """
        Salva todos os dados coletados em um arquivo CSV.

        Se nenhum dado foi coletado, a função não faz nada. O cabeçalho do CSV
        é gerado dinamicamente a partir de todas as chaves presentes nos dados,
        garantindo que todas as colunas sejam incluídas.
        """
        if not self.dados:
            print("Nenhum dado foi coletado para gerar o relatório.")
            return
            
        # Pega todas as chaves (colunas) possíveis de todos os registros
        fieldnames = sorted(list(set(key for row in self.dados for key in row.keys())))
            
        with open(self.arquivo_relatorio, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.dados)