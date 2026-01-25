import google.generativeai as genai
import os

# ==========================================
# PASTE YOUR API KEY HERE
# ==========================================
API_KEY = "AIzaSyDv3tM5GnlFoKCqmxCBHUYOLpeeq2JQlkI"
# ==========================================

def test_api_key():
    Test the Model API key by asking for the capital of India.
    print("--- Model API Key Test ---")
    
    if API_KEY == "YOUR_API_KEY_HERE" or not API_KEY:
        print("❌ Error: Please paste your Model API key in the 'API_KEY' variable within this file.")
        return

    try:
        # Configure the Model SDK
        print(f"Configuring Model SDK...")
        genai.configure(api_key=API_KEY)

        # Initialize the model (using model-1.5-flash for quick test)
        model_name = 'gemini-2.1-flash'
        print(f"Initializing model: {model_name}...")
        model = genai.GenerativeModel(model_name)

        # Define the question
        prompt = "What is the capital of India?"
        print(f"Sending prompt: '{prompt}'")
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Print output
        print("\n" + "="*30)
        print("RESPONSE FROM MODEL:")
        print("="*30)
        print(response.text.strip())
        print("="*30)
        
        print("\n✅ API Key is WORKING correctly!")

    except Exception as e:
        print("\n❌ API Key Test FAILED!")
        print(f"Error Details: {str(e)}")
        
        if "API_KEY_INVALID" in str(e):
            print("Hint: The API key you provided is invalid.")
        elif "quota" in str(e).lower() or "429" in str(e):
            print("Hint: You have exceeded your API quota.")
        elif "not found" in str(e).lower():
            print(f"Hint: The model '{model_name}' might not be available for this key or region.")

if __name__ == "__main__":
    test_api_key()
