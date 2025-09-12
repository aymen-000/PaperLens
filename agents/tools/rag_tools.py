import base64
from IPython.display import HTML, display
import re
from langchain_core.messages import HumanMessage
from agents.prompts.agents_prompts import PAPER_RAG_AGENT
from langchain_google_genai import ChatGoogleGenerativeAI 
from PIL import Image

def encode_image(image_path):
   """Getting the base64 string"""
   with open(image_path, "rb") as image_file:
       return base64.b64encode(image_file.read()).decode("utf-8")

        
def img_prompt_func(data_dict):
    """
    Join the context into a single string
    """
    formatted_texts = "\n".join(data_dict["context"]["texts"])
    messages = [
        {
            "type": "text",
            "text": (
                "You are financial analyst tasking with providing investment advice.\n"
                "You will be given a mix of text, tables, and image(s) usually of charts or graphs.\n"
                "Use this information to provide investment advice related to the user's question. \n"
                f"User-provided question: {data_dict['question']}\n\n"
                "Text and / or tables:\n"
                f"{formatted_texts}"
            ),
        }
    ]

    # Adding image(s) to the messages if present
    if data_dict["context"]["images"]:
        for image in data_dict["context"]["images"]:
            messages.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                }
            )
    return [HumanMessage(content=messages)]






llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

def get_image_base64(filename: str) -> str:
    with open(filename, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

# Load multiple images
image_paths = [
    "./storage/processed/images/page1_img1.png",
    "./storage/processed/images/page1_img2.png",
    "./storage/processed/images/page1_img3.png",
]
images_b64 = [get_image_base64(p) for p in image_paths]

# Build the message
message = HumanMessage(
    content=[
        {"type": "text", "text": "Compare these images and provide detailed descriptions."},
        *[
            {"type": "image_url", "image_url": {"url": img}}
            for img in images_b64
        ],
    ]
)

# Send to model
response = llm.invoke([message])
print(response.content)


    
    

    
    