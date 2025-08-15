document.addEventListener("DOMContentLoaded", () => {
    const tableBody = document.querySelector("table tbody");

    // Função para atualizar a tabela
    async function atualizarTabela() {
        try {
            // Faz a requisição para o backend Flask
            const response = await fetch("/bolsa");
            const html = await response.text();

            // Extrai apenas os dados da tabela do HTML retornado
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");
            const newTableBody = doc.querySelector("table tbody");

            if (newTableBody) {
                // Substitui os dados antigos pelos novos
                const newRows = newTableBody.querySelectorAll("tr");

                newRows.forEach((newRow, index) => {
                    const oldRow = tableBody.children[index];

                    // Verificar e animar as variações
                    const oldVariation = oldRow.querySelector(".positive, .negative");
                    const newVariation = newRow.querySelector(".positive, .negative");
                    const oldPercentage = oldRow.querySelector("td:nth-child(5)");
                    const newPercentage = newRow.querySelector("td:nth-child(5)");

                    // Verifica se o valor da variação ou % variação mudou
                    if (oldVariation.textContent.trim() !== newVariation.textContent.trim()) {
                        newVariation.classList.add(newVariation.textContent.trim() > 0 ? "variation-up" : "variation-down");
                    }

                    // Verifica se o valor da % variação mudou
                    if (oldPercentage.textContent.trim() !== newPercentage.textContent.trim()) {
                        newPercentage.classList.add(newPercentage.textContent.trim() > 0 ? "variation-up" : "variation-down");
                    }
                });

                // Atualiza o conteúdo da tabela com os novos dados
                tableBody.innerHTML = newTableBody.innerHTML;
            }
        } catch (error) {
            console.error("Erro ao atualizar tabela:", error);
        }
    }

    // Atualiza a tabela a cada 10 segundos
    setInterval(atualizarTabela, 10000);

    // Executa a atualização pela primeira vez
    atualizarTabela();
});
