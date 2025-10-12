# """
# OpenAI Helper Module for Liver Buddy
# Supports GPT-4o with multimodal capabilities (text + image)
# """

# import streamlit as st
# from openai import OpenAI  # FIXED: Import from openai package, not openai_helper
# import os
# import base64
# from typing import List, Dict, Optional

# class AIHelper:
#     """Wrapper for OpenAI API calls with GPT-4o support"""
    
#     def __init__(self):
#         """Initialize OpenAI client"""
#         try:
#             api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
#             if api_key:
#                 self.client = OpenAI(api_key=api_key)
#                 self.enabled = True
#             else:
#                 self.client = None
#                 self.enabled = False
#                 st.warning("⚠️ OpenAI API key not found. Using demo mode.")
#         except Exception as e:
#             self.client = None
#             self.enabled = False
#             st.warning(f"⚠️ Could not initialize OpenAI: {e}")
    
#     def chat_completion(
#         self, 
#         messages: List[Dict[str, str]], 
#         model: str = "gpt-4o",
#         temperature: float = 0.7,
#         max_tokens: Optional[int] = None
#     ) -> str:
#         """
#         Send messages to ChatGPT and get response
#         Uses GPT-4o by default for best performance
        
#         Args:
#             messages: List of message dicts with 'role' and 'content'
#             model: Model to use (gpt-4o recommended)
#             temperature: Creativity level (0-2)
#             max_tokens: Maximum response length
        
#         Returns:
#             Response text from ChatGPT
#         """
#         if not self.enabled:
#             return self._mock_response(messages[-1]["content"] if messages else "")
        
#         try:
#             response = self.client.chat.completions.create(
#                 model=model,
#                 messages=messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens
#             )
#             return response.choices[0].message.content
#         except Exception as e:
#             st.error(f"OpenAI API Error: {str(e)}")
#             return "I apologize, but I encountered an error. Please try again."
    
#     def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
#         """
#         Analyze image using GPT-4o Vision capabilities
        
#         Args:
#             image_bytes: Raw image bytes from file upload
#             prompt: Text prompt describing what to analyze
        
#         Returns:
#             Analysis text from GPT-4o Vision
#         """
#         if not self.enabled:
#             return "🖼️ Demo mode: Image analysis requires OpenAI API key with GPT-4o access. The AI will analyze food items, portions, nutritional content, and liver-friendly assessment."
        
#         try:
#             # Convert bytes to base64
#             image_base64 = base64.b64encode(image_bytes).decode('utf-8')
#             image_url = f"data:image/jpeg;base64,{image_base64}"
            
#             response = self.client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=[
#                     {
#                         "role": "user",
#                         "content": [
#                             {"type": "text", "text": prompt},
#                             {
#                                 "type": "image_url",
#                                 "image_url": {"url": image_url}
#                             }
#                         ]
#                     }
#                 ],
#                 max_tokens=1500,
#                 temperature=0.3
#             )
#             return response.choices[0].message.content
#         except Exception as e:
#             st.error(f"GPT-4o Vision Error: {str(e)}")
#             return f"Error analyzing image: {str(e)}. Please ensure your OpenAI API key has access to GPT-4o with vision capabilities."
    
#     def _mock_response(self, user_message: str) -> str:
#         """Generate mock response for demo mode"""
#         user_lower = user_message.lower() if user_message else ""
        
#         if "meal" in user_lower or "food" in user_lower or "eat" in user_lower:
#             return """🍽️ **Demo Meal Analysis for Fatty Liver Disease**

# **Food Items Identified:**
# - Grilled chicken breast (lean protein)
# - Steamed broccoli (cruciferous vegetable)
# - Brown rice (whole grain)
# - Olive oil (healthy fat)

# **Nutritional Estimate:**
# - Calories: ~420 kcal
# - Protein: 35g (33%)
# - Carbs: 45g (43%)
# - Fat: 11g (24%)
# - Fiber: 6g

# **Liver Health Score:** 9/10 ✅ **Excellent**

# **Assessment:**
# This meal is very well-suited for fatty liver disease management:
# - ✅ High in lean protein (supports liver repair)
# - ✅ Rich in fiber (aids fat metabolism)
# - ✅ Contains antioxidants from broccoli
# - ✅ Low in saturated fats
# - ✅ No processed ingredients or added sugars

# **Recommendations:**
# 1. Perfect portion size for liver health
# 2. Consider adding colorful vegetables for more phytonutrients
# 3. Ensure olive oil is used raw or low-heat
# 4. Stay hydrated with water or green tea

# *💡 Add your OpenAI API key for detailed AI-powered analysis!*"""
        
#         elif "risk" in user_lower or "assessment" in user_lower:
#             return """⚖️ **Demo Risk Assessment for Fatty Liver Disease**

# **Overall Risk Level:** 🟠 Moderate Risk

# **Key Findings:**
# - BMI indicates overweight category (risk factor)
# - Exercise level below recommended 150 min/week
# - Some dietary improvements needed

# **Protective Factors:**
# - ✅ No smoking
# - ✅ Adequate sleep
# - ✅ Low stress level

# **Recommendations:**
# 1. **Immediate (This Week):**
#    - Start food diary
#    - Begin 30-min daily walks
#    - Eliminate sugary drinks

# 2. **Short-term (1-3 Months):**
#    - Target 5% weight loss
#    - Exercise 150+ min/week
#    - Mediterranean diet pattern

# 3. **Medical Follow-up:**
#    - Schedule hepatologist appointment
#    - Request liver function tests
#    - Consider FibroScan

# *💡 Add your OpenAI API key for personalized AI analysis!*"""
        
#         elif "workout" in user_lower or "exercise" in user_lower:
#             return """💪 **Demo Workout Plan for Fatty Liver Health**

# **30-Minute Moderate Intensity Plan**

# **Warm-up (5 min):**
# - Gentle marching in place - 2 min
# - Arm circles - 1 min
# - Light stretching - 2 min

# **Main Workout (20 min):**
# - Brisk walking or cycling
# - Target: Moderate intensity (able to talk but slightly breathless)
# - Heart rate: 50-70% of maximum

# **Cool-down (5 min):**
# - Slow walking - 2 min
# - Static stretches - 3 min

# **Important for Fatty Liver:**
# - ✅ Exercise reduces liver fat by 20-40%
# - ✅ Improves insulin sensitivity
# - ✅ Start gradually, increase slowly
# - ⚠️ Stay hydrated
# - ⚠️ Don't push to exhaustion

# *💡 Add your OpenAI API key for personalized workout plans!*"""
        
#         elif "medication" in user_lower or "medicine" in user_lower:
#             return """💊 **Demo Medication Analysis**

# **General Safety Information:**
# Most medications can be used safely with fatty liver disease when properly monitored.

# **Important Considerations:**
# 1. ⚠️ Avoid unnecessary medications
# 2. ⚠️ Never exceed prescribed dosages
# 3. ⚠️ Avoid alcohol completely
# 4. ⚠️ Regular liver enzyme monitoring
# 5. ⚠️ Inform all doctors about liver condition

# **Monitoring Recommendations:**
# - Liver function tests every 3-6 months
# - Watch for: jaundice, dark urine, severe fatigue
# - Report any new medications to hepatologist

# **Common Liver-Safe Options:**
# - ✅ Most vitamins and supplements
# - ✅ Omega-3 fatty acids
# - ✅ Vitamin E (when prescribed)
# - ✅ Metformin (for diabetes)

# ⚠️ **Important:** Always consult your healthcare provider before starting, stopping, or changing any medication.

# *💡 Add your OpenAI API key for specific medication analysis!*"""
        
#         else:
#             return """🤖 **Demo Mode Active**

# This is a demonstration response. Add your OpenAI API key to get:
# - ✅ Real-time AI analysis with GPT-4o
# - ✅ Image recognition for meals
# - ✅ Personalized health recommendations
# - ✅ Evidence-based medical advice
# - ✅ Detailed nutritional breakdowns

# Your Liver Buddy features:
# - 🍽️ Smart Meal Analysis
# - ⚖️ Risk Assessment
# - 💪 Workout Planning
# - 💊 Medication Tracking
# - 📊 Progress Analytics

# Ready to help you manage fatty liver disease effectively!"""


# class HealthPrompts:
#     """Specialized prompts for fatty liver disease management"""
    
#     @staticmethod
#     def fatty_liver_nutrition_system():
#         """System prompt for nutritionist"""
#         return """You are a specialized clinical nutritionist focusing on fatty liver disease (NAFLD/NASH) management. 

# Provide evidence-based dietary advice emphasizing:
# - Mediterranean diet principles
# - Low glycemic index foods
# - Portion control for liver health
# - Foods to avoid: refined carbs, saturated fats, processed foods, added sugars, alcohol
# - Foods to encourage: omega-3, fiber, antioxidants, lean proteins, whole grains

# Be practical, actionable, and encouraging. Emphasize that diet + exercise can reverse fatty liver in many cases."""
    
#     @staticmethod
#     def fatty_liver_risk_system():
#         """System prompt for risk assessor"""
#         return """You are a hepatologist AI assistant specializing in fatty liver disease risk assessment.

# Assess risk factors comprehensively, evaluate severity levels, identify modifiable factors, and provide evidence-based recommendations. Never diagnose but guide toward appropriate medical care. Be encouraging about reversibility with lifestyle changes."""
    
#     @staticmethod
#     def fatty_liver_exercise_system():
#         """System prompt for exercise physiologist"""
#         return """You are a clinical exercise physiologist specializing in fatty liver disease patients.

# Key principles:
# - Aerobic exercise reduces liver fat (target 150-300 min/week)
# - Moderate intensity (60-70% max HR) is safe and effective
# - Exercise reduces liver fat 10-15% even without weight loss
# - Progressive overload must be gradual and safe
# - Safety first - avoid overexertion
# - Consistency matters more than intensity

# Create realistic, progressive plans for long-term adherence."""
    
#     @staticmethod
#     def fatty_liver_medication_system():
#         """System prompt for pharmacist"""
#         return """You are a clinical pharmacist with hepatology specialization.

# Assess hepatotoxicity risk, identify drug-induced liver injury potential, recommend monitoring schedules, suggest safer alternatives when appropriate. Always err on the side of caution and recommend medical consultation. Include alcohol interaction warnings. Be specific about liver enzyme monitoring."""
    
#     @staticmethod
#     def create_meal_analysis_prompt(description: str, meal_time: str, portion: str) -> str:
#         """Generate meal analysis prompt for text input"""
#         return f"""Analyze this meal for a patient with fatty liver disease:

# **Meal Description:** {description}
# **Meal Time:** {meal_time}
# **Portion Size:** {portion}

# Provide comprehensive analysis:
# 1. **Foods Identified**: List all items with estimated portions
# 2. **Nutritional Breakdown**: 
#    - Total calories
#    - Protein, carbs (simple vs complex), fats (saturated vs unsaturated)
#    - Fiber, sodium, added sugars
# 3. **Liver-Friendly Score**: Rate 1-10 (10=excellent for liver health)
# 4. **Fatty Liver Assessment**: 
#    - What's good about this meal?
#    - What's concerning? (fried foods, refined carbs, saturated fats, high sodium)
# 5. **Specific Recommendations**: 
#    - Foods to reduce or eliminate
#    - Healthier substitutions
#    - Portion adjustments
# 6. **Action Steps**: Practical advice for next meal

# Be specific, constructive, and encouraging. Focus on liver health impact."""
    
#     @staticmethod
#     def create_image_meal_analysis_prompt(notes: str = "") -> str:
#         """Generate image analysis prompt"""
#         return f"""Analyze this meal photo for a fatty liver disease patient.

# {f'Additional context: {notes}' if notes else ''}

# From the image, identify:
# 1. **Visible Foods**: All items with estimated portions and cooking methods
# 2. **Nutritional Estimate**: Approximate calories, macros, fiber, sodium
# 3. **Liver Health Score**: Rate 1-10 with detailed explanation
# 4. **Red Flags**: 
#    - Fried/greasy foods
#    - Processed items
#    - Large portions
#    - High-fat ingredients
#    - Refined carbohydrates
# 5. **Positive Aspects**: What's good for liver health?
# 6. **Improvements**: Specific suggestions to make this meal liver-friendly

# Be detailed about what you observe. If portions are unclear, provide ranges. Focus on practical, actionable feedback."""
    
#     @staticmethod
#     def create_risk_assessment_prompt(health_data: Dict) -> str:
#         """Generate comprehensive risk assessment prompt"""
#         return f"""Conduct comprehensive fatty liver disease risk assessment:

# **Physical Data:**
# - Age: {health_data.get('age')} years
# - BMI: {health_data.get('bmi')} (Height: {health_data.get('height')}cm, Weight: {health_data.get('weight')}kg)

# **Liver Status:**
# - Current diagnosis: {health_data.get('liver_diagnosis', 'Not specified')}
# - Symptoms: {', '.join(health_data.get('liver_symptoms', [])) if health_data.get('liver_symptoms') else 'None reported'}
# - Family history: {health_data.get('family_liver_history', 'Not specified')}
# - Lab results: {health_data.get('lab_results', 'Not provided')}

# **Lifestyle Factors:**
# - Exercise: {health_data.get('exercise')}h/week
# - Sleep: {health_data.get('sleep')}h/night
# - Alcohol: {health_data.get('alcohol')}
# - Diet quality: {health_data.get('diet_quality')}
# - Smoking: {health_data.get('smoking')}
# - Stress level: {health_data.get('stress')}

# **Medical Conditions:**
# - Related conditions: {', '.join(health_data.get('risk_factors', [])) if health_data.get('risk_factors') else 'None'}
# - Current medications: {health_data.get('medications', 'None listed')}
# - Recent weight change: {health_data.get('recent_weight_change', 'Stable')}

# **Concerns:** {health_data.get('concerns', 'None specified')}

# Provide comprehensive assessment:

# 1. **Risk Score**: 0-100 scale with clear interpretation
# 2. **Risk Category**: Low / Moderate / High / Severe (with explanation)
# 3. **Disease Stage Estimate**: 
#    - Normal liver
#    - Simple steatosis (fat accumulation)
#    - NASH (inflammation + fat)
#    - Fibrosis risk
#    - Cirrhosis risk
# 4. **Top Risk Factors**: List 3-5 key contributors ranked by impact
# 5. **Protective Factors**: What patient is doing well
# 6. **Lab Value Interpretation**: If provided, explain what they mean
# 7. **Detailed Recommendations**:
   
#    **Immediate Actions (This Week):**
#    - 3-5 specific steps
   
#    **Short-term Goals (1-3 Months):**
#    - Measurable objectives
   
#    **Long-term Plan (3-12 Months):**
#    - Sustainable lifestyle changes
   
# 8. **Medical Priority**: 
#    - Urgent (see doctor within days)
#    - Soon (within 2-4 weeks)
#    - Routine (within 3 months)
# 9. **Prognosis**: Expected outcomes with recommended changes
# 10. **Red Flags**: Warning signs requiring immediate medical attention

# Be specific, evidence-based, realistic, and encouraging. Emphasize reversibility."""
    
#     @staticmethod
#     def create_workout_prompt(goals: str, level: str, duration: int) -> str:
#         """Generate workout plan prompt"""
#         return f"""Create a {duration}-minute {level} workout plan for a fatty liver disease patient.

# **Focus Goals:** {goals}
# **Fitness Level:** {level}
# **Session Duration:** {duration} minutes

# Design a structured workout including:

# 1. **Warm-up (5 minutes):**
#    - Specific exercises with timing
#    - Prepare body for main workout

# 2. **Main Workout ({duration-10} minutes):**
#    - Specific exercises with sets/reps/duration
#    - Target heart rate guidance (50-70% max HR)
#    - Rest periods between exercises
#    - Form cues for safety

# 3. **Cool-down (5 minutes):**
#    - Specific stretches with hold times
#    - Breathing exercises
#    - Recovery tips

# 4. **Weekly Progression Plan:**
#    - How to increase intensity safely
#    - When to add duration/frequency
#    - Milestones to track

# 5. **Safety Precautions for Fatty Liver:**
#    - Intensity limits
#    - Hydration guidelines
#    - Warning signs to stop
#    - When to consult doctor

# 6. **Expected Benefits:**
#    - Impact on liver fat
#    - Timeline for results
#    - Other health improvements

# 7. **Tracking Recommendations:**
#    - What to log
#    - Progress markers

# Make it safe, practical, and motivating for {level} fitness level. Focus on consistency over intensity."""
    
#     @staticmethod
#     def create_medication_analysis_prompt(med_name: str, dosage: str, purpose: str, frequency: str = None) -> str:
#         """Generate medication safety analysis prompt"""
#         return f"""Analyze this medication for a fatty liver disease patient:

# **Medication Name:** {med_name}
# **Dosage:** {dosage}
# **Purpose/Indication:** {purpose}
# {f'**Frequency:** {frequency}' if frequency else ''}

# Provide comprehensive analysis:

# 1. **Medication Overview:**
#    - Generic name (if brand given)
#    - Drug class
#    - Primary mechanism of action
#    - Common uses

# 2. **Hepatotoxicity Assessment:**
#    - Risk level: None / Low / Moderate / High / Severe
#    - Detailed explanation of liver risk
#    - Incidence of liver injury (if known)

# 3. **Fatty Liver Specific Concerns:**
#    - Safe for NAFLD/NASH patients? (Yes/Caution/No)
#    - Dose adjustments needed?
#    - Special monitoring required?
#    - Contraindications?

# 4. **Metabolism & Processing:**
#    - How liver processes this drug
#    - Impact on liver enzyme levels
#    - Potential for drug accumulation

# 5. **Drug Interactions:**
#    - Interactions affecting liver
#    - Foods/supplements to avoid
#    - Alcohol interaction (critical)

# 6. **Monitoring Requirements:**
#    - Recommended blood tests
#    - Frequency of monitoring
#    - Baseline tests needed
#    - Warning signs to watch for:
#      * Jaundice
#      * Dark urine
#      * Severe fatigue
#      * Abdominal pain
#      * Unusual bruising

# 7. **Safer Alternatives:**
#    - If hepatotoxic, suggest liver-friendly options
#    - Compare risk/benefit

# 8. **Specific Recommendations:**
#    - Best time to take
#    - With/without food
#    - What to avoid
#    - When to contact doctor

# 9. **Safety Rating:**
#    - 🟢 Green (Safe with normal monitoring)
#    - 🟡 Yellow (Use with caution, close monitoring)
#    - 🔴 Red (Avoid or only with hepatologist approval)

# 10. **Patient Action Steps:**
#     - Immediate actions
#     - Questions to ask doctor
#     - Self-monitoring tips

# Be evidence-based, cite guidelines when possible. Include medical disclaimer. Err on side of caution."""


# # Convenience function
# @st.cache_resource
# def get_ai_helper():
#     """Get or create cached AI helper instance"""
#     return AIHelper()


"""
Gemini Helper Module for Liver Buddy
Supports Gemini Pro and Gemini Pro Vision (multimodal)
FREE API with generous limits!
"""

import streamlit as st
import google.generativeai as genai
import os
from typing import List, Dict, Optional
from PIL import Image
import io

class GeminiHelper:
    """Wrapper for Gemini API calls with multimodal support"""
    
    def __init__(self):
        """Initialize Gemini client"""
        try:
            api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.enabled = True
                
                # Initialize models
                self.text_model = genai.GenerativeModel('gemini-pro')
                self.vision_model = genai.GenerativeModel('gemini-pro-vision')
                
                # Safety settings (relaxed for medical content)
                self.safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            else:
                self.enabled = False
                st.warning("⚠️ Gemini API key not found. Using demo mode.")
        except Exception as e:
            self.enabled = False
            st.warning(f"⚠️ Could not initialize Gemini: {e}")
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Send messages to Gemini and get response
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Creativity level (0-1)
            max_tokens: Maximum response length
        
        Returns:
            Response text from Gemini
        """
        if not self.enabled:
            return self._mock_response(messages[-1]["content"] if messages else "")
        
        try:
            # Convert messages to Gemini format
            prompt = self._format_messages_for_gemini(messages)
            
            # Configure generation
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
            }
            
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            
            # Generate response
            response = self.text_model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            
            return response.text
        
        except Exception as e:
            st.error(f"Gemini API Error: {str(e)}")
            return "I apologize, but I encountered an error. Please try again."
    
    def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        """
        Analyze image using Gemini Pro Vision
        
        Args:
            image_bytes: Raw image bytes from file upload
            prompt: Text prompt describing what to analyze
        
        Returns:
            Analysis text from Gemini Vision
        """
        if not self.enabled:
            return "🖼️ Demo mode: Image analysis requires Gemini API key. The AI will analyze food items, portions, nutritional content, and liver-friendly assessment."
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Generate response with image
            response = self.vision_model.generate_content(
                [prompt, image],
                safety_settings=self.safety_settings
            )
            
            return response.text
        
        except Exception as e:
            st.error(f"Gemini Vision Error: {str(e)}")
            return f"Error analyzing image: {str(e)}. Please try again with a different image."
    
    def _format_messages_for_gemini(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert OpenAI-style messages to Gemini prompt format
        
        Gemini doesn't have system/user/assistant roles like OpenAI.
        We combine everything into a single prompt.
        """
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                # System messages become instructions
                prompt_parts.append(f"INSTRUCTIONS:\n{content}\n")
            elif role == "user":
                prompt_parts.append(f"USER REQUEST:\n{content}\n")
            elif role == "assistant":
                prompt_parts.append(f"PREVIOUS RESPONSE:\n{content}\n")
        
        return "\n".join(prompt_parts)
    
    def _mock_response(self, user_message: str) -> str:
        """Generate mock response for demo mode"""
        user_lower = user_message.lower() if user_message else ""
        
        if "meal" in user_lower or "food" in user_lower or "eat" in user_lower:
            return """🍽️ **Demo Meal Analysis for Fatty Liver Disease**

**Food Items Identified:**
- Grilled chicken breast (lean protein)
- Steamed broccoli (cruciferous vegetable)
- Brown rice (whole grain)
- Olive oil (healthy fat)

**Nutritional Estimate:**
- Calories: ~420 kcal
- Protein: 35g (33%)
- Carbs: 45g (43%)
- Fat: 11g (24%)
- Fiber: 6g

**Liver Health Score:** 9/10 ✅ **Excellent**

**Assessment:**
This meal is very well-suited for fatty liver disease management:
- ✅ High in lean protein (supports liver repair)
- ✅ Rich in fiber (aids fat metabolism)
- ✅ Contains antioxidants from broccoli
- ✅ Low in saturated fats
- ✅ No processed ingredients or added sugars

**Recommendations:**
1. Perfect portion size for liver health
2. Consider adding colorful vegetables for more phytonutrients
3. Ensure olive oil is used raw or low-heat
4. Stay hydrated with water or green tea

*💡 Add your Gemini API key for detailed AI-powered analysis!*"""
        
        elif "risk" in user_lower or "assessment" in user_lower:
            return """⚖️ **Demo Risk Assessment for Fatty Liver Disease**

**Overall Risk Level:** 🟠 Moderate Risk

**Key Findings:**
- BMI indicates overweight category (risk factor)
- Exercise level below recommended 150 min/week
- Some dietary improvements needed

**Protective Factors:**
- ✅ No smoking
- ✅ Adequate sleep
- ✅ Low stress level

**Recommendations:**
1. **Immediate (This Week):**
   - Start food diary
   - Begin 30-min daily walks
   - Eliminate sugary drinks

2. **Short-term (1-3 Months):**
   - Target 5% weight loss
   - Exercise 150+ min/week
   - Mediterranean diet pattern

3. **Medical Follow-up:**
   - Schedule hepatologist appointment
   - Request liver function tests
   - Consider FibroScan

*💡 Add your Gemini API key for personalized AI analysis!*"""
        
        elif "workout" in user_lower or "exercise" in user_lower:
            return """💪 **Demo Workout Plan for Fatty Liver Health**

**30-Minute Moderate Intensity Plan**

**Warm-up (5 min):**
- Gentle marching in place - 2 min
- Arm circles - 1 min
- Light stretching - 2 min

**Main Workout (20 min):**
- Brisk walking or cycling
- Target: Moderate intensity (able to talk but slightly breathless)
- Heart rate: 50-70% of maximum

**Cool-down (5 min):**
- Slow walking - 2 min
- Static stretches - 3 min

**Important for Fatty Liver:**
- ✅ Exercise reduces liver fat by 20-40%
- ✅ Improves insulin sensitivity
- ✅ Start gradually, increase slowly
- ⚠️ Stay hydrated
- ⚠️ Don't push to exhaustion

*💡 Add your Gemini API key for personalized workout plans!*"""
        
        elif "medication" in user_lower or "medicine" in user_lower:
            return """💊 **Demo Medication Analysis**

**General Safety Information:**
Most medications can be used safely with fatty liver disease when properly monitored.

**Important Considerations:**
1. ⚠️ Avoid unnecessary medications
2. ⚠️ Never exceed prescribed dosages
3. ⚠️ Avoid alcohol completely
4. ⚠️ Regular liver enzyme monitoring
5. ⚠️ Inform all doctors about liver condition

**Monitoring Recommendations:**
- Liver function tests every 3-6 months
- Watch for: jaundice, dark urine, severe fatigue
- Report any new medications to hepatologist

**Common Liver-Safe Options:**
- ✅ Most vitamins and supplements
- ✅ Omega-3 fatty acids
- ✅ Vitamin E (when prescribed)
- ✅ Metformin (for diabetes)

⚠️ **Important:** Always consult your healthcare provider before starting, stopping, or changing any medication.

*💡 Add your Gemini API key for specific medication analysis!*"""
        
        else:
            return """🤖 **Demo Mode Active**

This is a demonstration response. Add your Gemini API key to get:
- ✅ Real-time AI analysis with Gemini Pro
- ✅ Image recognition for meals (Gemini Vision)
- ✅ Personalized health recommendations
- ✅ Evidence-based medical advice
- ✅ Detailed nutritional breakdowns

**Gemini API is FREE** with generous limits!

Your Liver Buddy features:
- 🍽️ Smart Meal Analysis
- ⚖️ Risk Assessment
- 💪 Workout Planning
- 💊 Medication Tracking
- 📊 Progress Analytics

Ready to help you manage fatty liver disease effectively!"""


class HealthPrompts:
    """Specialized prompts for fatty liver disease management"""
    
    @staticmethod
    def fatty_liver_nutrition_system():
        """System prompt for nutritionist"""
        return """You are a specialized clinical nutritionist focusing on fatty liver disease (NAFLD/NASH) management. 

Provide evidence-based dietary advice emphasizing:
- Mediterranean diet principles
- Low glycemic index foods
- Portion control for liver health
- Foods to avoid: refined carbs, saturated fats, processed foods, added sugars, alcohol
- Foods to encourage: omega-3, fiber, antioxidants, lean proteins, whole grains

Be practical, actionable, and encouraging. Emphasize that diet + exercise can reverse fatty liver in many cases.

Format your response clearly with headers, bullet points, and actionable recommendations."""
    
    @staticmethod
    def fatty_liver_risk_system():
        """System prompt for risk assessor"""
        return """You are a hepatologist AI assistant specializing in fatty liver disease risk assessment.

Assess risk factors comprehensively, evaluate severity levels, identify modifiable factors, and provide evidence-based recommendations. Never diagnose but guide toward appropriate medical care. Be encouraging about reversibility with lifestyle changes.

Structure your assessment with:
1. Risk Score and Level
2. Key Risk Factors
3. Protective Factors
4. Detailed Recommendations (immediate, short-term, long-term)
5. Red flags requiring medical attention"""
    
    @staticmethod
    def fatty_liver_exercise_system():
        """System prompt for exercise physiologist"""
        return """You are a clinical exercise physiologist specializing in fatty liver disease patients.

Key principles:
- Aerobic exercise reduces liver fat (target 150-300 min/week)
- Moderate intensity (60-70% max HR) is safe and effective
- Exercise reduces liver fat 10-15% even without weight loss
- Progressive overload must be gradual and safe
- Safety first - avoid overexertion
- Consistency matters more than intensity

Create realistic, progressive plans with:
- Detailed warm-up, main workout, cool-down
- Specific exercises with timing/reps
- Safety precautions for liver patients
- Weekly progression plan"""
    
    @staticmethod
    def fatty_liver_medication_system():
        """System prompt for pharmacist"""
        return """You are a clinical pharmacist with hepatology specialization.

Assess hepatotoxicity risk, identify drug-induced liver injury potential, recommend monitoring schedules, suggest safer alternatives when appropriate. Always err on the side of caution and recommend medical consultation. Include alcohol interaction warnings. Be specific about liver enzyme monitoring.

Structure your analysis with:
1. Medication Overview
2. Hepatotoxicity Risk Level
3. Fatty Liver Specific Concerns
4. Monitoring Requirements
5. Safety Rating (Green/Yellow/Red)
6. Patient Action Steps"""
    
    @staticmethod
    def create_meal_analysis_prompt(description: str, meal_time: str, portion: str) -> str:
        """Generate meal analysis prompt for text input"""
        return f"""Analyze this meal for a patient with fatty liver disease:

**Meal Description:** {description}
**Meal Time:** {meal_time}
**Portion Size:** {portion}

Provide comprehensive analysis:

1. **Foods Identified**: List all items with estimated portions

2. **Nutritional Breakdown**: 
   - Total calories
   - Protein, carbs (simple vs complex), fats (saturated vs unsaturated)
   - Fiber, sodium, added sugars

3. **Liver-Friendly Score**: Rate 1-10 (10=excellent for liver health)

4. **Fatty Liver Assessment**: 
   - What's good about this meal?
   - What's concerning? (fried foods, refined carbs, saturated fats, high sodium)

5. **Specific Recommendations**: 
   - Foods to reduce or eliminate
   - Healthier substitutions
   - Portion adjustments

6. **Action Steps**: Practical advice for next meal

Be specific, constructive, and encouraging. Focus on liver health impact."""
    
    @staticmethod
    def create_image_meal_analysis_prompt(notes: str = "") -> str:
        """Generate image analysis prompt"""
        base_prompt = f"""Analyze this meal photo for a fatty liver disease patient.

{f'Additional context: {notes}' if notes else ''}

From the image, identify:

1. **Visible Foods**: All items with estimated portions and cooking methods

2. **Nutritional Estimate**: Approximate calories, macros, fiber, sodium

3. **Liver Health Score**: Rate 1-10 with detailed explanation

4. **Red Flags**: 
   - Fried/greasy foods
   - Processed items
   - Large portions
   - High-fat ingredients
   - Refined carbohydrates

5. **Positive Aspects**: What's good for liver health?

6. **Improvements**: Specific suggestions to make this meal liver-friendly

Be detailed about what you observe. If portions are unclear, provide ranges. Focus on practical, actionable feedback."""
        
        return base_prompt
    
    @staticmethod
    def create_risk_assessment_prompt(health_data: Dict) -> str:
        """Generate comprehensive risk assessment prompt"""
        return f"""Conduct comprehensive fatty liver disease risk assessment:

**Physical Data:**
- Age: {health_data.get('age')} years
- BMI: {health_data.get('bmi')} (Height: {health_data.get('height')}cm, Weight: {health_data.get('weight')}kg)

**Liver Status:**
- Current diagnosis: {health_data.get('liver_diagnosis', 'Not specified')}
- Symptoms: {', '.join(health_data.get('liver_symptoms', [])) if health_data.get('liver_symptoms') else 'None reported'}
- Family history: {health_data.get('family_liver_history', 'Not specified')}
- Lab results: {health_data.get('lab_results', 'Not provided')}

**Lifestyle Factors:**
- Exercise: {health_data.get('exercise')}h/week
- Sleep: {health_data.get('sleep')}h/night
- Alcohol: {health_data.get('alcohol')}
- Diet quality: {health_data.get('diet_quality')}
- Smoking: {health_data.get('smoking')}
- Stress level: {health_data.get('stress')}

**Medical Conditions:**
- Related conditions: {', '.join(health_data.get('risk_factors', [])) if health_data.get('risk_factors') else 'None'}
- Current medications: {health_data.get('medications', 'None listed')}
- Recent weight change: {health_data.get('recent_weight_change', 'Stable')}

**Concerns:** {health_data.get('concerns', 'None specified')}

Provide comprehensive assessment:

1. **Risk Score**: 0-100 scale with clear interpretation

2. **Risk Category**: Low / Moderate / High / Severe (with explanation)

3. **Disease Stage Estimate**: 
   - Normal liver / Simple steatosis / NASH / Fibrosis risk / Cirrhosis risk

4. **Top Risk Factors**: List 3-5 key contributors ranked by impact

5. **Protective Factors**: What patient is doing well

6. **Lab Value Interpretation**: If provided, explain what they mean

7. **Detailed Recommendations**:
   **Immediate Actions (This Week):** 3-5 specific steps
   **Short-term Goals (1-3 Months):** Measurable objectives
   **Long-term Plan (3-12 Months):** Sustainable lifestyle changes

8. **Medical Priority**: Urgent / Soon / Routine

9. **Prognosis**: Expected outcomes with recommended changes

10. **Red Flags**: Warning signs requiring immediate medical attention

Be specific, evidence-based, realistic, and encouraging. Emphasize reversibility."""
    
    @staticmethod
    def create_workout_prompt(goals: str, level: str, duration: int) -> str:
        """Generate workout plan prompt"""
        return f"""Create a {duration}-minute {level} workout plan for a fatty liver disease patient.

**Focus Goals:** {goals}
**Fitness Level:** {level}
**Session Duration:** {duration} minutes

Design a structured workout including:

1. **Warm-up (5 minutes):**
   - Specific exercises with timing
   - Prepare body for main workout

2. **Main Workout ({duration-10} minutes):**
   - Specific exercises with sets/reps/duration
   - Target heart rate guidance (50-70% max HR)
   - Rest periods between exercises
   - Form cues for safety

3. **Cool-down (5 minutes):**
   - Specific stretches with hold times
   - Breathing exercises
   - Recovery tips

4. **Weekly Progression Plan:**
   - How to increase intensity safely
   - When to add duration/frequency
   - Milestones to track

5. **Safety Precautions for Fatty Liver:**
   - Intensity limits
   - Hydration guidelines
   - Warning signs to stop
   - When to consult doctor

6. **Expected Benefits:**
   - Impact on liver fat
   - Timeline for results
   - Other health improvements

7. **Tracking Recommendations:**
   - What to log
   - Progress markers

Make it safe, practical, and motivating for {level} fitness level. Focus on consistency over intensity."""
    
    @staticmethod
    def create_medication_analysis_prompt(med_name: str, dosage: str, purpose: str, frequency: str = None) -> str:
        """Generate medication safety analysis prompt"""
        return f"""Analyze this medication for a fatty liver disease patient:

**Medication Name:** {med_name}
**Dosage:** {dosage}
**Purpose/Indication:** {purpose}
{f'**Frequency:** {frequency}' if frequency else ''}

Provide comprehensive analysis:

1. **Medication Overview:**
   - Generic name (if brand given)
   - Drug class
   - Primary mechanism of action

2. **Hepatotoxicity Assessment:**
   - Risk level: None / Low / Moderate / High / Severe
   - Detailed explanation of liver risk

3. **Fatty Liver Specific Concerns:**
   - Safe for NAFLD/NASH patients? (Yes/Caution/No)
   - Dose adjustments needed?
   - Special monitoring required?

4. **Metabolism & Processing:**
   - How liver processes this drug
   - Impact on liver enzyme levels

5. **Drug Interactions:**
   - Interactions affecting liver
   - Foods/supplements to avoid
   - Alcohol interaction (critical)

6. **Monitoring Requirements:**
   - Recommended blood tests
   - Frequency of monitoring
   - Warning signs to watch for: Jaundice, Dark urine, Severe fatigue, Abdominal pain

7. **Safer Alternatives:**
   - If hepatotoxic, suggest liver-friendly options

8. **Safety Rating:**
   - 🟢 Green (Safe with normal monitoring)
   - 🟡 Yellow (Use with caution, close monitoring)
   - 🔴 Red (Avoid or only with hepatologist approval)

9. **Patient Action Steps:**
   - Questions to ask doctor
   - Self-monitoring tips

Be evidence-based. Include medical disclaimer. Err on side of caution."""


# Convenience function
@st.cache_resource
def get_ai_helper():
    """Get or create cached Gemini helper instance"""
    return GeminiHelper()