# Content Creation APIs Documentation

## Overview
This document provides detailed information about the Content Creation APIs offered by the application. These APIs are designed to generate captions, emails, and images tailored for professional healthcare marketing purposes, particularly for a company like Emend Healthcare.

## API Endpoints

### 1. Generate Caption
**Endpoint:** `/generate_caption`  
**Method:** `POST`

#### Description
Generates a professional LinkedIn caption for healthcare-related posts.

#### Request Body
- **Optional Elements:**
  - `customizations`: A dictionary containing specific preferences for the generated caption, such as tone, audience, and specific hashtags.

#### Response Body
- `caption` (string): The generated caption.

#### Example Request
```json
{
  "customizations": {
    "tone": "professional",
    "audience": "patients and healthcare providers",
    "hashtags": ["#Healthcare", "#Recovery"]
  }
}
```

#### Example Response
```json
{
  "caption": "Emend Healthcare is here to guide you on your recovery journey with personalized care and innovative rehabilitation solutions. #Healthcare #Recovery"
}
```

---

### 2. Generate Email
**Endpoint:** `/generate_email`  
**Method:** `POST`

#### Description
Generates a compassionate and engaging email for marketing campaigns aimed at individuals and families seeking rehabilitation services.

#### Request Body
- **Optional Elements:**
  - `customizations`: A dictionary specifying preferences for the email, such as tone, subject line, and additional elements like testimonials or CTAs.

#### Response Body
- `email_content` (string): The generated email content.

#### Example Request
```json
{
  "customizations": {
    "subject_line": "Your Path to Recovery Starts Here",
    "tone": "supportive",
    "call_to_action": "Contact us today to learn more!"
  }
}
```

#### Example Response
```json
{
  "email_content": "Subject: Your Path to Recovery Starts Here\n\nDear [Name],\n\nAt Emend Healthcare, we specialize in personalized care that empowers you to rebuild your life. Contact us today to start your journey to recovery."
}
```

---

### 3. Generate Image
**Endpoint:** `/generate_image`  
**Method:** `POST`

#### Description
Generates a serene, professional healthcare-themed image based on the provided prompt.

#### Request Body
- **Optional Elements:**
  - `prompt` (string): A description of the scene or elements to include in the image.

#### Response Body
- `message` (string): Confirmation of successful image generation.
- **Or**
- `error` (string): Error message if image generation fails.

#### Example Request
```json
{
  "prompt": "A calm lake surrounded by mountains under a clear sky"
}
```

#### Example Response
```json
{
  "message": "Image generated successfully"
}
```

## Error Handling
All endpoints return a standard error message in case of failures.

#### Example Error Response
```json
{
  "error": "Invalid input provided"
}
```

## Notes
- Ensure proper authentication by setting environment variables for API keys.
- The application uses OpenAI, Hugging Face, and LangChain models to generate content.
- Generated images are saved in the `generated_images` folder with a timestamped filename.
