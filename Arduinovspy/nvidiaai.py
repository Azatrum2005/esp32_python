from openai import OpenAI

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)

while(True):
  s=input("\n\nEnter your prompt:")
  if s=="end convo":
    break
  else:
    completion = client.chat.completions.create(
    model="nvidia/llama-3.1-nemotron-70b-instruct",
    messages=[{"role":"user","content":s}],
    temperature=0.5,
    top_p=1,
    max_tokens=4096,
    stream=True
    )
    reply=""
    for text in completion:
      if text.choices[0].delta.content is not None:
        print(text.choices[0].delta.content, end="")
        # reply=reply+text.choices[0].delta.content
    # print(reply, end="")

# def get_user_input():
#   while True:
#     user_input = input("\n\nEnter your prompt: ")
#     if user_input.lower() == "end convo":
#       break
#     else:
#       yield user_input

# def generate_completion(prompt):
#   completion = client.chat.completions.create(
#     model="nvidia/llama-3.1-nemotron-70b-instruct",
#     messages=[{"role":"user","content":prompt}],
#     temperature=0.5,
#     top_p=1,
#     max_tokens=4096,
#     stream=True
#   )
#   return completion

# def print_completion(completion):
#   for text in completion:
#     if text.choices[0].delta.content is not None:
#       print(text.choices[0].delta.content, end="")

# def main():
#   for user_input in get_user_input():
#     completion = generate_completion(user_input)
#     print_completion(completion)

# if __name__ == "__main__":
#   main()

