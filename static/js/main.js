/* static/js/script.js */

// Atualiza os dados a cada 150ms
setInterval(async () => {
    try {
        // Faz a requisição para a rota do Flask
        const res = await fetch('/status');
        const data = await res.json();

        // 1. Atualiza Contagem e Fase (Topo)
        document.getElementById('reps').innerText = data.reps;
        document.getElementById('phase').innerText = data.phase;

        // 2. Atualiza Feedback de Postura (Fundo)
        const fbEl = document.getElementById('feedback');
        fbEl.innerText = data.feedback;
        
        // Atualiza a classe de cor baseada no tipo de feedback
        // Ex: status-CORRETO, status-ERRO_CRITICO
        fbEl.className = `feedback-main status-${data.feedback_type}`;

    } catch(e) { 
        console.error("Erro na comunicação com o servidor:", e); 
    }
}, 150); 

async function finishWorkout() {
    try {
        const res = await fetch('/finish_workout');
        const data = await res.json();
        
        // Preenche o modal com o relatório recebido
        document.getElementById('reportText').innerText = data.report;
        
        // Mostra o modal
        document.getElementById('reportModal').style.display = 'flex';
    } catch (error) {
        console.error("Erro ao finalizar treino:", error);
        alert("Erro ao gerar relatório.");
    }
}