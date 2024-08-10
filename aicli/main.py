import os
import io
import sys
import argparse
from openai import OpenAI
import pyperclip
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('aicli')

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

DEFAULT_MODEL = "gpt-4-0613"
DEFAULT_SYSTEM = "You are a helpful assistant."

def query_chatgpt(prompt, complete=False, model=DEFAULT_MODEL, system=DEFAULT_SYSTEM, output=sys.stdout):
    try:
        if complete == False:
            # Streaming response from OpenAI's API
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                stream=True  # Enable streaming mode
            )
        
            # Collecting and printing the streamed response
            collected_response = ""
            for chunk in stream:
                chunk_message = chunk.choices[0].delta.content or ""
                print(chunk_message, end="", flush=True, file=output)
                collected_response += chunk_message
        
            return collected_response
    
        else:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ]
            )
            
            print(response.choices[0].message.content, end="", flush=True, file=output)

    except openai.APIConnectionError as e:
        logger.error("The server could not be reached", exc_info=e)
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.
    except openai.RateLimitError as e:
        logger.error("A 429 status code was received; we should back off a bit.", exc_info=e)
    except openai.APIStatusError as e:
        logger.error("Another non-200-range status code was received", exc_info=e)
        print(e.status_code)
        print(e.response)        
        
def main():

    try:
        parser = argparse.ArgumentParser(description="Query OpenAI's ChatGPT")
        parser.add_argument('prompt', type=str, help='The prompt to send to ChatGPT or "-" to read from stdin')
        parser.add_argument('-m', '--model', default=DEFAULT_MODEL, help='model name')
        parser.add_argument('-c', '--complete', default=False, action='store_true', help='get a message when completed')
        parser.add_argument('-s', '--system', default=DEFAULT_SYSTEM, help='spcify a system content')
        parser.add_argument('-o', '--output', help='output destination, "clip" for clipboard', default=sys.stdout)
        args = parser.parse_args()

        # Check if the prompt is "-" and read from stdin if so
        if args.prompt == "-":
            prompt = sys.stdin.read().strip()
        else:
            prompt = args.prompt

        if args.output == 'clip' or args.output == 'clipboard':
            buffer = io.StringIO()
        else:
            buffer = sys.stdout

        query_chatgpt(prompt, model=args.model, complete=args.complete, system=args.system, output=buffer)

        if args.output == 'clip' or args.output == 'clipboard':
            pyperclip.copy(buffer.getvalue())

    except Exception as e:
        logger.error(f"Error", exc_info=e)
        raise Exception(f"Error: {e}")

if __name__ == "__main__":
    main()

    
