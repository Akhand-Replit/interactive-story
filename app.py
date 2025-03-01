import streamlit as st
import requests
import json
import time
import random
from PIL import Image
import io
import base64
import pandas as pd
import streamlit_lottie as st_lottie

# Set page configuration
st.set_page_config(
    page_title="Interactive Story Adventure",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a clean, modern UI
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: 500;
    }
    .story-text {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .choice-button {
        margin-top: 10px;
    }
    h1, h2, h3 {
        color: #1E1E1E;
    }
    .footer {
        margin-top: 30px;
        text-align: center;
        color: #888888;
    }
</style>
""", unsafe_allow_html=True)

# Function to load Lottie animations
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Cache the Lottie animations
@st.cache_resource
def get_lotties():
    lotties = {
        "adventure": load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_bXmwcH6RUo.json"),
        "horror": load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_kcxosgub.json"),
        "romance": load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_khrclx93.json"),
        "fantasy": load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_hk63n9i9.json"),
        "mystery": load_lottieurl("https://assets7.lottiefiles.com/packages/lf20_rdkby0a0.json"),
        "sci_fi": load_lottieurl("https://assets7.lottiefiles.com/packages/lf20_xUSzvwkTmz.json"),
    }
    return lotties

# Function to generate story using Hugging Face API (Deepseek model)
def generate_story(prompt, api_key, model="deepseek-ai/deepseek-coder-33b-instruct"):
    API_URL = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()
        
        # Handle different response formats
        if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
            return result[0]["generated_text"]
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        elif isinstance(result, list) and len(result) > 0:
            return result[0]
        else:
            return "Error: Unexpected response format. Please try again."
    except Exception as e:
        return f"Error generating story: {str(e)}"

# Function to generate story choices
def generate_choices(current_scene, genre, api_key):
    prompt = f"""
    Given the following scene in a {genre} story:
    
    {current_scene}
    
    Generate two distinct and interesting choices for the protagonist. Each choice should lead the story in a different direction.
    Format your response as a JSON object with two choices like this:
    {{
        "choice1": "Brief description of first choice (10-15 words)",
        "choice2": "Brief description of second choice (10-15 words)"
    }}
    Only return the JSON, nothing else.
    """
    
    try:
        result = generate_story(prompt, api_key)
        # Extract JSON from the response
        json_str = result.strip()
        if not json_str.startswith('{'):
            # Find the first occurrence of '{'
            start_idx = json_str.find('{')
            if start_idx != -1:
                json_str = json_str[start_idx:]
        if not json_str.endswith('}'):
            # Find the last occurrence of '}'
            end_idx = json_str.rfind('}')
            if end_idx != -1:
                json_str = json_str[:end_idx+1]
        
        choices = json.loads(json_str)
        return choices
    except Exception as e:
        # Fallback to default choices if there's an error
        return {
            "choice1": "Continue cautiously and investigate further",
            "choice2": "Take a bold approach and face the situation head-on"
        }

# Function to generate next scene based on choice
def generate_next_scene(current_scene, chosen_choice, genre, api_key):
    prompt = f"""
    In this {genre} story:
    
    Current situation: {current_scene}
    
    The protagonist decides to: {chosen_choice}
    
    Continue the story with an engaging scene (150-200 words) based on this choice. Make it vivid and immersive.
    """
    
    result = generate_story(prompt, api_key)
    
    # Clean up the result to get just the new scene
    if current_scene in result:
        result = result.split(current_scene)[1]
    
    # Remove any trailing or leading whitespace
    result = result.strip()
    
    return result

# Function to create a downloadable story
def get_download_link(story_text, filename="my_adventure.txt"):
    """Generates a link to download the story text as a file"""
    b64 = base64.b64encode(story_text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">Download your adventure story</a>'
    return href

# Initialize session state variables
if "start_game" not in st.session_state:
    st.session_state.start_game = False
if "player_name" not in st.session_state:
    st.session_state.player_name = ""
if "genre" not in st.session_state:
    st.session_state.genre = ""
if "current_scene" not in st.session_state:
    st.session_state.current_scene = ""
if "story_log" not in st.session_state:
    st.session_state.story_log = []
if "choices" not in st.session_state:
    st.session_state.choices = {}
if "choice_count" not in st.session_state:
    st.session_state.choice_count = 0
if "game_over" not in st.session_state:
    st.session_state.game_over = False

# Main app logic
def main():
    lotties = get_lotties()
    
    # Title and introduction
    st.title("🔮 Interactive Story Adventure")
    
    # Sidebar for navigation and settings
    with st.sidebar:
        st.header("Game Settings")
        huggingface_api_key = st.text_input("Enter Hugging Face API Key", type="password")
        
        if st.button("Reset Game"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()
            
        st.markdown("---")
        st.markdown("### How to Play")
        st.markdown("""
        1. Enter your name and select a genre
        2. Read the story that unfolds
        3. Make choices to shape your adventure
        4. After 20 choices, your story will conclude
        5. Download your complete adventure!
        """)
    
    # Game start screen
    if not st.session_state.start_game:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.header("Welcome to your personalized adventure!")
            st.markdown("""
            This interactive story game uses AI to create a unique adventure just for you. 
            Your choices will shape the narrative and lead to different outcomes.
            
            To begin, enter your name and select a genre for your adventure.
            """)
            
            # Player name input
            player_name = st.text_input("Your Name", placeholder="Enter your name")
            
            # Genre selection
            genre_options = {
                "adventure": "Adventure 🏞️",
                "horror": "Horror 👻",
                "romance": "Romance ❤️",
                "fantasy": "Fantasy 🧙‍♂️",
                "mystery": "Mystery 🔍",
                "sci_fi": "Science Fiction 🚀"
            }
            
            selected_genre = st.selectbox("Choose your story genre", list(genre_options.values()))
            
            # Map the display name back to the key
            selected_genre_key = list(genre_options.keys())[list(genre_options.values()).index(selected_genre)]
            
            # Start game button
            if st.button("Start Your Adventure") and player_name and huggingface_api_key:
                st.session_state.player_name = player_name
                st.session_state.genre = selected_genre_key
                
                # Generate initial scene
                initial_prompt = f"""
                Create an engaging opening scene for a {selected_genre_key} story where the protagonist is named {player_name}.
                Set the scene (about 150 words) with an interesting situation that will lead to choices.
                Make it immersive and end at a point where the protagonist needs to make a decision.
                """
                
                with st.spinner("Creating your adventure..."):
                    initial_scene = generate_story(initial_prompt, huggingface_api_key)
                    st.session_state.current_scene = initial_scene
                    st.session_state.story_log.append(("narrator", initial_scene))
                    
                    # Generate initial choices
                    initial_choices = generate_choices(initial_scene, selected_genre_key, huggingface_api_key)
                    st.session_state.choices = initial_choices
                
                st.session_state.start_game = True
                st.experimental_rerun()
            
            elif not huggingface_api_key and st.button("Start Your Adventure"):
                st.error("Please enter your Hugging Face API key to start the game")
                
        with col2:
            # Display the Lottie animation for the selected genre
            if selected_genre_key in lotties and lotties[selected_genre_key]:
                st_lottie.st_lottie(lotties[selected_genre_key], key=f"lottie_{selected_genre_key}", height=300)
            else:
                st.image("https://via.placeholder.com/400x300?text=Interactive+Story+Adventure", use_column_width=True)
    
    # Game in progress
    elif st.session_state.start_game and not st.session_state.game_over:
        # Display current scene
        st.markdown(f"### {st.session_state.player_name}'s {st.session_state.genre.capitalize()} Adventure")
        
        # Progress bar
        progress = min(st.session_state.choice_count / 20, 1.0)
        st.progress(progress)
        st.markdown(f"Decision point: {st.session_state.choice_count}/20")
        
        # Display current scene
        st.markdown('<div class="story-text">', unsafe_allow_html=True)
        st.write(st.session_state.current_scene)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display choices
        st.markdown("### What will you do?")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(st.session_state.choices.get("choice1", "Option 1"), key="btn_choice1", help="Select this path for your story"):
                chosen_choice = st.session_state.choices["choice1"]
                st.session_state.story_log.append(("player", chosen_choice))
                
                with st.spinner("Continuing your adventure..."):
                    # Generate next scene
                    next_scene = generate_next_scene(
                        st.session_state.current_scene,
                        chosen_choice,
                        st.session_state.genre,
                        huggingface_api_key
                    )
                    
                    # Update game state
                    st.session_state.current_scene = next_scene
                    st.session_state.story_log.append(("narrator", next_scene))
                    st.session_state.choice_count += 1
                    
                    # Check if game should end
                    if st.session_state.choice_count >= 20:
                        st.session_state.game_over = True
                    else:
                        # Generate new choices
                        new_choices = generate_choices(next_scene, st.session_state.genre, huggingface_api_key)
                        st.session_state.choices = new_choices
                
                st.experimental_rerun()
                
        with col2:
            if st.button(st.session_state.choices.get("choice2", "Option 2"), key="btn_choice2", help="Select this path for your story"):
                chosen_choice = st.session_state.choices["choice2"]
                st.session_state.story_log.append(("player", chosen_choice))
                
                with st.spinner("Continuing your adventure..."):
                    # Generate next scene
                    next_scene = generate_next_scene(
                        st.session_state.current_scene,
                        chosen_choice,
                        st.session_state.genre,
                        huggingface_api_key
                    )
                    
                    # Update game state
                    st.session_state.current_scene = next_scene
                    st.session_state.story_log.append(("narrator", next_scene))
                    st.session_state.choice_count += 1
                    
                    # Check if game should end
                    if st.session_state.choice_count >= 20:
                        st.session_state.game_over = True
                    else:
                        # Generate new choices
                        new_choices = generate_choices(next_scene, st.session_state.genre, huggingface_api_key)
                        st.session_state.choices = new_choices
                
                st.experimental_rerun()
    
    # Game over screen
    elif st.session_state.game_over:
        st.header("🎉 Your Adventure is Complete!")
        
        # Generate conclusion
        if "conclusion" not in st.session_state:
            conclusion_prompt = f"""
            Write a satisfying conclusion (about 200 words) to this {st.session_state.genre} story:
            
            {st.session_state.current_scene}
            
            Make it feel like a natural ending that wraps up the adventure for {st.session_state.player_name}.
            """
            
            with st.spinner("Generating the conclusion to your adventure..."):
                conclusion = generate_story(conclusion_prompt, huggingface_api_key)
                st.session_state.conclusion = conclusion
                st.session_state.story_log.append(("narrator", conclusion))
        
        # Display conclusion
        st.markdown('<div class="story-text">', unsafe_allow_html=True)
        st.write(st.session_state.conclusion)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Compile full story
        full_story = f"# {st.session_state.player_name}'s {st.session_state.genre.capitalize()} Adventure\n\n"
        
        for role, text in st.session_state.story_log:
            if role == "player":
                full_story += f"\n**{st.session_state.player_name} chose:** {text}\n\n"
            else:
                full_story += f"{text}\n\n"
        
        # Create download button for the story
        st.markdown("### Download Your Complete Adventure")
        st.markdown(get_download_link(full_story, f"{st.session_state.player_name}_{st.session_state.genre}_adventure.txt"), unsafe_allow_html=True)
        
        # Option to play again
        if st.button("Play Again with a New Story"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()
    
    # Footer
    st.markdown("""
    <div class="footer">
        Powered by Streamlit and Hugging Face AI
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
