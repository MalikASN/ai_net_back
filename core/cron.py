import base64
import getpass
import io
import os
import numpy as np
import pydantic
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chat_models import init_chat_model
from langchain_google_vertexai.vision_models import VertexAIImageGeneratorChat
from PIL import Image
from langchain_core.messages import AIMessage, HumanMessage
from core.models import Post, PostImage
from data import agent_categories_with_subcategories
from django.core.files.base import ContentFile


agent_categories = [

    "Finance",
    "Education",
    "Entertainment",
    "Travel",
    "Sports",
    "Food",
    "Lifestyle",
    "Fashion",
    "Art",
    "Music",
    "Gaming",
    "Environment",
    "Politics",
    "Science",
    "History",
    "Culture",
    "Automotive"
]


agent_style = [
    "Generalist",
    "Professional",
    "Journalist",
    "Influencer"
]

def check_credentials():
     if not os.environ.get("GOOGLE_API_KEY"):
       os.environ["GOOGLE_API_KEY"] = "AIzaSyCBt72dSoc1PVJftmK6PKeTOnUt_YaCuq0"


class InitialPost(pydantic.BaseModel):
    title = pydantic.Field(description="the title of the post")
    text_content = pydantic.Field(description= "the post text content")

def post_std_agent_job():
    check_credentials()

    # Upload for 4 random agents
    agent_field_choices = [np.random.randint(0, len(agent_categories)) for _ in range(4)] 
    agent_fields = [agent_categories[el] for el in agent_field_choices]
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.8,       
    )
    generator = VertexAIImageGeneratorChat(
        number_of_results=3, 
        model_name="imagen-4.0-generate-001"
    )           
    
    for i in range(4):
        # Generate initial post
        parser = PydanticOutputParser(pydantic_object=InitialPost)
        
        # Prompt
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"You are an agent specialized in the {agent_fields[i]} field. \n{{format_instructions}}",
            ),
            ("human", "{query}"),
        ]).partial(format_instructions=parser.get_format_instructions())

        query = "Generate an attractive eye catching post about this using a generalist response style"
        chain = prompt | llm | parser
        result = chain.invoke({"query": query})

        # Randomly decide if post should be multimodal (50% chance)
        multimodal_post = np.random.randint(0, 2)
            
        if multimodal_post == 1:
            num_of_images_to_generate = np.random.randint(1, 4)
            messages = [HumanMessage(content=[f"Generate {str(num_of_images_to_generate)} images according to this provided post {str(result)}"])]
            
            try:
                response = generator.invoke(messages)
                # To view the generated Image
                generated_image = response.content[0]
                # Parse response object to get base64 string for image
                img_base64 = generated_image["image_url"]["url"].split(",")[-1]
                img_bytes = base64.b64decode(img_base64)
                # Convert base64 string to Image
                img = Image.open(io.BytesIO(base64.decodebytes(bytes(img_base64, "utf-8"))))

                # Create post first
                post = Post.objects.create(
                    title=result.title,
                    text_content=result.text_content,
                    category=agent_fields[i]
                )

                # Insert images in PostImages entity sql table
                # Note: You'll need to save the PIL Image to a file first
                # This is a placeholder for the actual image saving logic
                post_image = PostImage.objects.create(
                    post=post
                )
                image_name = f"post_{post.id}_img_{i}.png"

                post_image.image.save(image_name, ContentFile(img_bytes), save=True)
                
            except Exception as e:
                print(f"Error generating images: {e}")
                # Create text-only post if image generation fails
                post = Post.objects.create(
                    title=result.title,
                    text_content=result.text_content,
                    category=agent_fields[i]
                )
        else:
            # Directly insert post without images
            post = Post.objects.create(
                title=result.title,
                text_content=result.text_content,
                category=agent_fields[i]
            )

        print(f"Created post {i+1}: {result.title}")