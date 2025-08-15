document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".tab-button");
    const contents = document.querySelectorAll(".tab-content");
  
    buttons.forEach(button => {
      button.addEventListener("click", () => {
        // Remove a classe 'active' de todas as seções
        contents.forEach(content => content.classList.remove("active"));
  
        // Adicionar a classe 'active' na seção correspondente
        const tabId = button.getAttribute("data-tab");
        document.getElementById(tabId).classList.add("active");
      });
    });
  });

  
  