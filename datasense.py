"""
DataSense Library
"""
from typing import Tuple, List, Dict
from gemini import generate
from google.genai.types import Part, Content

def premium_applicable(history_obj: str) -> bool:
    if len(history_obj) > 3:
        return True
    return False



def chat_response(history_obj: List[Dict], user_input: str) -> Dict:
    """
    Takes user input. Gets Gemini response.
    """
    content_history: List[Content] = []
    for item in history_obj:
        if item['role'] == 'user':
            content_history.append(Content(role='user', parts=[Part.from_text(text=item['content'])]))
        elif item['role'] == 'assistant':
            content_history.append(Content(role='assistant', parts=[Part.from_text(text=item['content'])]))
        
            
    content_history, model_response = generate(content_history, user_input)
    print("Model response received.")
    premium_flag = premium_applicable(history_obj)
    return {"chatHistory": history_obj, "modelResponse": model_response, "premiumFlag": premium_flag}
