# gpt4o.py
from openai import OpenAI
import base64
from PIL import Image
from io import BytesIO
import os
import json

class GPTFoodScanner:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def analyze_food_image(self, image_file):
        try:
            # Resize the image to 224x224
            image = Image.open(image_file)
            image = image.resize((224, 224))

            # Convert the image to base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # Construct a detailed prompt for OpenAI API
            prompt = (
                "Based on the image provided, estimate the below macros based on its appearance."
                "Return the response in JSON format with the following fields: "
                "'calories', 'protein_grams', 'carbs_grams', 'fat_grams', and 'food_name'. "
            )

            # Call OpenAI API using ChatCompletion to interpret the image
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You provide estimates of calories and macros."},
                    {"role": "user", "content": [
                      {
                        "type": 'text',
                        "text": ("Based on the image provided, estimate the below macros based on its appearance.\n"
                                "Return the response in JSON format with the following fields:\n"
                                "'calories', 'protein_grams', 'carbs_grams', 'fat_grams', and 'food_name'.\n"
                                "Only respond with the json, no leading text.")
                      },
                      {
                        "type": 'image_url',
                        'image_url': {
                          "url": f'data:image/png;base64,{image_base64}'
                        }
                      }
                    ]},
                ]
            )

            # Parse response and return result
            return self.parse_response(response)
        except Exception as e:
            raise RuntimeError(f"Failed to analyze the image: {str(e)}")

    def parse_response(self, response):
        # Check if the response has the correct structure and retrieve JSON
        try:
            message_content = response.choices[0].message.content
            cleaned_content = message_content.strip("```json").strip("```").strip()
            print(cleaned_content)
            parsed_content = json.loads(cleaned_content)
            print(parsed_content)
            return parsed_content

        except Exception as e:
            print(e)
            raise ValueError("Unexpected response format from OpenAI API.")
