document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("chatbotModal");
    const input = document.getElementById("userInput");
    const chatWindow = document.getElementById("chatWindow");
    const toggleBtn = document.querySelector(".chatbot-toggle");
    const closeBtn = document.querySelector(".chatbot-close");
    const sendBtn = document.querySelector(".chatbot-send");

    // WebSocket setup
    // const socket = new WebSocket("ws://" + window.location.host + "/ws/chat/");
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/chat/`);


    // Stop if any required elements are missing
    if (!modal || !input || !chatWindow || !toggleBtn || !sendBtn || !closeBtn) return;

    // Hide modal on load (safety)
    modal.style.display = "none";

    // Toggle chatbot modal on button click
    toggleBtn.addEventListener("click", () => {
        modal.style.display = modal.style.display === "flex" ? "none" : "flex";
    });

    // Close button always hides modal
    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    // Send message on Enter key
    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") sendMessage();
    });

    // Send message on send button click
    sendBtn.addEventListener("click", () => {
        sendMessage();
    });



    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        appendMessage("bot", data.message);
    };

    // Send message function
    function sendMessage() {
        const message = input.value.trim();
        if (!message || socket.readyState !== WebSocket.OPEN) return;
        appendMessage("user", message);
        socket.send(JSON.stringify({ message }));
        input.value = "";
    }

    // Append message to chat window
    function appendMessage(sender, text) {
        const msg = document.createElement("div");
        msg.classList.add("chatbot-message", sender); // user or bot
        msg.innerText = text;
        chatWindow.appendChild(msg);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});
