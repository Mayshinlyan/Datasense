"""
DataSense Library
"""
from typing import List, Dict
from gemini import generate
from google.genai.types import Part, Content


def chat_response(history_obj: List[Dict], user_input: str, vector_store) -> Dict:
    """
    Takes user input. Gets Gemini response.
    """
    content_history: List[Content] = []
    for item in history_obj:
        if item['role'] == 'user':
            content_history.append(Content(role='user', parts=[Part.from_text(text=item['content'])]))
        elif item['role'] == 'assistant':
            content_history.append(Content(role='assistant', parts=[Part.from_text(text=item['content'])]))


    content_history, gemini_response_content, video_file_link, premium_response_content = generate(content_history, user_input, vector_store)
    print(f"Datasense.py: Gemini response received. {gemini_response_content}")
    print(f"Datasense.py: Premium response received. {premium_response_content}")

    if video_file_link!="N/A" and premium_response_content.parts[0].text!="N/A":
        premium_flag = True
        print(f"datasense.py: Premium response received. {premium_flag}")
    else:
        premium_flag = False
    return {"chatHistory": history_obj, "modelResponse": gemini_response_content, "premiumFlag": premium_flag, "videoFileLink": video_file_link, "premiumResponse": premium_response_content}
