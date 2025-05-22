import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file (if you have one)
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    api_key = input("Please enter your OpenAI API key: ")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def encode_image(image_path):
    """Encode image to base64 for API submission"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_maps(map_folder):
    """Analyze map images to identify the city"""
    
    # Improved prompt for better city identification
    prompt = """
    You are a map and geography expert with extensive knowledge of European cities and their layouts. 
    
    Task: Analyze these four map fragments meticulously and determine which city they depict. Note that one fragment may be from a different city than the others.
    
    For each map fragment, provide a detailed analysis:
    
    1. STREET NAMES: Identify ALL visible street names, paying special attention to their language, spelling patterns, and naming conventions which can indicate the country/region.
    
    2. LANDMARKS & POINTS OF INTEREST: Identify ALL visible:
       - Churches, synagogues, mosques or religious buildings
       - Parks, gardens, squares, plazas
       - Schools, universities, hospitals
       - Cemeteries, monuments
       - Shopping centers, markets
       - Government buildings
       - Transportation hubs (train stations, tram stops, metro)
    
    3. URBAN LAYOUT ANALYSIS:
       - Street pattern (grid system, radial, medieval irregular, etc.)
       - Building blocks shape and density
       - Any distinctive neighborhood layouts
       - Presence of waterways, canals, rivers and their shape/pattern
    
    4. GEOGRAPHICAL FEATURES:
       - Hills, elevation changes
       - Coastlines, rivers, lakes
       - Green spaces and their distribution
    
    After analyzing all fragments, answer these questions:
    
    1. What city do most of the fragments depict? Provide a confidence percentage.
    
    2. Which specific fragment (if any) appears to be from a different city? Why?
    
    3. What specific evidence supports your city identification? List at least 5 concrete pieces of evidence.
    
    4. VERIFICATION: For the main city you've identified, find at least 3 specific locations visible in the fragments that you can verify exist in this city (specific street intersections, landmarks, etc.)
    
    5. LANGUAGE CLUES: What language are the street names in? How does this support your conclusion?
    
    BE EXTREMELY SPECIFIC in your analysis. Don't just say "the streets look European" - identify specific streets, landmarks, and patterns. Focus on concrete details rather than general impressions.

    The City is not either of these: Wroclaw, Warszaw, Krakow, Lodz, Poznan, Gdansk, Szczecin, Torun, Bydgoszcz
    """
    
    # Get map file paths
    map_files = [os.path.join(map_folder, f) for f in os.listdir(map_folder) if f.endswith('.png')]
    
    if not map_files:
        print("No map images found in the specified folder.")
        return
    
    # Prepare content for API call
    content = [
        {"type": "text", "text": prompt}
    ]
    
    # Add each map image to the content
    for i, map_file in enumerate(map_files, 1):
        try:
            base64_image = encode_image(map_file)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                        "detail": "high"
                    }
                }
            )
            print(f"Added map {i}: {os.path.basename(map_file)}")
        except Exception as e:
            print(f"Error processing map {i}: {e}")
    
    # Call the OpenAI API
    try:
        print("Sending request to OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=3000  # Increased token limit for more detailed analysis
        )
        
        # Extract and print the response
        result = response.choices[0].message.content
        print("\n" + "="*50)
        print("ANALYSIS RESULT:")
        print("="*50)
        print(result)
        
        # Save result to file
        with open("map_analysis_result.txt", "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\nResult saved to map_analysis_result.txt")
        
        return result
        
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

if __name__ == "__main__":
    # Path to the maps folder
    maps_folder = os.path.join("exrcises", "maps")
    
    # Check if the folder exists
    if not os.path.exists(maps_folder):
        print(f"Maps folder not found at {maps_folder}")
        maps_folder = input("Please enter the path to the maps folder: ")
    
    # Analyze the maps
    analyze_maps(maps_folder) 