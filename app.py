import os , json
import re , io , random
import pandas as pd
import time , requests
from PIL import Image
from typing import Optional, Dict, List
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from datetime import datetime
from flask import Flask ,jsonify ,request
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


class ContentCreationBot:
    def __init__(self, file_path="sample code/data/processed_posts.json"):
        # Initialize API keys and FAISS index path
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.huggingface_token = os.getenv('HUGGINGFACE_API_TOKEN')
        self.langchain_api_key = os.getenv('LANGCHAIN_API_KEY')
        self.faiss_index_path = 'faiss_index' 
        self.image_folder = 'generated_images'
        self.df = None
        self.unique_tags = None
        os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
        os.environ['LANGCHAIN_API_KEY']=os.getenv('LANGCHAIN_API_KEY')
        os.environ['LANGCHAIN_PROJECT']=os.getenv('LANGCHAIN_PROJECT')
        os.environ['LANGCHAIN_TRACING_V2'] = 'true'

        self.load_posts(file_path)
        # Initialize models and embeddings
        self.model = ChatOpenAI(temperature=0.7)

    
    def load_posts(self, file_path):
        with open(file_path, encoding="utf-8") as f:
            posts = json.load(f)
            self.df = pd.json_normalize(posts)
            self.df['length'] = self.df['line_count'].apply(self.categorize_length)
            # collect unique tags
            all_tags = self.df['tags'].apply(lambda x: x).sum()
            self.unique_tags = list(set(all_tags))

    def categorize_length(self, line_count):
        if line_count < 5:
            return "Short"
        elif 5 <= line_count <= 10:
            return "Medium"
        else:
            return "Long"

    def get_tags(self):
        return self.unique_tags
    
    def get_filtered_posts(self):
        df_filtered = self.df
        return df_filtered.to_dict(orient='records')
    
    def get_length_str(self,length):
        if length == "Short":
            return "1 to 5 lines"
        if length == "Medium":
            return "6 to 10 lines"
        if length == "Long":
            return "11 to 15 lines"


    def get_caption(self, customizations:dict=None):

        tag = random.choice(self.get_tags())
        length = random.choice(['small','medium','large'])
        length_str = self.get_length_str(length)
        prompt = f"""
        Generate a professional LinkedIn post for a healthcare company called 'Emend Healthcare'. 

        1) Length: {length_str}
        2) Audience: Healthcare professionals, patients, and families looking for rehabilitation services.
        3) Focus: Highlight Emend Healthcare's services, including compassionate care, personalized recovery plans, and innovative approaches to rehabilitation.
        4) Include a professional tone, engaging call-to-action, and 3-5 relevant hashtags such as #Rehabilitation, #HealthcareInnovation, and #RecoveryJourney at the end of the post, without the word "hashtag" preceding them.

        The script for the generated post should always be in English.
        """

        examples = self.get_filtered_posts()

        if len(examples) > 0:
            prompt += "\n\nUse the writing style of the following examples:"

            for i, post in enumerate(examples):
                post_text = post['text']
                prompt += f'\n\nExample {i+1}: {post_text}'

                if i == 1:  # Use max two samples
                    break

        if customizations:
            prompt += "\n\nScript must be in according to the following Special customizations:"
            for k ,v in customizations.items():
                prompt += f'\n{k}  : {v}'

        # Generate content
        social_output = self.model.invoke(prompt)
        # print(social_output.content)
        return social_output.content




    def generate_image(self, prompt: str, max_retries: int = 3) -> Optional[bytes]:
        IMG_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
        headers = {"Authorization": f"Bearer {self.huggingface_token}"}
        default_background_color = "#F0F8FF"
        default_text_color = "#2C3E50"

        # Default template settings inspired by the provided newsletter
        default_prompt = """
        Design a serene, professional healthcare-themed image for a rehab company called "Emend Healthcare."
        Features:
        - Text Placement: Leave space for text near the center but avoid adding any text, logos, or other graphic elements.
        - Color Palette: Use soothing natural tones, emphasizing blues, greens, and soft sunlight reflections on water.
        - Focus: Minimalistic and clean design to evoke a sense of peace, recovery, and new beginnings.
        - Text: Do not use any Text.
        """

        # Merge optional prompt with the default template
        if prompt:
            full_prompt = default_prompt + f"\n\n-Additional Features:\nScene: {prompt}"
        else:
            full_prompt = default_prompt + f"\n- Scene: A calm lake surrounded by mountains under a clear sky. A red kayak is visible in the foreground, pointing toward the horizon, symbolizing a journey."

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "num_inference_steps": 75,
                "guidance_scale": 8.5,
                "width": 1024,
                "height": 768,
            },
        }


        for attempt in range(max_retries):
            try:
                response = requests.post(IMG_URL, headers=headers, json=payload)
                
                if response.status_code == 200:
                    return response.content
                
                if response.status_code == 500:
                    print(f"Internal Server Error: {response.text}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in 10 seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(10)
                        continue
                    else:
                        print("Max retries reached. Could not generate image.")
                        return None

                print(f"Error: {response.status_code}, {response.text}")
                return None
                    
            except Exception as e:
                print(f"Error occurred: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(10)
                    continue
                return None


    def save_image(self, image_bytes: Optional[bytes]) -> Optional[Image.Image]:
        """Save the generated image with the timestamp as the filename"""
        if image_bytes is None:
            return None        
        try:
            # Ensure the folder exists
            if not os.path.exists(self.image_folder):
                os.makedirs(self.image_folder)
            
            # Get the current timestamp for the filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Combine timestamp and sanitized caption for the filename
            company_name = "Emend Healthcare"
            filename = f"{timestamp}_{company_name.replace(' ', '_')}.png"
            file_path = os.path.join(self.image_folder, filename)
            
            # Save the image
            image = Image.open(io.BytesIO(image_bytes))
            image.save(file_path)
            print(f"Image saved to {file_path}")
            return image
        except Exception as e:
            raise (f"Error saving image: {str(e)}")

        
    # Function to generate email content based on extracted text and customizations
    def generate_email(self, customizations: dict =None):

        # Define the prompt template for email generation
        email_prompt_template = """
        You are tasked with generating a compassionate and engaging email marketing campaign for "Emend HealthCare", a rehab company that specializes in helping individuals overcome addiction and rebuild their lives. The user can provide additional customization details through a dictionary, such as tone, target audience, subject line, and other relevant elements. Use the provided details to craft an email that resonates with individuals seeking recovery and healing.

        Additional Customizations (provided by the user in a dictionary format):
        {customizations}

        Instructions:
        - Ensure the email has a compassionate and supportive tone that resonates with those seeking help and their families.
        - The subject line should encourage hope, renewal, and the possibility of a fresh start.
        - Emphasize the life-changing impact of rehabilitation and the personalized care provided by "Emend Solutions."
        - Craft strong calls to action (CTA) that drive individuals to inquire about services or schedule a consultation.
        - Tailor the content to build trust and highlight the expertise and success stories of "Emend Solutions."
        - Customize any other content based on the provided dictionary values, such as testimonials, recovery success rates, or available treatment programs.

        Email content:
        """

        # Create the prompt template for LangChain
        prompt_template = PromptTemplate(input_variables=["text", "customizations"], template=email_prompt_template)

        # Create the LLMChain with the model
        llm_chain = LLMChain(prompt=prompt_template, llm=self.model)

        # Default customizations if none are provided
        if customizations is None:
            customizations = {
                "subject_line": "Take the First Step Toward a New Beginning with Emend Solutions",
                "tone": "supportive and empathetic",
                "target_audience": "individuals struggling with addiction, their families, and those seeking a fresh start",
                "call_to_action": "Contact us today to learn more about how we can help you heal.",
                "additional_elements": "Include a success story or testimonial from a past client who has successfully completed the program."
            }

        # Generate the email content using LangChain
        email_content = llm_chain.run({"customizations": str(customizations)})

        return email_content


app = Flask(__name__)
content_creation_bot = ContentCreationBot()

@app.route("/generate_caption", methods=["POST"])
def generate_caption():
    try:
        customizations = request.get_json() or {}
        caption = content_creation_bot.get_caption(customizations)
        return jsonify({"caption": caption}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/generate_email", methods=["POST"])
def generate_email():
    try:
        customizations = request.get_json() or {}
        email_content = content_creation_bot.generate_email(customizations)
        return jsonify({"email_content": email_content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/generate_image", methods=["POST"])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        image_bytes = content_creation_bot.generate_image(prompt)
        if image_bytes:
            file_path = content_creation_bot.save_image(image_bytes)
            return jsonify({"message": "Image generated successfully"}), 200
        return jsonify({"error": "Image generation failed"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
