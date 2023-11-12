import re

#function to extract session id from payload with regex 
def extract_session_id(session_str: str):
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string
    
    return ""


def get_str_from_food_dict(food_dict: dict):
    result = ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])
    return result

# if __name__ == "__main__":
# #     print(extract_session_id("projects/chatbot-emaan-food-orderi-oypl/agent/sessions/4c81f431-7fc3-d9d7-36a9-d8d4a7ed5cc7/contexts/__system_counters__"))
#     print(get_str_from_food_dict({"samosa": 2, "chole bhature": 5}))