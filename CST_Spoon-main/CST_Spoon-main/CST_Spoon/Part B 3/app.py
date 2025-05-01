import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from diet_planner import calculate_bmr, calculate_daily_calories, generate_diet_plan
import base64
from io import BytesIO
import os

# Set page config
st.set_page_config(
    page_title="Indian Vegetarian Diet & Fitness Planner",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for accessibility and patient-friendly UI
st.markdown("""
    <style>
    .main {
        background-color: #0E1117;
        color: #FAFAFA;
        font-size: 18px;
    }
    .css-1d391kg {
        background-color: #0E1117;
    }
    .st-bq, .st-c0, .st-c1, .st-c2, .st-c3, .st-c4 {
        background-color: #1E2128;
    }
    .stTabs [data-baseweb="tab-panel"], .stTabs [data-baseweb="tab-list"] {
        background-color: #0E1117;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E2128;
        color: white;
        border-radius: 4px 4px 0px 0px;
        padding: 0.5rem 1rem;
        font-size: 16px;
    }
    .stTabs [data-baseweb="tab"]:focus {
        background-color: #3B4357;
    }
    div.stButton > button {
        background-color: #3B4357;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        font-size: 16px;
    }
    div.stButton > button:hover {
        background-color: #4B5675;
    }
    .stMetric {
        background-color: #1E2128;
        padding: 1rem;
        border-radius: 5px;
        font-size: 16px;
    }
    .stMetric label {
        color: #8C94A6;
    }
    .stTable, table {
        background-color: #1E2128;
        color: white;
        font-size: 16px;
    }
    thead tr th {
        background-color: #3B4357;
    }
    tbody tr:nth-child(odd) {
        background-color: #1E2128;
    }
    tbody tr:nth-child(even) {
        background-color: #262B36;
    }
    .streamlit-expanderHeader, .streamlit-expanderContent {
        background-color: #1E2128;
        color: white;
        font-size: 16px;
    }
    section[data-testid="stSidebar"] {
        background-color: #1E2128;
    }
    .css-12oz5g7 {
        background-color: #1E2128;
        padding: 1.5rem;
        border-radius: 10px;
    }
    .stAlert {
        background-color: #2D3648;
        color: white;
        font-size: 16px;
    }
    label {
        font-size: 18px;
        color: #FAFAFA;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🌱 Indian Vegetarian Diet & Fitness Planner")
st.markdown("""
    Welcome to your personalized diet and fitness planner! Enter your details to get a tailored Indian vegetarian diet plan, exercise routine, and health tips to support your wellness journey. 🌿
""")

# Sidebar
with st.sidebar:
    st.header("💡 Health Tips")
    st.markdown("""
        - Drink plenty of water daily 💧
        - Eat slowly and mindfully 🍽️
        - Aim for 7–9 hours of sleep 😴
        - Take short walks to stay active 🚶
        - Manage stress with deep breathing 🧘
    """)
    st.header("📱 Track Your Progress")
    st.markdown("""
        - Log your meals and water intake
        - Record exercise sessions
        - Monitor weight and energy levels
    """)

# Load food data
@st.cache_data
def load_food_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, "foods.csv")
        return pd.read_csv(csv_path)
    except FileNotFoundError:
        st.error("Food database not found. Please ensure foods.csv is available.")
        return None
    except Exception as e:
        st.error(f"Error loading food database: {e}")
        return None

food_data = load_food_data()

# Input form
with st.form("user_info"):
    st.subheader("Tell Us About Yourself")
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Name", help="Enter your full name or a nickname.")
        age = st.number_input("Age (years)", min_value=1, max_value=120, value=30, help="Your age helps us tailor portion sizes and calorie needs.")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], help="Used to calculate your calorie needs accurately.")
        weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0, help="Enter your current weight in kilograms.")
        height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0, help="Enter your height in centimeters.")
    
    with col2:
        activity = st.selectbox("Activity Level", ["Sedentary", "Moderate", "Active"], 
                                help="Sedentary: Little exercise; Moderate: 3–5 days/week; Active: 6–7 days/week.")
        dietary_preference = st.selectbox("Dietary Preference", ["Vegetarian", "Vegan"], 
                                         help="Choose Vegetarian (includes dairy) or Vegan (no animal products).")
        allergies = st.multiselect("Allergies", ["Dairy", "Nuts", "Gluten", "Soy"], 
                                   help="Select any food allergies to exclude from your plan.")
        health_goal = st.selectbox("Health Goal", [
            "Maintain Weight", 
            "Lose Weight", 
            "Gain Weight", 
            "Low Sodium Diet", 
            "Keto Diet"
        ], help="Choose your goal:\n- Maintain Weight: Keep current weight\n- Lose Weight: Reduce weight\n- Gain Weight: Build muscle\n- Low Sodium Diet: For hypertension\n- Keto Diet: High-fat, low-carb for ketosis")
        budget = st.selectbox("Budget", ["Low", "Medium", "High"], index=1, 
                              help="Low: Affordable foods (≤₹15/100g); Medium: ≤₹25/100g; High: All foods.")
    
    submitted = st.form_submit_button("Generate My Plan")

# Process submission
if submitted and food_data is not None:
    # Input validation
    if not name.strip():
        st.error("Please enter a name.")
        st.stop()
    if age < 1 or weight < 30 or height < 100:
        st.error("Please enter realistic values: Age > 0, Weight ≥ 30kg, Height ≥ 100cm.")
        st.stop()
    
    # Calculate BMR and calories
    bmr = calculate_bmr(weight, height, age, gender)
    daily_calories, macro_ratios = calculate_daily_calories(bmr, activity, health_goal)
    water_intake = weight * 30
    
    # Display user stats
    st.subheader(f"👋 Hello, {name}!")
    st.success("Your personalized plan has been generated!")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("BMR", f"{bmr:.0f} calories")
    with col2:
        st.metric("Daily Calories", f"{daily_calories:.0f} calories")
    with col3:
        protein = (daily_calories * macro_ratios["protein"]) / 4
        st.metric("Protein Needs", f"{protein:.0f}g/day")
    with col4:
        st.metric("Water Intake", f"{water_intake:.0f}ml/day")
    
    # Health goal warnings
    if health_goal == "Low Sodium Diet":
        st.info("Low Sodium Diet: We've selected foods with low sodium (≤100mg/100g) to support heart health. Consult your doctor for medical advice.")
    elif health_goal == "Keto Diet":
        st.info("Keto Diet: Your plan emphasizes high-fat, low-carb foods to promote ketosis. Stay hydrated and consult a dietitian for long-term use.")
    
    # Tabs for results
    tab1, tab2, tab3 = st.tabs(["🍽️ Diet Plan", "💪 Exercise Guide", "💧 Hydration & Health"])
    
    with tab1:
        st.subheader("Your Personalized Diet Plan")
        diet_plan = generate_diet_plan(
            food_data,
            daily_calories,
            macro_ratios,  # Pass macro_ratios
            age,
            dietary_preference,
            allergies,
            activity,
            budget,
            "Indian",
            health_goal
        )
        
        if diet_plan:
            total_cost = diet_plan.get("total_cost", 0)
            st.info(f"Estimated Daily Food Cost: ₹{total_cost:.0f}")
            
            meal_keys = [key for key in diet_plan.keys() if key != "total_cost"]
            meal_tabs = st.tabs(meal_keys)
            
            for i, meal_name in enumerate(meal_keys):
                with meal_tabs[i]:
                    meal_items = diet_plan[meal_name]
                    if "foods" in meal_items:
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"Total Calories: {meal_items['calories']:.0f}")
                            meal_df = pd.DataFrame(meal_items["foods"])
                            columns_to_show = ["food", "portion", "calories", "protein", "carbs", "fats"]
                            if health_goal == "Low Sodium Diet":
                                columns_to_show.append("sodium")
                            if "price" in meal_df.columns:
                                meal_df["price"] = meal_df["price"].apply(lambda x: f"₹{x:.0f}")
                                columns_to_show.append("price")
                            st.table(meal_df[columns_to_show])
                        with col2:
                            plt.style.use("dark_background")
                            fig, ax = plt.subplots(figsize=(4, 4))
                            fig.patch.set_facecolor("#1E2128")
                            ax.set_facecolor("#1E2128")
                            labels = ["Protein", "Carbs", "Fats"]
                            sizes = [
                                meal_items["macros"]["protein"],
                                meal_items["macros"]["carbs"],
                                meal_items["macros"]["fats"]
                            ]
                            colors = ["#FF9999", "#66B3FF", "#99FF99"]
                            ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90,
                                   textprops={'color': 'white'})
                            ax.axis("equal")
                            st.pyplot(fig)
                            if "cost" in meal_items:
                                st.metric("Meal Cost", f"₹{meal_items['cost']:.0f}")
                            if health_goal == "Low Sodium Diet":
                                st.metric("Meal Sodium", f"{meal_items['macros']['sodium']:.0f}mg")
        else:
            st.error("No foods match your preferences, allergies, or budget. Try adjusting your selections (e.g., fewer allergies, higher budget).")
    
    with tab2:
        st.subheader("🏃‍♂️ Personalized Exercise Guide")
        if health_goal == "Low Sodium Diet":
            st.markdown("""
                ### Gentle Exercise for Heart Health
                **Morning (20–30 minutes):**
                - Light stretching (5 min)
                - Brisk walking (15 min)
                - Breathing exercises (5–10 min)
                
                **Evening (20–30 minutes):**
                - Yoga (e.g., gentle poses like Child’s Pose, Cat-Cow) (15 min)
                - Light bodyweight exercises (10 squats, 10 seated leg lifts, 30-sec wall push-ups)
                
                **Weekly Goals:**
                - Exercise 4–5 days/week
                - Focus on low-impact activities
                - Avoid overexertion
            """)
        else:
            if activity == "Sedentary":
                st.markdown("""
                    ### Beginner's Exercise Routine
                    **Morning (15–20 minutes):**
                    - Light stretching (5 min)
                    - Walking in place (5 min)
                    - Basic yoga poses (10 min)
                    
                    **Evening (20–30 minutes):**
                    - Brisk walking (15 min)
                    - Bodyweight exercises: 10 squats, 10 push-ups (knee), 10 lunges, 30-sec plank
                    
                    **Weekly Goals:**
                    - 3–4 days of exercise
                    - Increase duration gradually
                """)
            elif activity == "Moderate":
                st.markdown("""
                    ### Intermediate Exercise Routine
                    **Morning (30 minutes):**
                    - Dynamic stretching (5 min)
                    - Cardio: Jumping jacks, high knees, mountain climbers (15 min)
                    - Strength: 15 squats, 15 push-ups, 15 lunges, 45-sec plank (10 min)
                    
                    **Evening (30–40 minutes):**
                    - Brisk walking/jogging (20 min)
                    - Circuit: 3 rounds of 20 squats, 20 push-ups, 20 mountain climbers, 1-min plank
                    
                    **Weekly Goals:**
                    - 4–5 days of exercise
                    - Mix cardio and strength
                """)
            else:
                st.markdown("""
                    ### Advanced Exercise Routine
                    **Morning (45–60 minutes):**
                    - Dynamic warm-up (10 min)
                    - High-intensity cardio: Burpees, jump squats, mountain climbers (20 min)
                    - Strength: 3 sets of 20 squats, 20 push-ups, 20 lunges, 1-min plank
                    
                    **Evening (45–60 minutes):**
                    - Running/cycling (30 min)
                    - Circuit: 4 rounds of 25 burpees, 25 squats, 25 push-ups, 1.5-min plank
                    
                    **Weekly Goals:**
                    - 5–6 days of exercise
                    - High-intensity workouts
                """)
    
    with tab3:
        st.subheader("💧 Hydration & Health Guidelines")
        st.markdown(f"""
            ### Daily Water Intake Goal: {water_intake:.0f}ml
            **Schedule:**
            - Morning: 500ml (250ml on waking, 250ml with breakfast)
            - Mid-morning: 500ml (sip throughout)
            - Lunch: 500ml (250ml before, 250ml with lunch)
            - Afternoon: 500ml (regular sips)
            - Evening: 500ml (250ml before, 250ml with dinner)
            - Night: 500ml (as needed)
        """)
        st.subheader("🌿 Health Tips")
        if health_goal == "Low Sodium Diet":
            st.markdown("""
                **Heart-Healthy Tips:**
                - Choose fresh vegetables and fruits
                - Avoid processed foods (e.g., packaged snacks)
                - Season with herbs instead of salt
                - Monitor blood pressure regularly
                - Consult your doctor for personalized advice
            """)
        elif health_goal == "Keto Diet":
            st.markdown("""
                **Keto Tips:**
                - Stay hydrated to support ketosis
                - Include healthy fats (e.g., ghee, nuts)
                - Avoid high-carb foods (e.g., rice, sweets)
                - Monitor ketone levels if possible
                - Consult a dietitian for long-term planning
            """)
        else:
            st.markdown("""
                **General Tips:**
                - Eat a variety of colorful vegetables
                - Practice portion control
                - Aim for 7–9 hours of sleep
                - Take short breaks to reduce stress
                - Schedule regular health check-ups
            """)
    
    # Download plan
    def get_download_link():
        plan_text = f"Personalized Health Plan for {name}\n\n"
        plan_text += f"BMR: {bmr:.0f} calories\n"
        plan_text += f"Daily Calories: {daily_calories:.0f} calories\n"
        plan_text += f"Water Intake: {water_intake:.0f}ml\n"
        plan_text += f"Budget: {budget}\n"
        plan_text += f"Estimated Cost: ₹{diet_plan.get('total_cost', 0):.0f}\n\n"
        
        plan_text += "=== Diet Plan ===\n"
        for meal_name in [k for k in diet_plan.keys() if k != "total_cost"]:
            meal_items = diet_plan[meal_name]
            plan_text += f"\n{meal_name}:\n"
            if "foods" in meal_items:
                for food in meal_items["foods"]:
                    price_str = f" (₹{food['price']:.0f})" if "price" in food else ""
                    sodium_str = f", Sodium: {food['sodium']:.0f}mg" if "sodium" in food else ""
                    plan_text += f"- {food['food']}: {food['portion']} ({food['calories']:.0f} calories{sodium_str}){price_str}\n"
        
        plan_text += "\n=== Exercise Plan ===\n"
        plan_text += f"Activity Level: {activity}\n"
        if health_goal == "Low Sodium Diet":
            plan_text += "Gentle exercises for heart health (yoga, walking, stretching)\n"
        else:
            plan_text += f"{activity} exercise routine (cardio, strength training)\n"
        
        plan_text += "\n=== Health Tips ===\n"
        if health_goal == "Low Sodium Diet":
            plan_text += "- Choose low-sodium foods\n- Avoid processed snacks\n- Monitor blood pressure\n"
        elif health_goal == "Keto Diet":
            plan_text += "- Focus on high-fat, low-carb foods\n- Stay hydrated\n- Monitor ketosis\n"
        else:
            plan_text += "- Stay hydrated\n- Eat balanced meals\n- Exercise regularly\n"
        
        b64 = base64.b64encode(plan_text.encode()).decode()
        return f'<a href="data:file/txt;base64,{b64}" download="health_plan.txt" style="color: #66B3FF; text-decoration: none; padding: 0.5rem 1rem; background-color: #1E2128; border-radius: 5px; border: 1px solid #66B3FF;">Download Your Plan</a>'
    
    if diet_plan:
        st.markdown(get_download_link(), unsafe_allow_html=True)

# About section
with st.expander("ℹ️ About This Planner"):
    st.markdown("""
        ### How It Works
        This planner creates a personalized diet and fitness plan based on your:
        - Age, gender, weight, and height
        - Activity level and dietary preferences
        - Allergies and health goals
        - Budget constraints
        
        ### Features
        - Tailored Indian vegetarian diet plans
        - Exercise routines for all activity levels
        - Hydration and health tips
        - Support for special diets (e.g., low sodium, keto)
        
        ### Budget Levels
        - Low: ₹15 or less per 100g
        - Medium: ₹25 or less per 100g
        - High: All foods
        
        ### Nutritional Balance
        - Standard: 30% protein, 40% carbs, 30% fats
        - Keto: 20% protein, 10% carbs, 70% fats
        - Low Sodium: Low-sodium foods (≤100mg/100g) for heart health
    """)