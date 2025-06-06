class ChatInterface {
    constructor() {
        this.chatHistory = []; // ampma: Initialize chatHistory
        this.isPremium = false;
        this.isTyping = false;
        this.isPaid = false;
        this.premiumMessage = '';
        this.fileLinks = [];
        this.fileNames = [];
        this.thumbnailLinks = [];
        this.partnerNames = [];
        this.pdfDocuments = []; // ampma: Initialize pdfDocuments
        this.clientId = "user123";
        this.socket = null;
        this.status = '';
        this.initializeEventListeners();
        this.initializeWebSocket();
    }

    initializeEventListeners() {
        // Attach an event listener to the Send button.
        // Should check if button is in DOM before attaching.
        console.log("initializeEventListeners called");
        const sendButton = document.querySelector('#sendButton');
        if (sendButton) {
            console.log("sendButton exists");
            sendButton.addEventListener('click', () => {
                this.handleUserInput();
            });
        }

        // Listen for the Enter key press
        const userInput = document.getElementById('userInput');
        if(userInput) {
            userInput.addEventListener('keypress', (event) => {
                if (event.key === 'Enter' && userInput.value.trim() !== '') {
                    event.preventDefault(); // Prevent form submission if applicable
                    this.handleUserInput();
                }
            });
        }

        document.addEventListener('click', (e) => {
            if (e.target.closest('.try-now-button')) {
                this.showUpgradeModal();
            } else if (e.target.closest('#watchAd')) {
                this.handleWatchAd();
            } else if (e.target.closest('#buyCredits')) {
                this.handleBuyCredits();
            } else if (e.target.closest('#continue')) {
                this.handleContinueFree();
            } else if (e.target.closest('.try-advanced')) {
                this.handleBuyCredits();
            }
        });
    }

    initializeWebSocket() {
        // Initialize WebSocket connection
        this.socket = new WebSocket(`ws://localhost:8000/ws/${this.clientId}`);

        this.socket.onopen = () => {
            console.log("WebSocket connection established");
        };

        this.socket.onmessage = async (event) => {
            console.log("Received WebSocket message:", event.data);
            const data = JSON.parse(event.data);

            switch(data.status) {
                case "started":
                    console.log("Premium response generation started");
                    this.status = "Premium response generation started"
                    if(this.isPaid){
                    await this.showStatus("Premium response generation started");}
                    break;
                case "searching":
                case "searching_videos":
                case "synthesizing":
                    console.log(data.message);
                    this.status = data.message
                    if(this.isPaid){
                    await this.showStatus(data.message);}
                    break;
                case "completed":
                    console.log("Premium response completed");
                    this.status = "Premium response completed";
                    // Handle the premium response data
                    if (data.data) {
                        this.premiumMessage = data.data.gemini_response;
                        this.fileLinks = data.data.video_file_links;
                        this.fileNames = data.data.video_file_names;
                        this.thumbnailLinks = data.data.thumbnail_links;
                        this.partnerNames = data.data.partner_names;
                        this.pdfDocuments = data.data.pdf_documents;
                        // Update UI with premium content

                        if(this.isPaid){
                        await this.showPremiumContent();}
                        }
                    break;
                case "error":
                    console.error("Premium response error:", data.message);
                    break;
            }
        };

        this.socket.onclose = () => {
            console.log("WebSocket connection closed");
            // Attempt to reconnect after a delay
            setTimeout(() => this.initializeWebSocket(), 5000);
        };

        this.socket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };
    }

    async handleUserInput() {
        console.log("handleUserInput called");
        const inputElement = document.getElementById('userInput');
        const messageText = inputElement.value.trim();

         // Clear welcome message
         const welcomeContainer = document.querySelector('.welcome-container');
         if (welcomeContainer) {
            welcomeContainer.classList.add('fade-out');
            await new Promise(resolve => setTimeout(resolve, 500));
            welcomeContainer.remove();
         }

        if (messageText === '' || this.isTyping) return;

        inputElement.value = '';
        await this.addMessage('user', messageText);

        // ampma: posting to /chat
        try {
            this.isTyping = true;
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: messageText,
                    chatHistory: this.chatHistory,
                    clientId: this.clientId
                 })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            } else {

                // this is not triggering async. Need to fix.
                // this.showStatus("Determining if premium response is applicable...");


                const data = await response.json();

                console.log('<HandleUserInput> Response from /chat: ', data);

                this.isPremium = data.premium_applicable;
                // Handle response from the server
                await this.addMessage('assistant', data.gemini_response)
                console.log('<HandleUserInput> Gemini Response: ',data.gemini_response)
                console.log('<HandleUserInput> data.premium_applicable: ',data.premium_applicable)
            }

        } catch (error) {
            console.log("Error sending message to /chat: ", error);
            await this.addMessage('assistant', "Sorry, there was an error processing your request. Please try again.");
        } finally {
            this.isTyping = false;
        }
    }

    async addMessage(role, content) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');

        // ampma: Add message to chatHistory
        let isPremium = this.isPremium;
        let isPaid = this.isPaid;
        let fileLinks = this.fileLinks;
        let fileNames = this.fileNames;
        let thumbnailLinks = this.thumbnailLinks;
        let partnerNames = this.partnerNames;
        this.chatHistory.push({role: role, content: content, isPremium: isPremium});

        console.log('<addMessage>: isPremium: ',isPremium)
        console.log('<addMessage>: Premium Response: ', this.premiumMessage)
        console.log('<addMessage>: fileLinks: ', fileLinks)
        console.log('<addMessage>: videoFileName: ', fileNames)
        console.log('<addMessage>: thumbnailLinks: ', thumbnailLinks)
        console.log('<addMessage>: partnerNames: ', partnerNames)

        if (role === 'user') {
            messageDiv.className = 'user-message';
            messageDiv.textContent = content;
            chatMessages.appendChild(messageDiv);
        } else if (role === 'assistant') {
            messageDiv.className = 'message ai-message';
            const formattedContent = content.replace(/\n/g, '<br>');

            // Need to loop through this
            let videoChipComponent = ''

            if (isPaid && isPremium) {
                for (let i = 0; i < fileLinks.length; i++) {
                    videoChipComponent += `

                    <div class="rag-card">
                        <div class="card-header">
                            <span class="card-url">${fileLinks[i]}</span>
                        </div>

                        <div class="card-body">
                            <h4 class="card-title">
                                 <span class="material-icons video-icon">video_library</span>
                                <a href="${fileLinks[i]}" target="_blank" title="${fileNames[i]}"> ${fileNames[i]} </a>

                            </h4>
                            <div class="thumbnail-container">
                                <a href="${fileLinks[i]}" target="_blank" title="${fileNames[i]}">
                                  <img class="thumbnail" src="${thumbnailLinks[i]}" alt="${fileNames[i]}">
                                </a>
                            </div>
                        </div>

                        <div class="card-footer">
                            <span>Source: ${partnerNames[i]}</span>
                            <a class="material-icons preview-icon" title="Preview" href="${fileLinks[i]}" target="_blank">visibility</a>
                        </div>
                </div>
                    </div>

                    `

                    console.log('in for loop for', fileLinks[i]);
                    console.log(videoChipComponent);
                    this.isPremium = false;
                }
            }

            // const videoChipComponent = isPaid ? ` <div class="premium-prompt-chip">
            // <span class="material-icons">verified</span>
            // <button class="try-now-button"> <a class='video-link' href="${this.videoFileLink[0]}" target="_blank">Watch Video</a></button>

            // </div>` : '';
            // console.log('video chip', videoChipComponent);

            const premiumChip = (isPremium && !isPaid) ? `
                <div class="premium-prompt-chip">
                    <span class="material-icons">verified</span>
                    Get Premium Answer with DataSense Partner Data
                    <button class="try-now-button chip-button">Try now</button>
                </div>
            ` : ''

            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <img src="static/images/google-gemini-icon.png" alt="Gemini" class="gemini-icon">
                </div>
                <div class="message-content">
                    <div style="white-space: pre-line">${formattedContent}</div>
                    ${premiumChip}
                    <div class="pdf-cards-container"></div>
                    <div class="videoChipComponent">${videoChipComponent}<div>
                    <div class="message-actions">
                        <button title="Like">
                            <span class="material-icons">thumb_up</span>
                        </button>
                        <button title="Dislike">
                            <span class="material-icons">thumb_down</span>
                        </button>
                        <button title="Regenerate">
                            <span class="material-icons">refresh</span>
                        </button>
                        <button title="Share">
                            <span class="material-icons">share</span>
                        </button>
                        <button title="More">
                            <span class="material-icons">more_vert</span>
                        </button>
                    </div>
                </div>
            `;
            if (isPaid && isPremium) {
                const pdfContainer = messageDiv.querySelector('.pdf-cards-container');
                if (pdfContainer) {
                    this.displayPdfCards(pdfContainer);
                }
            }
            chatMessages.appendChild(messageDiv);
            messageDiv.querySelector('.message-avatar').classList.add('typing');
            setTimeout(() => {
                messageDiv.querySelector('.message-avatar').classList.remove('typing');
            }, 1000);
        }
        smoothScrollTo(chatMessages, chatMessages.scrollHeight);
    }

    /**
     * Renders PDF cards into a given container element.
     * @param {HTMLElement} container - The element to append the cards to.
     */
     async displayPdfCards(container) {
        // Do nothing if there are no documents to display
        if (!this.pdfDocuments || this.pdfDocuments.length === 0) {
            return;
        }

        this.pdfDocuments.forEach(doc => {
            // Create the main card element
            const card = document.createElement('div');
            card.className = 'rag-card';

            // Use innerHTML to build the card structure
            card.innerHTML = `
                <div class="card-header">
                    <span class="card-url">${doc.link}</span>
                </div>
                <div class="card-body">
                    <h4 class="card-title">
                        <span class="material-icons pdf-icon">picture_as_pdf</span>
                        <a href="${doc.link}" target="_blank" title="${doc.title}"> ${doc.title}</a>
                    </h4>
                    <p class="card-snippet">${doc.snippets && doc.snippets.length > 0 ? doc.snippets.join(" ") : 'No snippet available.'}</p>
                </div>
                <div class="card-footer">
                    <span class="card-page-number">Page: ${doc.page_number}</span>
                    <a class="material-icons preview-icon" title="Preview" href="${doc.link_with_page}" target="_blank">visibility</a>
                </div>
            `;

            // Append the completed card to the container
            container.appendChild(card);
        });

        // Clear the array after rendering to prevent duplicates in future messages
        this.pdfDocuments = [];
    }

    async showUpgradeModal() {
        const chatMessages = document.getElementById('chatMessages');
        const upgradeDiv = document.createElement('div');
        upgradeDiv.className = 'upgrade-container';
        upgradeDiv.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <div class="datasense-logo">
                        <img src="static/images/datasense.svg" alt="DataSense">
                    </div>
                    <div class="partner-logos">
                        <img src="static/images/thoughtleaders-logo.png" alt="Thought Leaders">
                        <span class="more-partners">+</span>
                    </div>
                </div>
                <h2>Upgrade to DataSense</h2>
                <p class="subtitle">Your inital answer was based on fair-use content and publicly available data.</p>

                <p class="subtitle">DataSense answers leverage proprietary partner data / content. Enhance your answer with exclusive insights from our partners.

                <div class="upgrade-options">
                    <button id="continue" class="option-button">
                        <span>No Thanks</span>
                        <span class="subtext">Continue with generic data and answers</span>
                        <span class="arrow">›</span>
                    </button>
                    <button id="watchAd" class="option-button">
                        <span>Watch an Ad</span>
                        <span class="subtext">Unlock DataSense for this answer by watching an ad</span>
                        <span class="arrow">›</span>
                    </button>
                    <button id="buyCredits" class="option-button">
                        <span>Buy Credits</span>
                        <span class="subtext">Unlock the most up to date, relevant answers</span>
                        <span class="arrow">›</span>
                    </button>
                </div>
            </div>
        `;
        chatMessages.appendChild(upgradeDiv);
        smoothScrollTo(chatMessages, chatMessages.scrollHeight);
    }

    hideUpgradeModal() {
        const modal = document.getElementById('upgradeModal');
        modal.classList.remove('show');
    }

    async handleWatchAd() {
        const upgradeDiv = document.querySelector('.upgrade-container');
        if (upgradeDiv) {
            upgradeDiv.classList.add('fade-out');
            await new Promise(resolve => setTimeout(resolve, 500));
            upgradeDiv.remove();
        }

        const adOverlay = document.createElement('div');
        adOverlay.className = 'ad-overlay';

        // Create ad container
        adOverlay.innerHTML = `
            <div class="ad-container">
                <div class="ad-header">
                    <span class="ad-title">Watch this ad to unlock premium content</span>
                    <button class="skip-button" disabled>Skip Ad (5)</button>
                </div>
                <div class="ad-iframe-container">
                    <iframe
                        src="https://www.youtube.com/embed/G4h14tc2wHo?autoplay=1"
                        title="YouTube video player"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowfullscreen>
                    </iframe>
                </div>
            </div>
        `;

        document.body.appendChild(adOverlay);

        // Handle skip button countdown
        const skipButton = adOverlay.querySelector('.skip-button');
        let timeLeft = 5;

        const countdownInterval = setInterval(() => {
            timeLeft--;
            if (timeLeft > 0) {
                skipButton.textContent = 'Skip Ad ';
                skipButton.setAttribute('data-time', `(${timeLeft})`);
            } else {
                skipButton.textContent = 'Skip Ad';
                skipButton.disabled = false;
                skipButton.style.opacity = '';
                skipButton.style.cursor = '';
                skipButton.onclick = async () => {
                    adOverlay.classList.add('fade-out');
                    await new Promise(resolve => setTimeout(resolve, 300));
                    adOverlay.remove();
                    clearInterval(countdownInterval);
                    this.showPremiumContent();
                };
            }
        }, 1000);

        // Add CSS for disabled state
        skipButton.style.opacity = '0.5';
        skipButton.style.cursor = 'not-allowed';

        // Auto-close after 30 seconds if not skipped
        await new Promise(resolve => setTimeout(resolve, 30000));
        this.isPaid = true;
        if (document.body.contains(adOverlay)) {
            adOverlay.remove();
            clearInterval(countdownInterval);
            await this.showPremiumContent();
        }
    }

    async handleBuyCredits() {
        const upgradeDiv = document.querySelector('.upgrade-container');
        if (upgradeDiv) {
            upgradeDiv.classList.add('fade-out');
            await new Promise(resolve => setTimeout(resolve, 500));
            upgradeDiv.remove();
        }

        const buyModal = document.createElement('div');
        buyModal.className = 'buy-credits-overlay';
        buyModal.innerHTML = `
            <div class="buy-credits-modal">
                <div class="buy-credits-header">
                    <div class="header-top">
                        <div class="datasense-logo">
                            <img src="static/images/datasense.svg" alt="Gemini">
                        </div>
                        <div class="partner-logos">
                            <img src="static/images/thoughtleaders-logo.png" alt="Thought Leaders">
                            <span class="more-partners">+</span>
                        </div>
                        <button class="close-button">
                            <span class="material-icons">close</span>
                        </button>
                    </div>
                    <h2>Buy DataSense Credits</h2>
                    <p>To continue browsing with data from premium data buy <b>datasense credits<b>.</p>
                </div>
                <div class="credits-options">
                    <label class="credit-option">
                        <input type="radio" name="credits" value="25" checked>
                        <div class="credit-content">
                            <div class="credit-amount">25 DataSense Credits</div>
                            <div class="credit-description">Good for smaller targeted research sessions</div>
                        </div>
                    </label>
                    <label class="credit-option">
                        <input type="radio" name="credits" value="50">
                        <div class="credit-content">
                            <div class="credit-amount">50 DataSense Credits</div>
                            <div class="credit-description">Best for mid-sized research sessions</div>
                        </div>
                    </label>
                    <label class="credit-option subscription">
                        <input type="radio" name="credits" value="subscription">
                        <div class="credit-content">
                            <div class="credit-amount">Subscribe to Gemini with DataSense</div>
                            <div class="credit-description">200 credits per month + all Gemini Advanced features</div>
                            <div class="subscription-price">$149/month</div>
                        </div>
                    </label>
                </div>

                <div class="order-details">
                    <h3>Order Details:</h3>
                    <div class="order-summary">
                        <span>25 Premium Data Credits</span>
                        <span class="price">$25.00</span>
                    </div>
                    <div class="payment-methods">
                        <img src="static/images/visa.svg" alt="Visa">
                        <img src="static/images/mastercard.svg" alt="Mastercard">
                        <img src="static/images/amex.svg" alt="Maestro">
                        <img src="static/images/paypal.svg" alt="Google Pay">
                    </div>
                    <button class="buy-button">
                        Buy
                        <span class="material-icons">arrow_forward</span>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(buyModal);

        // Handle close button
        const closeButton = buyModal.querySelector('.close-button');
        closeButton.onclick = async () => {
            buyModal.classList.add('fade-out');
            await new Promise(resolve => setTimeout(resolve, 300));
            buyModal.remove();
        };

        // Handle buy button
        const buyButton = buyModal.querySelector('.buy-button');
        buyButton.onclick = async () => {
            buyModal.classList.add('fade-out');
            await new Promise(resolve => setTimeout(resolve, 300));
            buyModal.remove();

            // Show success toast
            const toast = document.createElement('div');
            toast.className = 'success-toast';
            toast.innerHTML = `
                <span class="material-icons">check_circle</span>
                Transaction charged to Google Account
            `;
            document.body.appendChild(toast);

            // Remove toast after 3 seconds
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 3000);


            this.isPaid = true;
            await this.showStatus(this.status);
            // await this.showPremiumContent();
        };

        // Add after creating the buyModal
        const radioButtons = buyModal.querySelectorAll('input[type="radio"]');
        const orderSummary = buyModal.querySelector('.order-summary');

        radioButtons.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.value === 'subscription') {
                    orderSummary.innerHTML = `
                        <span>Gemini with DataSense Subscription</span>
                        <span class="price">$149.00/month</span>
                    `;
                } else {
                    orderSummary.innerHTML = `
                        <span>${radio.value} Premium Data Credits</span>
                        <span class="price">$${radio.value}.00</span>
                    `;
                }
            });
        });
    }

    handleContinueFree() {
        const upgradeDiv = document.querySelector('.upgrade-container');
        if (upgradeDiv) upgradeDiv.remove();
        this.addMessage('assistant', conversationFlow.basicResponse.content);
    }

    async showPremiumContent() {
        const premiumMessage = this.premiumMessage;
        console.log('<showPremiumContent> premiumMessage', premiumMessage);
        this.status = "";
        await this.addMessage('assistant', premiumMessage);
    }

    async showStatus(statusMessage) {
        console.log('<showStatus> status', statusMessage);
        await this.addMessage('assistant', statusMessage);
    }
}

// Smooth scroll implementation
function smoothScrollTo(element, target) {
    const start = element.scrollTop;
    const distance = target - start;
    const duration = 300;
    let startTime = null;

    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const progress = Math.min(timeElapsed / duration, 1);

        element.scrollTop = start + distance * easeInOutQuad(progress);

        if (timeElapsed < duration) {
            requestAnimationFrame(animation);
        }
    }

    function easeInOutQuad(t) {
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }

    requestAnimationFrame(animation);
}

// Initialize the chat interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();

});
