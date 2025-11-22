import os
from datetime import datetime
from config import LOG_CONFIG
from collections import Counter

class Log:
    """
    Gera um relatório de SESSÃO focado em fornecer insights úteis para o usuário,
    incluindo em quais repetições específicas os erros ocorreram.
    """
    def __init__(self, exercise_config):
        """
        Inicializa as estruturas de dados para coletar estatísticas da sessão.
        """
        self.dir_logs = LOG_CONFIG['dir_logs']
        self.exercise_config = exercise_config
        self.exercise_name = exercise_config['name']
        
        self.stats = {
            'total_reps': 0,
            'ok_reps': 0,
            'invalid_reps': 0,
            'errors': {}
        }

        timestamp_file = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(self.dir_logs, f"resumo_{self.exercise_name}_{timestamp_file}.txt")
        
        self._make_dir_log()
    
    def _make_dir_log(self):
        """Cria o diretório para salvar o relatório, se ele não existir."""
        os.makedirs(self.dir_logs, exist_ok=True)
    
    def save_rep(self, rep_num, rep_ok, rep_error):
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
            for error in rep_error:
                if error not in self.stats['errors']:
                    self.stats['errors'][error] = {'count': 0, 'reps': []}
                
                self.stats['errors'][error]['count'] += 1
                self.stats['errors'][error]['reps'].append(rep_num)
    
    def save(self):
        """Salva o resumo estatístico da sessão em um arquivo de texto legível."""
        if self.stats['total_reps'] == 0:
            print("Nenhuma repetição foi completada para gerar o relatório.")
            return

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
            
            sorted_errors = sorted(self.stats['errors'].items(), key=lambda item: item[1]['count'], reverse=True)
            
            for i, (error_message, details) in enumerate(sorted_errors):
                reps_str = ', '.join(map(str, details['reps']))
                report_content.append(f"{i+1}. {error_message} (Ocorreu {details['count']} vez(es))")
                report_content.append(f"   -> Nas repetições: {reps_str}")
                
                # Procura a regra correspondente à mensagem de erro para dar o foco correto
                for rule in self.exercise_config['rules']['feedback']:
                    if rule['message'] == error_message:
                        # Verifica se é uma regra de 'zona' (que tem a chave 'angle')
                        if 'angle' in rule:
                            angle_name = rule['angle']
                            joints = self.exercise_config['angle_definitions'][angle_name]
                            joint_names = ', '.join(joints).replace('_', ' ').title()
                            report_content.append(f"   -> Foco: Alinhamento entre {joint_names}")

                        # Verifica se é uma regra 'relativa' (que tem 'angle1' e 'angle2')
                        elif 'angle1' in rule and 'angle2' in rule:
                            angle1_name = rule['angle1'].replace('_', ' ')
                            angle2_name = rule['angle2'].replace('_', ' ')
                            report_content.append(f"   -> Foco: Relacao entre {angle1_name} e {angle2_name}")
                        break # Encontrou a regra, pode parar de procurar
        else:
            report_content.append("\n--- EXCELENTE! ---")
            report_content.append("Você completou todas as repetições com boa postura!")

        # Escreve o conteúdo no arquivo .txt
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_content))
            
    def get_report_content(self):
        """
        Gera e retorna o conteúdo do relatório como uma string formatada,
        sem salvar no arquivo (útil para exibição web em tempo real).
        """
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
            report_content.append(f"Taxa de Sucesso na Postura: 0.0%\n")

        if self.stats['invalid_reps'] > 0:
            report_content.append("--- PONTOS PRINCIPAIS PARA MELHORAR ---")
            sorted_errors = sorted(self.stats['errors'].items(), key=lambda item: item[1]['count'], reverse=True)
            for i, (error_message, details) in enumerate(sorted_errors):
                report_content.append(f"{i+1}. {error_message} (Ocorreu {details['count']} vez(es))")
        else:
            if self.stats['total_reps'] > 0:
                report_content.append("\n--- EXCELENTE! ---")
                report_content.append("Você completou todas as repetições com boa postura!")
            else:
                report_content.append("\nNenhuma repetição registrada.")

        return "\n".join(report_content)