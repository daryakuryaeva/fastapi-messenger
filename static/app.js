console.log("Messenger started");

async function refreshMessages() {
    const messagesBlock = document.getElementById("messages");

    if (!messagesBlock) return;

    const currentScroll = messagesBlock.scrollTop;

    const response = await response.text();

    const parser = new DOMParser();

    const doc = parser.parseFromString(html, "text/html");

    const newMessages = doc.getElementById("messages");

    if (newMessages) {
        messagesBlock.innerHTML = newMessages.innerHTML;
        scrollToBottom();

        messagesBlock.scrollTop = currentScroll;
    }
}

setInterval(refreshMessages, 2000);

function scrollToBottom() {
    const messages = document.getElementById("messages");

    if (messages) {
        messages.scrollTop = messages.scrollHeight;
    }
}

scrollToBottom();