from flask import Flask, render_template, request
import os
import re
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Initialize Flask App
app = Flask(__name__)
api_key = "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"

# Load API key securely from an environment variable (NEVER expose it in code!)


# Check if API key exists
if not api_key:
    raise ValueError("❌ OpenAI API Key is missing! Set the 'OPENAI_API_KEY' environment variable.")

# Initialize OpenAI model (Use ChatOpenAI for better results)
llm_restro = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, openai_api_key=api_key)

# Function to calculate BMI
def calculate_bmi(weight, height):
    try:
        weight = float(weight)
        height = float(height)
        bmi = round(weight / (height ** 2), 2)  # BMI Formula
        return bmi
    except ValueError:
        return None

# Function to categorize BMI
def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight 🥺 – we need to feed you!"
    elif 18.5 <= bmi < 24.9:
        return "Normal weight ✨ – Look at you! Just the right balance!"
    elif 25 <= bmi < 29.9:
        return "Overweight 😅 – Alright, time to move that cute body!"
    else:
        return "Obese 😭 – Sweetie, we need to fix this ASAP!"

# Define Prompt Template (More human-like, fun, and engaging)
prompt_template_resto = PromptTemplate(
    input_variables=["age", "weight", "height", "gender", "veg_or_nonveg", "disease", "allergics", "foodtype", "bmi", "bmi_category"],
    template="""
    Hey ! 💕 Based on your details:
    - Age: {age}
    - Weight: {weight}
    - Height: {height}
    - Gender: {gender}
    - Dietary Preference: {veg_or_nonveg}
    - Medical Condition: {disease}
    - Allergies: {allergics}
    - Food Type: {foodtype}
    - BMI: {bmi} ({bmi_category})

    Here’s my fabulous advice for you! 😘

    💖 **Daily Routine:**  
    - [Give 3-5 routine suggestions with a fun and sassy touch]  

    🍳 **Breakfast:**  
    - [List 3-4 yummy but healthy breakfast items]  

    🍽 **Dinner:**  
    - [Suggest 3-4 tasty yet balanced dinner ideas]  

    🏋️‍♀️ **Workout Plan:**  
    - [List 3-4 exercises to keep that body in shape]
    """
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    age = request.form.get('age', '').strip()
    gender = request.form.get('gender', '').strip()
    weight = request.form.get('weight', '').strip()
    height = request.form.get('height', '').strip()
    disease = request.form.get('disease', '').strip()
    veg_or_nonveg = request.form.get('veg', '').strip()
    allergic = request.form.get('allergics', '').strip()
    food_type = request.form.get('foodtype', '').strip()

    if not all([age, gender, weight, height, disease, veg_or_nonveg, allergic, food_type]):
        return "⚠️ you forgot to fill in some details! Help me help you. 😘", 400

    bmi = calculate_bmi(weight, height)
    if bmi is None:
        return "⚠️ Oops! Your weight or height isn’t valid, love. Try again. 😭", 400

    bmi_status = bmi_category(bmi)
    input_data = {
        "age": age,
        "weight": weight,
        "height": height,
        "bmi": bmi,
        "bmi_category": bmi_status,
        "gender": gender,
        "veg_or_nonveg": veg_or_nonveg,
        "disease": disease,
        "allergics": allergic,
        "foodtype": food_type
    }

    try:
        # Debug: Print input data before making API call
        print("📡 Sending Data to OpenAI:", input_data)

        chain = LLMChain(llm=llm_restro, prompt=prompt_template_resto)
        response = chain.run(input_data)

        print("🤖 AI Response:", response)  # DEBUG: Check AI output

        if not response.strip():
            return "⚠️ Ugh, AI ghosted us! Try again later, love. 😢", 500

        # Extract data using improved regex
        daily_routine = re.findall(r"💖\s*\*\*Daily Routine:\*\*\s*(.*?)(?=\n🍳|\Z)", response, re.DOTALL)
        breakfast_items = re.findall(r"🍳\s*\*\*Breakfast:\*\*\s*(.*?)(?=\n🍽|\Z)", response, re.DOTALL)
        dinner_items = re.findall(r"🍽\s*\*\*Dinner:\*\*\s*(.*?)(?=\n🏋️‍♀️|\Z)", response, re.DOTALL)
        workout_plans = re.findall(r"🏋️‍♀️\s*\*\*Workout Plan:\*\*\s*(.*?)(?=\Z)", response, re.DOTALL)

        return render_template(
            'result.html',
            bmi=bmi,
            bmi_status=bmi_status,
            daily_routine=daily_routine[0].split('\n') if daily_routine else ["⚠ No daily routine suggestions, blame AI!"],
            breakfast_items=breakfast_items[0].split('\n') if breakfast_items else ["⚠ No breakfast? Tragic!"],
            dinner_items=dinner_items[0].split('\n') if dinner_items else ["⚠ No dinner ideas? I'm disappointed 😞"],
            workout_plans=workout_plans[0].split('\n') if workout_plans else ["⚠ No workouts? Lazy much? 😂"]
        )
    except Exception as e:
        print("❌ Error:", e)
        return f"⚠️ something went wrong! {e}", 500
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_pdf(bmi, bmi_status, daily_routine, breakfast_items, dinner_items, workout_plans):
    pdf_path = "recommendations.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, "Diet & Workout Recommendations")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, f"BMI: {bmi} ({bmi_status})")

    y_position = 700
    sections = {
        "Daily Routine Recommendations": daily_routine,
        "Recommended Breakfast": breakfast_items,
        "Recommended Dinner": dinner_items,
        "Recommended Workouts": workout_plans
    }

    for section, items in sections.items():
        y_position -= 30
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, y_position, section)
        
        c.setFont("Helvetica", 12)
        for item in items:
            y_position -= 20
            c.drawString(120, y_position, f"- {item}")

    c.save()
    return pdf_path

@app.route('/download')
def download():
    pdf_path = generate_pdf(
        request.args.get('bmi', ''),
        request.args.get('bmi_status', ''),
        request.args.getlist('daily_routine'),
        request.args.getlist('breakfast_items'),
        request.args.getlist('dinner_items'),
        request.args.getlist('workout_plans')
    )
    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
