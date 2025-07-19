document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("chatbotModal");
    const input = document.getElementById("userInput");
    const chatWindow = document.getElementById("chatWindow");
    const toggleBtn = document.querySelector(".chatbot-toggle");
    const closeBtn = document.querySelector(".chatbot-close");
    const sendBtn = document.querySelector(".chatbot-send");

    if (!modal || !input || !chatWindow || !toggleBtn || !sendBtn || !closeBtn) return;

    toggleBtn.addEventListener("click", () => {
        modal.style.display = modal.style.display === "flex" ? "none" : "flex";
    });

    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") sendMessage();
    });

    sendBtn.addEventListener("click", () => {
        sendMessage();
    });

    const socket = new WebSocket("ws://" + window.location.host + "/ws/chat/");

    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        appendMessage("bot", data.message);
    };

    function sendMessage() {
        const message = input.value.trim();
        if (!message || socket.readyState !== WebSocket.OPEN) return;
        appendMessage("user", message);
        socket.send(JSON.stringify({ message }));
        input.value = "";
    }

    function appendMessage(sender, text) {
        const msg = document.createElement("div");
        msg.classList.add("chatbot-message", sender); // user or bot
        msg.innerText = text;
        chatWindow.appendChild(msg);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});
