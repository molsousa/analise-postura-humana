import os
from datetime import datetime
from config import LOG_CONFIG
from collections import Counter

class Log:
    """
    Gera um relatório de SESSÃO focado em fornecer insights úteis para o usuário.
    Em vez de um log por frame, ele cria um resumo com estatísticas de repetições
    e os erros de postura mais comuns.
    """
    def __init__(self, exercise_config):
        """
        Inicializa as estruturas de dados para coletar estatísticas da sessão.
        """
        self.dir_logs = LOG_CONFIG['dir_logs']
        self.exercise_config = exercise_config
        self.exercise_name = exercise_config['name']
        
        # Estrutura para armazenar as estatísticas
        self.stats = {
            'total_reps': 0,
            'ok_reps': 0,
            'invalid_reps': 0,
            'errors': Counter() # Usamos um Counter para contar a frequência dos erros
        }

        # Gera um nome de arquivo .txt único com data e hora
        timestamp_file = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(self.dir_logs, f"resumo_{self.exercise_name}_{timestamp_file}.txt")
        
        self._make_dir_log()
    
    def _make_dir_log(self):
        """Cria o diretório para salvar o relatório, se ele não existir."""
        os.makedirs(self.dir_logs, exist_ok=True)
    
    def save_rep(self, rep_ok, rep_error):
        """
        Registra os dados consolidados de uma única repetição finalizada.
        Este método é chamado pelo PostureAnalyzer ao final de cada rep.

        Args:
            rep_ok (bool): True se a repetição foi executada com boa postura, False caso contrário.
            rep_error (set): Um conjunto contendo as mensagens de erro que ocorreram na rep.
        """
        self.stats['total_reps'] += 1
        if rep_ok:
            self.stats['ok_reps'] += 1
        else:
            self.stats['invalid_reps'] += 1
            # Atualiza a contagem de cada erro que ocorreu nesta repetição inválida
            for error in rep_error:
                self.stats['errors'][error] += 1
    
    def save(self):
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
        report_content.append(f"  - Repetições Corretas: {self.stats['ok_reps']}")
        report_content.append(f"  - Repetições com Erros: {self.stats['invalid_reps']}")
        
        try:
            sucess_percent = (self.stats['ok_reps'] / self.stats['total_reps']) * 100
            report_content.append(f"Taxa de Sucesso na Postura: {sucess_percent:.1f}%\n")
        except ZeroDivisionError:
            pass

        if self.stats['invalid_reps'] > 0:
            report_content.append("--- PONTOS PRINCIPAIS PARA MELHORAR ---")
            # Lista os erros do mais comum para o menos comum
            common_errors = self.stats['errors'].most_common()
            
            for i, (error_message, count) in enumerate(common_errors):
                report_content.append(f"{i+1}. {error_message} (Ocorreu em {count} repetições)")
                
                # Encontra o ângulo associado a essa mensagem de erro na configuração
                for rule in self.exercise_config['rules']['feedback']:
                    if rule['message'] == error_message:
                        angle_name = rule['angle']
                        joints = self.exercise_config['angle_definitions'][angle_name]
                        joint_names = ', '.join(joints).replace('_', ' ').title()
                        report_content.append(f"   -> Foco: Alinhamento entre {joint_names}")
                        break
        else:
            report_content.append("\n--- EXCELENTE! ---")
            report_content.append("Você completou todas as repetições com boa postura!")

        # Escreve o conteúdo no arquivo .txt
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_content))