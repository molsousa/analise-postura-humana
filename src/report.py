import os
from datetime import datetime
from config import CONFIG_RELATORIO
from collections import Counter

class Relatorio:
    """
    Gera um relatório de SESSÃO focado em fornecer insights úteis para o usuário.
    Em vez de um log por frame, ele cria um resumo com estatísticas de repetições
    e os erros de postura mais comuns.
    """
    def __init__(self, exercise_config):
        """
        Inicializa as estruturas de dados para coletar estatísticas da sessão.
        """
        self.diretorio_logs = CONFIG_RELATORIO['diretorio_logs']
        self.exercise_config = exercise_config
        self.exercise_name = exercise_config['name']
        
        # Estrutura para armazenar as estatísticas
        self.stats = {
            'total_reps': 0,
            'reps_boas': 0,
            'reps_invalidas': 0,
            'erros_cometidos': Counter() # Usamos um Counter para contar a frequência dos erros
        }

        # Gera um nome de arquivo .txt único com data e hora
        timestamp_arquivo = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.arquivo_relatorio = os.path.join(self.diretorio_logs, f"resumo_{self.exercise_name}_{timestamp_arquivo}.txt")
        
        self._criar_diretorio_log()
    
    def _criar_diretorio_log(self):
        """Cria o diretório para salvar o relatório, se ele não existir."""
        os.makedirs(self.diretorio_logs, exist_ok=True)
    
    def registrar_repeticao(self, foi_boa, erros_da_rep):
        """
        Registra os dados consolidados de uma única repetição finalizada.
        Este método é chamado pelo PostureAnalyzer ao final de cada rep.

        Args:
            foi_boa (bool): True se a repetição foi executada com boa postura, False caso contrário.
            erros_da_rep (set): Um conjunto contendo as mensagens de erro que ocorreram na rep.
        """
        self.stats['total_reps'] += 1
        if foi_boa:
            self.stats['reps_boas'] += 1
        else:
            self.stats['reps_invalidas'] += 1
            # Atualiza a contagem de cada erro que ocorreu nesta repetição inválida
            for erro in erros_da_rep:
                self.stats['erros_cometidos'][erro] += 1
    
    def salvar(self):
        """Salva o resumo estatístico da sessão em um arquivo de texto legível."""
        if self.stats['total_reps'] == 0:
            print("Nenhuma repetição foi completada para gerar o relatório.")
            return

        # Monta o conteúdo do arquivo de texto
        report_content = []
        report_content.append("="*40)
        report_content.append(f" RESUMO DA SESSÃO DE TREINO")
        report_content.append("="*40)
        report_content.append(f"Exercício: {self.exercise_name}")
        report_content.append(f"Data e Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

        report_content.append("--- DESEMPENHO GERAL ---")
        report_content.append(f"Total de Repetições: {self.stats['total_reps']}")
        report_content.append(f"  - Repetições Corretas: {self.stats['reps_boas']}")
        report_content.append(f"  - Repetições com Erros: {self.stats['reps_invalidas']}")
        
        try:
            percentual_sucesso = (self.stats['reps_boas'] / self.stats['total_reps']) * 100
            report_content.append(f"Taxa de Sucesso na Postura: {percentual_sucesso:.1f}%\n")
        except ZeroDivisionError:
            pass

        if self.stats['reps_invalidas'] > 0:
            report_content.append("--- PONTOS PRINCIPAIS PARA MELHORAR ---")
            # Lista os erros do mais comum para o menos comum
            erros_mais_comuns = self.stats['erros_cometidos'].most_common()
            
            for i, (erro_msg, contagem) in enumerate(erros_mais_comuns):
                report_content.append(f"{i+1}. {erro_msg} (Ocorreu em {contagem} repetições)")
                
                # Encontra o ângulo associado a essa mensagem de erro na configuração
                for rule in self.exercise_config['rules']['feedback']:
                    if rule['message'] == erro_msg:
                        angle_name = rule['angle']
                        joints = self.exercise_config['angle_definitions'][angle_name]
                        joint_names = ', '.join(joints).replace('_', ' ').title()
                        report_content.append(f"   -> Foco: Alinhamento entre {joint_names}")
                        break
        else:
            report_content.append("\n--- EXCELENTE! ---")
            report_content.append("Você completou todas as repetições com boa postura. Continue assim!")

        # Escreve o conteúdo no arquivo .txt
        with open(self.arquivo_relatorio, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_content))