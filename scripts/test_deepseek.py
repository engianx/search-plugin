# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI

client = OpenAI(base_url="http://snoflake:8000/v1")

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Where is the capital of China?"},
    ],
    stream=False
)

print(response.choices[0].message.content)