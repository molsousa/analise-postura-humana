import csv
import os
from datetime import datetime
from config import CONFIG_RELATORIO

class Relatorio:
    """
    Gera um relatório em formato CSV com os dados da análise de postura.

    Coleta dados de cada frame processado e os salva em um arquivo CSV 
    ao final da sessão, incluindo o tipo de feedback para análise de severidade.
    """
    def __init__(self):
        """Inicializa a lista de dados e o caminho do arquivo de relatório."""
        self.dados = []
        self.diretorio_logs = CONFIG_RELATORIO['diretorio_logs']
        
        # Gera um nome de arquivo único com data e hora
        timestamp_arquivo = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.arquivo_relatorio = os.path.join(self.diretorio_logs, f"sessao_{timestamp_arquivo}.csv")
        
        self._criar_diretorio_log()
    
    def _criar_diretorio_log(self):
        """Cria o diretório para salvar o relatório, se ele não existir."""
        os.makedirs(self.diretorio_logs, exist_ok=True)
    
    def adicionar_dados(self, exercicio, angulos, feedback_text, feedback_type):
        """
        Adiciona uma nova linha de dados para ser salva no relatório.

        Args:
            exercicio (str): Nome do exercício analisado.
            angulos (dict): Dicionário de ângulos calculados.
            feedback_text (str): O texto de feedback gerado.
            feedback_type (str): O tipo de feedback ('CORRETO', 'ATENCAO', 'ERRO_CRITICO').
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        linha = {
            'timestamp': timestamp,
            'exercicio': exercicio,
            'feedback_tipo': feedback_type,
            'feedback_texto': feedback_text
        }
        # Adiciona cada ângulo como uma coluna separada
        for nome_angulo, valor_angulo in angulos.items():
            linha[nome_angulo] = f"{valor_angulo:.2f}"
            
        self.dados.append(linha)
    
    def salvar(self):
        """Salva todos os dados coletados em um arquivo CSV."""
        if not self.dados:
            print("Nenhum dado foi coletado para gerar o relatório.")
            return
            
        # Pega todas as chaves (colunas) possíveis para o cabeçalho
        fieldnames = sorted(list(set(key for row in self.dados for key in row.keys())))
            
        with open(self.arquivo_relatorio, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.dados)