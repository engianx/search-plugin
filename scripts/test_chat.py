import asyncio
from search.utils.llm_chat import ChatCompletionGenerator


def chat_sync():
    chat = ChatCompletionGenerator()

        # Using raw messages
    response = chat.generate([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"}
    ])
    print(response)
    # Using simplified method
    response = chat.generate_with_context(
        system_prompt="You are a helpful assistant.",
        user_message="What is Python?",
        temperature=0.5
    )
    print(response)
    # Synchronous
    response = chat.generate_with_context("You are helpful.", "Hello!")
    print(response)

async def chat_async():
    chat = ChatCompletionGenerator()

    response = await chat.generate_with_context_async("You are helpful.", "Hello!")
    print(response)

    # Streaming
    async for chunk in chat.generate_with_context_stream("You are helpful.", "Hello!"):
        print(chunk, end="", flush=True)

chat_sync()

asyncio.run(chat_async())
