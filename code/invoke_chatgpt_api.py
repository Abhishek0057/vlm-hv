import requests
import base64
from IPython.display import display, Markdown
import pandas as pd
import re
import os
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import time

def resize_image(input_image_path, output_image_path, max_size):
    os.makedirs(os.path.dirname(output_image_path), exist_ok=True)  # Ensure the directory exists
    with Image.open(input_image_path) as img:
        img.thumbnail((max_size, max_size))  # Resize image maintaining aspect ratio
        img.save(output_image_path)
    
def load_image_as_base64(file_path, input_image_directory):
    file_path = f"{input_image_directory}/{file_path}"
    reduced_file_path = f"reduced_{file_path}"
    resize_image(file_path, reduced_file_path, max_size=800)
    
    with open(reduced_file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_test_dataframe(parquet_file_path):
    df = pd.read_parquet(parquet_file_path)
    df = pd.concat([df.head(5), df.tail(5)])
    #df = df[1:5]
    print(df)
    return df

def build_explanation_prompt(row, input_image_directory):
    encoded_image_one = load_image_as_base64(row['sample1'], input_image_directory)
    encoded_image_two = load_image_as_base64(row['sample2'], input_image_directory)

    prompt = f"""
    You are a Forensic Document Examiner. You will be provided with two handwritten samples images. Your task is to provide a explanation comparing two handwritten samples are written by the same writer or by different writers as follows:

    - "Explanation" : 

    Handwriting sample 1:
    {encoded_image_one}

    Handwriting sample 2:
    {encoded_image_two}
    """
    return prompt

def build_payload(messages, temperature=None):
    payload = {
        "model": "gpt-4o",  # Make sure to use the appropriate model
        "messages": messages
    }
    if temperature is not None:
        payload["temperature"] = temperature
    return payload

def build_decision_prompt():
    prompt = f"""
    Based on the explanation, what is the decision?
    """
    return prompt

def determine_decision(text):
    unknown_pattern = re.compile(r'\bUnknown\b', re.IGNORECASE)
    yes_pattern = re.compile(r'\bYes\b', re.IGNORECASE)
    no_pattern = re.compile(r'\bNo\b', re.IGNORECASE)

    unknown_match = re.search(unknown_pattern, text)
    if unknown_match:
        return "Unknown"

    yes_match = re.search(yes_pattern, text)
    no_match = re.search(no_pattern, text)

    if yes_match and not no_match:
        return "Yes"
    elif no_match and not yes_match:
        return "No"
    elif not yes_match and not no_match:
        return "Unknown"
    else:
        return "Both"

def save_row_to_parquet(row, index, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_name = f"{index}_{row['sample1']}_{row['sample2']}.parquet"
    file_path = os.path.join(directory, file_name)
    df = pd.DataFrame([row])
    df.to_parquet(file_path)

def post_process_decision(response_content2):
    return determine_decision(response_content2)

def invoke_chatgpt_endpoint(payload, headers):
    return requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

def process_row(api_key, row, index, output_directory, headers, input_image_directory, updated_rows):
    print("Processing index : ", index)
    messages = []
    explanation_prompt = build_explanation_prompt(row, input_image_directory)
    messages = [
        {"role": "system", "content": "You are a Forensic Document Examiner."},
        {"role": "user", "content": explanation_prompt}
    ]
    explanation_payload = build_payload(messages, temperature=None)  #None temp
    explanation_response = invoke_chatgpt_endpoint(explanation_payload, headers)

    if explanation_response.status_code == 200:
        response_data = explanation_response.json()
        response_content = response_data['choices'][0]['message']['content']
        row['explanation'] = response_content
        print(f"Explanation : {index} : ", response_content)
        messages.append({"role": "assistant", "content": response_content})
        decision_prompt = build_decision_prompt()
        messages.append({"role": "user", "content": decision_prompt})

        decision_payload = build_payload(messages, temperature=None) #None temp
        decision_response = invoke_chatgpt_endpoint(decision_payload, headers)

        if decision_response.status_code == 200:
            time.sleep(1)
            response_data2 = decision_response.json()
            response_content2 = response_data2['choices'][0]['message']['content']
            print(f"Decision response_content2 : {index} :", response_content2)
            decision = post_process_decision(response_content2)
            if decision == "Unknown":
                return
            row['decision'] = decision
            print(f"Decision : {index} :", decision)
            # Save updated row to dictionary
            updated_rows[index] = row
        else:
            display(Markdown(f"**Error:** {decision_response.status_code}\n\n{decision_response.text}"))
    else:
        display(Markdown(f"**Error:** {explanation_response.status_code}\n\n{explanation_response.text}"))

def invoke_chatgpt(api_key, test_df, output_directory, input_image_directory, parallel=True):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    updated_rows = {}

    if parallel:
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(process_row, api_key, row, index, output_directory, headers, input_image_directory, updated_rows)
                for index, row in test_df.iterrows()
            ]
            for future in futures:
                future.result()
    else:
        for index, row in test_df.iterrows():
            process_row(api_key, row, index, output_directory, headers, input_image_directory, updated_rows)

    # Update the DataFrame with the updated rows
    for index, row in updated_rows.items():
        print(row)
        test_df.loc[index] = row

    return test_df

def main():
    for i in range(1):
        api_key = '<api-key>'
        output_directory = f'./output_original_letter_parquet_files/final_100_{i}'
        parquet_file_path = "1000_LETTER_test_samples.parquet"
        input_image_directory = f"original_letter_images"

        test_df = get_test_dataframe(parquet_file_path)
        test_df = invoke_chatgpt(api_key, test_df, output_directory, input_image_directory, parallel=False)
        print(f"Completed running {i} times")
        #print("Test df:", test_df)


