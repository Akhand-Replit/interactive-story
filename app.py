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
    page_title="ইন্টারেক্টিভ গল্প অ্যাডভেঞ্চার",  # Interactive Story Adventure in Bengali
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

# Function to generate story using Gemini API
def generate_story(prompt, model="gemini-1.5-flash"):
    try:
        # Get API key from Streamlit secrets
        api_key = st.secrets["gemini"]["api_key"]
        
        # Set up the API endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        # Modify prompt to request Bengali language
        bengali_prompt = f"Please respond in Bengali (Bangla) language only: {prompt}"
        
        # Prepare the request payload
        payload = {
            "contents": [{
                "parts": [{"text": bengali_prompt}]
            }]
        }
        
        # Set headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if request was successful
        if response.status_code != 200:
            raise Exception(f"API request failed with status code: {response.status_code}, response: {response.text}")
        
        # Parse the response
        result = response.json()
        
        # Extract the generated text
        if (result and "candidates" in result and len(result["candidates"]) > 0 and
                "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"] and
                len(result["candidates"][0]["content"]["parts"]) > 0):
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise Exception("Unexpected response structure from Gemini API")
            
    except Exception as e:
        st.error(f"Error generating story: {str(e)}")
        return f"Error generating story. Please check your API configuration. Error: {str(e)}"

# Function to generate story choices
def generate_choices(current_scene, genre):
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
    Write the choices in Bengali (Bangla) language.
    """
    
    try:
        result = generate_story(prompt)
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
        st.warning(f"Error generating choices: {str(e)}. Using fallback choices.")
        # Fallback to default choices if there's an error
        return {
            "choice1": "সাবধানে অগ্রসর হন এবং আরও অনুসন্ধান করুন",  # Continue cautiously and investigate further in Bengali
            "choice2": "একটি সাহসী পদ্ধতি নিন এবং পরিস্থিতির মুখোমুখি হন"  # Take a bold approach and face the situation head-on in Bengali
        }

# Function to generate next scene based on choice
def generate_next_scene(current_scene, chosen_choice, genre):
    prompt = f"""
    In this {genre} story:
    
    Current situation: {current_scene}
    
    The protagonist decides to: {chosen_choice}
    
    Continue the story with an engaging scene (150-200 words) based on this choice. Make it vivid and immersive.
    Write this in Bengali (Bangla) language only.
    """
    
    result = generate_story(prompt)
    
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
    st.title("🔮 ইন্টারেক্টিভ গল্প অ্যাডভেঞ্চার")  # Interactive Story Adventure in Bengali
    
    # Sidebar for navigation and settings
    with st.sidebar:
        st.header("গেম সেটিংস")  # Game Settings in Bengali
        
        if st.button("গেম রিসেট করুন"):  # Reset Game in Bengali
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            
        st.markdown("---")
        st.markdown("### কিভাবে খেলবেন")  # How to Play in Bengali
        st.markdown("""
        1. আপনার নাম দিন এবং একটি গল্পের ধরন বাছাই করুন
        2. গল্পটি পড়ুন যা উন্মোচিত হচ্ছে
        3. আপনার অ্যাডভেঞ্চার আকার দেওয়ার জন্য পছন্দ করুন
        4. 20টি পছন্দের পরে, আপনার গল্প শেষ হবে
        5. আপনার সম্পূর্ণ অ্যাডভেঞ্চার ডাউনলোড করুন!
        """)
    
    # Game start screen
    if not st.session_state.start_game:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.header("আপনার ব্যক্তিগতকৃত অ্যাডভেঞ্চারে স্বাগতম!")  # Welcome to your personalized adventure in Bengali
            st.markdown("""
            এই ইন্টারেক্টিভ গল্প গেমটি আপনার জন্য একটি অনন্য অ্যাডভেঞ্চার তৈরি করতে AI ব্যবহার করে।
            আপনার পছন্দগুলি গল্পের গতিপথ আকার দেবে এবং বিভিন্ন ফলাফলে পৌঁছাবে।
            
            শুরু করতে, আপনার নাম লিখুন এবং আপনার অ্যাডভেঞ্চারের জন্য একটি ধরন নির্বাচন করুন।
            """)
            
            # Player name input
            player_name = st.text_input("আপনার নাম", placeholder="আপনার নাম লিখুন")  # Your Name in Bengali
            
            # Genre selection
            genre_options = {
                "adventure": "অ্যাডভেঞ্চার 🏞️",  # Adventure in Bengali
                "horror": "হরর 👻",  # Horror in Bengali
                "romance": "রোমান্স ❤️",  # Romance in Bengali
                "fantasy": "ফ্যান্টাসি 🧙‍♂️",  # Fantasy in Bengali
                "mystery": "মিস্টেরি 🔍",  # Mystery in Bengali
                "sci_fi": "সায়েন্স ফিকশন 🚀"  # Science Fiction in Bengali
            }
            
            selected_genre = st.selectbox("আপনার গল্পের ধরন বাছাই করুন", list(genre_options.values()))  # Choose your story genre in Bengali
            
            # Map the display name back to the key
            selected_genre_key = list(genre_options.keys())[list(genre_options.values()).index(selected_genre)]
            
            # Start game button
            if st.button("আপনার অ্যাডভেঞ্চার শুরু করুন") and player_name:  # Start Your Adventure in Bengali
                st.session_state.player_name = player_name
                st.session_state.genre = selected_genre_key
                
                # Generate initial scene
                initial_prompt = f"""
                Create an engaging opening scene for a {selected_genre_key} story where the protagonist is named {player_name}.
                Set the scene (about 150 words) with an interesting situation that will lead to choices.
                Make it immersive and end at a point where the protagonist needs to make a decision.
                Write this in Bengali (Bangla) language only.
                """
                
                try:
                    with st.spinner("আপনার অ্যাডভেঞ্চার তৈরি করা হচ্ছে..."):  # Creating your adventure in Bengali
                        initial_scene = generate_story(initial_prompt)
                        st.session_state.current_scene = initial_scene
                        st.session_state.story_log.append(("narrator", initial_scene))
                        
                        # Generate initial choices
                        initial_choices = generate_choices(initial_scene, selected_genre_key)
                        st.session_state.choices = initial_choices
                    
                    st.session_state.start_game = True
                    st.rerun()
                except Exception as e:
                    st.error(f"গেম শুরু করতে ত্রুটি: {str(e)}। অনুগ্রহ করে দেখুন Gemini API কী সঠিকভাবে সেট করা আছে কিনা।")  # Error message in Bengali
            
        with col2:
            # Display the Lottie animation for the selected genre
            if selected_genre_key in lotties and lotties[selected_genre_key]:
                st_lottie.st_lottie(lotties[selected_genre_key], key=f"lottie_{selected_genre_key}", height=300)
            else:
                st.image("https://via.placeholder.com/400x300?text=Interactive+Story+Adventure", use_container_width=True)
    
    # Game in progress
    elif st.session_state.start_game and not st.session_state.game_over:
        # Display current scene
        st.markdown(f"### {st.session_state.player_name}'s {st.session_state.genre.capitalize()} অ্যাডভেঞ্চার")  # Adventure in Bengali
        
        # Progress bar
        progress = min(st.session_state.choice_count / 20, 1.0)
        st.progress(progress)
        st.markdown(f"সিদ্ধান্তের পয়েন্ট: {st.session_state.choice_count}/20")  # Decision point in Bengali
        
        # Display current scene
        st.markdown('<div class="story-text">', unsafe_allow_html=True)
        st.write(st.session_state.current_scene)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display choices
        st.markdown("### আপনি কি করবেন?")  # What will you do? in Bengali
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(st.session_state.choices.get("choice1", "Option 1"), key="btn_choice1", help="Select this path for your story"):
                chosen_choice = st.session_state.choices["choice1"]
                st.session_state.story_log.append(("player", chosen_choice))
                
                with st.spinner("আপনার অ্যাডভেঞ্চার চালিয়ে যাওয়া হচ্ছে..."):  # Continuing your adventure in Bengali
                    # Generate next scene
                    next_scene = generate_next_scene(
                        st.session_state.current_scene,
                        chosen_choice,
                        st.session_state.genre
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
                        new_choices = generate_choices(next_scene, st.session_state.genre)
                        st.session_state.choices = new_choices
                
                st.rerun()
                
        with col2:
            if st.button(st.session_state.choices.get("choice2", "Option 2"), key="btn_choice2", help="Select this path for your story"):
                chosen_choice = st.session_state.choices["choice2"]
                st.session_state.story_log.append(("player", chosen_choice))
                
                with st.spinner("Continuing your adventure..."):
                    # Generate next scene
                    next_scene = generate_next_scene(
                        st.session_state.current_scene,
                        chosen_choice,
                        st.session_state.genre
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
                        new_choices = generate_choices(next_scene, st.session_state.genre)
                        st.session_state.choices = new_choices
                
                st.rerun()
    
    # Game over screen
    elif st.session_state.game_over:
        st.header("🎉 আপনার অ্যাডভেঞ্চার সম্পূর্ণ হয়েছে!")  # Your Adventure is Complete! in Bengali
        
        # Generate conclusion
        if "conclusion" not in st.session_state:
            conclusion_prompt = f"""
            Write a satisfying conclusion (about 200 words) to this {st.session_state.genre} story:
            
            {st.session_state.current_scene}
            
            Make it feel like a natural ending that wraps up the adventure for {st.session_state.player_name}.
            Write this in Bengali (Bangla) language only.
            """
            
            with st.spinner("আপনার অ্যাডভেঞ্চারের সমাপ্তি তৈরি করা হচ্ছে..."):  # Generating the conclusion to your adventure in Bengali
                conclusion = generate_story(conclusion_prompt)
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
        st.markdown("### আপনার সম্পূর্ণ অ্যাডভেঞ্চার ডাউনলোড করুন")  # Download Your Complete Adventure in Bengali
        st.markdown(get_download_link(full_story, f"{st.session_state.player_name}_{st.session_state.genre}_adventure.txt"), unsafe_allow_html=True)
        
        # Option to play again
        if st.button("নতুন গল্প দিয়ে আবার খেলুন"):  # Play Again with a New Story in Bengali
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Footer
    st.markdown("""
    <div class="footer">
        স্ট্রিমলিট এবং Google Gemini AI দ্বারা পরিচালিত
    </div>
    """, unsafe_allow_html=True)  # Powered by Streamlit and Google Gemini AI in Bengali

if __name__ == "__main__":
    main()
