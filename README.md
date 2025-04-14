# Commands




```bash
uvicorn main:app --reload
```

# Env variables 
These are variables you can control. If the variable includes a default value, you can skip it.


GCP_PROJECT
GCP_LOCATION
SYSTEM_INSTRUCTION='You are Gemini, a helpful chat assistant'
GCP_MODEL="gemini-2.0-flash-001"
MODEL_TEMPERATURE=0.2
MODEL_TOP_P=0.8
MODEL_MAX_OUTPUT_TOKENS=1024


# Architecture


```mermaid
sequenceDiagram
    participant User
    participant WebBrowser
    participant FastAPI as FastAPI:main.py
    participant DataSense as datasense.py
    participant Gemini as gemini.py

    Note over User,WebBrowser: User requests the root endpoint
    User->>+WebBrowser: GET /
    WebBrowser->>+FastAPI: GET /
    activate FastAPI
    FastAPI-->>-WebBrowser: index.html
    deactivate FastAPI
    

    User->>+WebBrowser: User enters message
    WebBrowser->>+FastAPI: POST /chat {message, chatHistory}
    activate FastAPI
    FastAPI->>+DataSense: chat_response(chatHistory, message)
    activate DataSense
    DataSense->>+Gemini: generate(content_history, user_input)
    activate Gemini
    Gemini-->>-DataSense: chat_history, model_response
    deactivate Gemini
    DataSense->>DataSense: premium_applicable(chatHistory) -> premiumFlag
    DataSense-->>-FastAPI: Dict {chatHistory, modelResponse, premiumFlag}
    deactivate DataSense
    FastAPI-->>-WebBrowser: JSON {chatHistory, modelResponse, premiumFlag}
    deactivate FastAPI
    WebBrowser->>WebBrowser: Update UI with response
```


![alt text](image.png)