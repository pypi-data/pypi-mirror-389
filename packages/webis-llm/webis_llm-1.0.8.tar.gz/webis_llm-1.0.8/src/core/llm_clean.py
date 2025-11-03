import os
import requests
from tqdm import tqdm
from dotenv import load_dotenv

class ResultFilter:

    @staticmethod
    def call_deepseek_api(text, api_key=None):
        # DeepSeek API 配置
        if api_key is None:
            api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DeepSeek API密钥未提供且未在环境变量中找到")
        
        base_url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        model_name = "deepseek-ai/DeepSeek-V3"
        prompt = f"""
        Act as a prudent text refinement assistant. Carefully read the entire text to grasp its core themes and logical structure. Remove only obvious fragmentary noise elements such as advertising snippets, repetitive promotional phrases, and platform-generated system messages. Preserve all potentially meaningful content including examples, technical details, and domain-specific terminology. When in doubt about content relevance, prioritize retention over deletion. Return the refined text strictly following these rules:1.No explanations - Provide only the cleaned text without any analysis.2.​Format integrity - Strictly preserve the original formatting and syntactic flow.3.​Minimal intervention - Limit changes to unquestionably non-essential elements.Now, please analyze and filter the following text:'{text}''
        """
        data = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "max_tokens": 20000,
            "stop": None,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "response_format": {"type": "text"}
        }
        try:
            response = requests.post(base_url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            # print(f"result:{result}")
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"api_key:{api_key}")
            print(f"Error calling DeepSeek API: {e}")
            print(f"Error response: {response.text}")
            print(f"Error status code: {response.status_code}")
            return text

    @staticmethod
    def call_chatgpt_api(text):
        # ChatGPT API 配置（如果将来需要使用）
        # 目前暂不支持，返回原文本
        raise NotImplementedError("ChatGPT API not implemented yet. Please use 'deepseek' instead.")
    
    @staticmethod
    def filter_text(text, api_type, api_key=None):
        # 根据指定的 API 类型调用相应的 API
        if api_type == "chatgpt":
            return ResultFilter.call_chatgpt_api(text)
        elif api_type == "deepseek":
            return ResultFilter.call_deepseek_api(text, api_key)
        else:
            raise ValueError("Unsupported API type. Supported types: 'deepseek'")

    @staticmethod
    def process_files(input_dir, output_dir, api_type, api_key=None):
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        file_count = 0

        # 遍历输入目录中的文件
        for filename in tqdm(os.listdir(input_dir), desc="Processing files"):
            if filename.endswith(".txt"):
                # 读取原始文本
                input_path = os.path.join(input_dir, filename)
                with open(input_path, 'r', encoding='utf-8') as f:
                    original_text = f.read()

                # 过滤文本
                filtered_text = ResultFilter.filter_text(original_text, api_type, api_key)

                # 保存过滤后的文本
                output_filename = filename
                output_path = os.path.join(output_dir, output_filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(filtered_text)

                file_count += 1

        print(f"过滤完成，共处理 {file_count} 个文件")
        print(f"过滤结果已保存到 {output_dir} 文件夹中")

def run_filter(input_dir, output_dir, api_type, api_key=None):
    """
    运行文本过滤流程。
    
    参数:
        input_dir (str): 输入目录，包含待过滤的文本文件。
        output_dir (str): 输出目录，用于保存过滤后的文本文件。
        api_type (str): 使用的 API 类型 ("chatgpt" 或 "deepseek")。
        api_key (str): API密钥（可选，如未提供则从环境变量读取）。
    """
    if api_key is None:
        load_dotenv()
        api_key = os.environ.get("DEEPSEEK_API_KEY")
    
    ResultFilter.process_files(input_dir, output_dir, api_type, api_key)

if __name__ == "__main__":
    input_dir = r"F:\data\sftllm_v2_predicted_texts"
    output_dir = r"F:\data\double_gpt_sftllm_v4_predicted_texts"

