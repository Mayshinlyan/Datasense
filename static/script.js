const conversationFlow = {
    initialMessages: [
        // First exchange
        {
            role: 'user',
            content: 'How can I get a free business class upgrade on my next flight?'
        },
        {
            role: 'assistant',
            content: `Getting a free business class upgrade is a coveted travel perk, but it's important to understand that it's not guaranteed. However, there are strategies that can increase your chances. Here's a breakdown of key approaches:

1. Airline Loyalty and Status:
• Frequent Flyer Programs:
  - Joining an airline's frequent flyer program is the most fundamental step. Accumulating miles and achieving elite status can unlock upgrade opportunities.
• Airlines prioritize upgrades for their most loyal customers.
• Airline Credit Cards:
  - Many airline-branded credit cards offer benefits like priority boarding and potential upgrade consideration.

2. Strategic Booking and Timing:
• Travel During Off-Peak Times:
  - Flying during midweek or less popular travel times can increase the availability of business class seats.`
        },
        // Second exchange (with upgrade prompt)
        {
            role: 'user',
            content: 'What are the best times to try for an upgrade?'
        },
        {
            role: 'assistant',
            content: `Based on general travel patterns, here are the most opportune times to seek upgrades:

1. Mid-week flights (Tuesday and Wednesday)
2. Early morning or late evening departures
3. Holiday off-seasons
4. Business routes during weekends
5. Leisure routes during weekdays

Would you like to access premium data insights from our airline partners about specific success rates and optimal timing?`,
            shouldShowUpgrade: true
        }
    ],

    basicResponse: {
        role: 'assistant',
        content: `Here are some general tips for getting business class upgrades:

1. Join airline loyalty programs and earn status
2. Book flexible economy fares
3. Check for last-minute upgrade offers
4. Travel during off-peak times
5. Consider using miles or points

Keep in mind that upgrades are never guaranteed and depend on many factors including availability and your status level.`
    },

    premiumMessages: [
        {
            role: 'assistant',
            content: `<div class="premium-chip"><span class="material-icons">verified</span>DataSense Premium Insight</div>

Based on aggregated data from our airline partners:

• American Airlines: 72% of successful upgrades occur between 72-96 hours before departure
• Qantas: Highest upgrade success rate is 4.3x greater on Tuesday/Wednesday flights
• Delta: Premium members have 68% better chances when booking red-eye flights

Key timing strategies:
1. Monitor load factors using ExpertFlyer 72 hours before departure
2. Set alerts for business class seat availability changes
3. Check upgrade windows specific to your status level
4. Book flights with historically low business class occupancy

Partner-verified upgrade hacks:
1. Book "Y" or "B" fare classes for priority upgrade lists
2. Use airline partner status matches strategically
3. Consider split-cabin booking on longer routes
4. Target newly launched routes for better upgrade chances

Would you like specific details about any of these strategies?

<div class="sources-section">
    <div class="sources-title">
        <span>Data Provided by Premium Data Partners</span>
        <span class="material-icons">expand_more</span>
    </div>
    <div class="sources-grid">
        <div class="source-card">
            <div class="source-icon-container">
                <img src="static/images/aa.png" alt="American Airlines" class="source-icon">
            </div>
            <div class="source-content">
                <div class="source-title">How to get a flight upgrade and snag those business class perks - American Airlines</div>
                <div class="source-url">www.aa.com</div>
            </div>
            <span class="material-icons source-menu">more_vert</span>
        </div>
        <div class="source-card">
            <div class="source-icon-container">
                <img src="static/images/qantas.svg" alt="Qantas" class="source-icon">
            </div>
            <div class="source-content">
                <div class="source-title">What is priority boarding? - Qantas Airways</div>
                <div class="source-url">www.qantas.com</div>
            </div>
            <span class="material-icons source-menu">more_vert</span>
        </div>
        <div class="source-card">
            <div class="source-icon-container">
                <img src="static/images/delta.jpg" alt="Delta" class="source-icon">
            </div>
            <div class="source-content">
                <div class="source-title">Claim Compensation for Overbooked Flights - Delta</div>
                <div class="source-url">www.delta.com</div>
            </div>
            <span class="material-icons source-menu">more_vert</span>
        </div>
    </div>
</div>`
        }
    ]
};

class ChatInterface {
    constructor() {
        this.chatHistory = []; // ampma: Initialize chatHistory
        this.isPremium = false;
        this.isTyping = false;
        this.initializeEventListeners();
        // Start the demo after a short delay
        // ampma:
        // setTimeout(() => this.startDemo(), 500);
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

    async startDemo() {
        let skipTyping = false;

        // Add event listener for Enter key
        const skipHandler = (e) => {
            if (e.key === 'Enter') {
                skipTyping = true;
            }
        };
        document.addEventListener('keydown', skipHandler);

        // Wait for initial load
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Clear welcome message
        const welcomeContainer = document.querySelector('.welcome-container');
        welcomeContainer.classList.add('fade-out');
        await new Promise(resolve => setTimeout(resolve, 500));
        welcomeContainer.remove();

        // First exchange
        const inputElement = document.getElementById('userInput');
        const firstQuestion = conversationFlow.initialMessages[0].content;

        if (!skipTyping) {
            for (let i = 0; i < firstQuestion.length; i++) {
                if (skipTyping) break;
                inputElement.value += firstQuestion[i];
                await new Promise(resolve => setTimeout(resolve, 20));
            }
        }

        inputElement.value = firstQuestion;
        await new Promise(resolve => setTimeout(resolve, 300));
        inputElement.value = '';
        await this.addMessage('user', firstQuestion);
        await new Promise(resolve => setTimeout(resolve, 1000));
        await this.addMessage('assistant', conversationFlow.initialMessages[1].content);
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Second exchange
        const secondQuestion = conversationFlow.initialMessages[2].content;

        if (!skipTyping) {
            for (let i = 0; i < secondQuestion.length; i++) {
                if (skipTyping) break;
                inputElement.value += secondQuestion[i];
                await new Promise(resolve => setTimeout(resolve, 20));
            }
        }

        inputElement.value = secondQuestion;
        await new Promise(resolve => setTimeout(resolve, 300));
        inputElement.value = '';
        await this.addMessage('user', secondQuestion);
        await new Promise(resolve => setTimeout(resolve, 1000));
        await this.addMessage('assistant', conversationFlow.initialMessages[3].content);
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Clean up event listener
        document.removeEventListener('keydown', skipHandler);
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

        /* ampma
        // Get the next assistant message
        const nextMessage = conversationFlow.initialMessages[this.currentMessageIndex + 1];
        await this.addMessage('assistant', nextMessage.content);

        this.currentMessageIndex += 2;

        // Show upgrade modal after third exchange
        if (nextMessage.shouldShowUpgrade) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            this.showUpgradeModal();
        }
        */

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
                    chatHistory: this.chatHistory
                 })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Response from le /chat: ', data);

            // Handle response from the server
            await this.addMessage('assistant', data.modelResponse.parts[0].text, data.premiumFlag, data.videoFileLink)

            // Check if premium content should be shown
            //if (data.premiumFlag) {
            //    await new Promise(resolve => setTimeout(resolve, 1000));
            //    this.showUpgradeModal();
            //}
        } catch (error) {
            console.log("Error sending message to /chat: ", error);
            await this.addMessage('assistant', "Sorry, there was an error processing your request. Please try again.");
        } finally {
            this.isTyping = false;
        }
    }

    async addMessage(role, content, isPremium, videoFileLink) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');

        // ampma: Add message to chatHistory
        this.chatHistory.push({role: role, content: content, isPremium: isPremium})

        if (role === 'user') {
            messageDiv.className = 'user-message';
            messageDiv.textContent = content;
            chatMessages.appendChild(messageDiv);
        } else if (role === 'assistant') {
            messageDiv.className = 'message ai-message';
            const formattedContent = content.replace(/\n/g, '<br>');

            // display video link if available


            const videoChip = isPremium ? ` <div class="premium-prompt-chip">
            <span class="material-icons">verified</span>
            <button class="try-now-button"> <a class='video-link' href="${videoFileLink}" target="_blank">Watch Video</a></button>

            </div>` : '';
            console.log('video chip', videoChip);


            // ampma: Override below - we'll add premium chip IF premiumFlag is set.
            // Add premium chip if this is the second answer
            //const isPremiumPrompt = content === conversationFlow.initialMessages[3].content;
            const isPremiumPrompt = false;
            const premiumChip = isPremiumPrompt ? `
                    <div class="premium-prompt-chip">
                        <span class="material-icons">verified</span>
                        Get Premium Answer with DataSense Partner Data
                        <button class="try-now-button">Try now</button>
                    </div>
                ` : '';


            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <img src="static/images/google-gemini-icon.png" alt="Gemini" class="gemini-icon">
                </div>
                <div class="message-content">
                    <div style="white-space: pre-line">${formattedContent}</div>
                    ${videoChip}
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
            chatMessages.appendChild(messageDiv);
            messageDiv.querySelector('.message-avatar').classList.add('typing');
            setTimeout(() => {
                messageDiv.querySelector('.message-avatar').classList.remove('typing');
            }, 1000);
        }

        smoothScrollTo(chatMessages, chatMessages.scrollHeight);
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
                        <img src="static/images/aa.png" alt="American Airlines">
                        <img src="static/images/delta.jpg" alt="Qantas">
                        <img src="static/images/qantas.svg" alt="Delta">
                        <span class="more-partners">+</span>
                    </div>
                </div>
                <h2>Upgrade to DataSense</h2>
                <p class="subtitle">Your inital answer was based on fair-use content and publicly available data.</p>

                <p class="subtitle">DataSense answers leverage proprietary partner data / content. Enhance your answer with exclusive insights from <strong>American Airlines, Qantas</strong> and <strong>Delta</strong>.</p>

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
                            <img src="static/images/delta.jpg" alt="delta">
                            <img src="static/images/qantas.svg" alt="qantas">
                            <img src="static/images/aa.png" alt="american airlines">
                            <span class="more-partners">+</span>
                        </div>
                        <button class="close-button">
                            <span class="material-icons">close</span>
                        </button>
                    </div>
                    <h2>Buy DataSense Credits</h2>
                    <p>To continue browsing with data from <strong>American Airlines, Delta</strong> and <strong>Qantas</strong> buy premium data / content credits.</p>
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

            // Show premium content
            this.isPremium = true;
            await this.showPremiumContent();
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
        const premiumMessage = conversationFlow.premiumMessages[0];
        await this.addMessage('assistant', premiumMessage.content);
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