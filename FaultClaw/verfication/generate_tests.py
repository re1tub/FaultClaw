import os
from openai import OpenAI  # Replace `some_library` with the actual library name

# Fetch the API key from environment variables
api_key = os.getenv("NVIDIA_API_KEY")

if not api_key:
    raise ValueError("API key not found. Please set the NVIDIA_API_KEY environment variable.")

# Initialize the API client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key
)

print("Client created")

try:
    # Make the API call
    completion = openai.ChatCompletion.create(
        model="nvidia/nemotron-3-super-120b-a12b",
        messages=[
            {
                "role": "user",
                "content": "Return ONLY a Python list of 10 random 4-bit tuples in this exact format: [(1,2), (3,4)]"
            }
        ],
        temperature=0.7,
        max_tokens=300
    )

    print("Request completed")

    # Print the response content
    print(completion.choices[0].message.content)

except Exception as e:
    # Handle any errors
    print(f"An error occurred: {e}")
