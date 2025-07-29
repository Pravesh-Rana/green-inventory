document.addEventListener('DOMContentLoaded', function() {
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');

    /**
     * Creates and appends a new chat message to the chat window.
     * @param {string} message - The message text.
     * @param {string} sender - 'user' or 'bot'.
     */
    function addMessage(message, sender) {
        // Create the main message container
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('chat-message', `${sender}-message`);

        // Create the avatar icon
        const avatar = document.createElement('div');
        avatar.classList.add('message-avatar');
        const icon = document.createElement('i');
        icon.classList.add('bi');
        icon.classList.add(sender === 'user' ? 'bi-person-circle' : 'bi-robot');
        avatar.appendChild(icon);

        // Create the message bubble
        const messageBubble = document.createElement('div');
        messageBubble.classList.add('message-bubble');

        // Create the content div
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        messageContent.innerText = message;
        messageBubble.appendChild(messageContent);

        // Assemble the full message
        messageContainer.appendChild(avatar);
        messageContainer.appendChild(messageBubble);

        // Add to the chat window and scroll
        chatWindow.appendChild(messageContainer);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
    
    // Add the initial welcome message from the bot
    addMessage("Hello! I'm Green-Ops AI. Ask me about your inventory, or any other topic!", 'bot');


    async function handleUserMessage() {
        const question = chatInput.value.trim();
        if (!question) return;

        addMessage(question, 'user');
        chatInput.value = '';
        
        // Optional: show a "Bot is typing..." indicator
        addMessage("...", 'bot');
        const typingIndicator = chatWindow.lastChild;

        try {
            const response = await fetch('/api/chatbot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            // Remove the "typing" indicator and add the real response
            typingIndicator.remove();
            addMessage(data.answer, 'bot');

        } catch (error) {
            console.error('Error fetching chatbot response:', error);
            typingIndicator.remove();
            addMessage('Sorry, I am having trouble connecting. Please try again later.', 'bot');
        }
    }

    sendBtn.addEventListener('click', handleUserMessage);
    chatInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            handleUserMessage();
        }
    });
});