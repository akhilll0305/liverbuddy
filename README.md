# 🫀 Liver Buddy

### AI-Powered Companion for Fatty Liver Disease Management

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![Gemini](https://img.shields.io/badge/Google%20AI-Gemini%201.5-blueviolet.svg)](https://ai.google.dev/)
[![Firebase](https://img.shields.io/badge/Firebase-9.0+-orange.svg)](https://firebase.google.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Overview

**Liver Buddy** is a comprehensive AI-powered health management application specifically designed for patients with fatty liver disease (NAFLD/NASH). Using advanced GPT-4o multimodal capabilities, it provides personalized nutrition analysis, risk assessment, exercise planning, and medication tracking.

### 🎯 The Problem

- **25% of adults worldwide** have fatty liver disease
- **No medications exist** - only lifestyle changes work
- Patients struggle with **lack of personalized guidance**
- Traditional healthcare can't provide **continuous monitoring**

### 💡 The Solution

Liver Buddy offers:
- 🍽️ **Smart meal analysis** from text or photos
- ⚖️ **Personalized risk assessment** with actionable plans
- 💪 **Safe exercise programs** designed for liver patients
- 💊 **Medication safety analysis** for hepatotoxicity
- 📊 **Progress tracking** with comprehensive analytics
- 📄 **Health reports** for doctor appointments

---

## ✨ Features

### 1. 👤 Patient Profile Management
- Complete demographic information
- Medical history tracking
- Blood group and contact details
- Editable profile with persistent storage

### 2. 🍽️ Smart Meal Planner
- **Multimodal input**: Text description or photo upload
- **GPT-4o Vision**: Identifies foods from images
- **Nutritional analysis**: Calories, macros, micronutrients
- **Liver-friendly scoring**: 1-10 rating system
- **Personalized recommendations**: Food swaps, portion control
- **Foods to avoid**: Specific guidance for fatty liver

### 3. 📊 Nutrition Tracker & Dashboard
- Daily meal logging with timestamps
- Weekly and monthly trend analysis
- Meal type distribution charts
- Consistency tracking and streaks
- Liver-friendly compliance percentage
- Visual analytics with interactive charts

### 4. ⚖️ Fatty Liver Risk Assessment
- **Comprehensive evaluation**: 30+ health factors
- **Risk scoring**: 0-100 scale with interpretation
- **Stage assessment**: Normal → Steatosis → NASH → Fibrosis
- **BMI calculation**: Automatic from height/weight
- **Lab results integration**: ALT, AST, GGT analysis
- **Action plan**: Immediate, short-term, long-term goals
- **Downloadable reports**: Share with healthcare providers

### 5. 💪 Exercise & Workout Plans
- Safe workouts for liver patients
- Moderate-intensity focus (50-70% max HR)
- Customized by fitness level
- Structured sessions: warm-up, main, cool-down
- Weekly progression plans
- Liver-specific safety precautions
- Expected benefits timeline

### 6. 💊 Medication Tracker & Analysis
- **AI safety analysis**: Hepatotoxicity risk assessment
- **Drug interactions**: Liver-specific warnings
- **Monitoring guidelines**: Lab test recommendations
- **Safer alternatives**: If medications are risky
- **Reminder system**: Track active medications
- **Progress tracking**: Days remaining, compliance

### 7. 📊 Health Reports & Analytics
- **Executive summaries**: Overall health status
- **Trend visualizations**: Charts and graphs
- **Progress metrics**: Goals and achievements
- **Comprehensive reports**: All activities in one document
- **Downloadable formats**: Text reports for doctors
- **Activity timeline**: Recent health actions

---

### Backend
- **Python 3.8+** - Core application  
- **Gemini API (Google AI)** - AI analysis & recommendations  
- **Firebase Authentication** - User management  
- **Cloud Firestore** - NoSQL database  

### AI & ML
- **Gemini 2.5 Pro** - Multimodal text + image analysis  
- **Google Cloud Vision API** - Food recognition from photos  
- **Natural Language Processing** - Meal descriptions  
- **Predictive analytics** - Risk assessment  


### Data & Analytics
- **Pandas** - Data manipulation
- **Streamlit Charts** - Visualizations
- **Real-time updates** - Live dashboards

---

## 📦 Installation

### Prerequisites
```bash
Python 3.8 or higher
pip package manager
Firebase account (free tier)
OpenAI API key
```

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/liver-buddy.git
cd liver-buddy
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Secrets
Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "sk-proj-your-openai-key-here"
FIREBASE_WEB_API_KEY = "your-firebase-web-api-key"

[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-cert-url"
```

### Step 4: Run Application
```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

---

## 📁 Project Structure

```
liver-buddy/
│
├── app.py                  # Main Streamlit application
├── firebase_helper.py      # Firebase authentication & Firestore
├── openai_helper.py        # OpenAI GPT-4o integration
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── .streamlit/
│   └── secrets.toml       # API keys and credentials (gitignored)
│
└── .gitignore             # Git ignore file
```

---

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key with GPT-4o access | Yes |
| `FIREBASE_WEB_API_KEY` | Firebase Web API key | Yes |
| `firebase.*` | Firebase service account credentials | Yes |

---

## 🚀 Usage Guide

### For Patients

#### 1. **Getting Started**
```
1. Register with email and password
2. Complete your profile (name, age, address, blood group)
3. Explore the dashboard
```

#### 2. **Log Your Meals**
```
Option A - Text Input:
- Describe your meal: "Grilled salmon, quinoa, spinach salad"
- Select meal type and portion size
- Get instant AI analysis

Option B - Photo Upload:
- Take a photo of your meal
- Upload to app
- AI identifies foods and analyzes nutrition
```

#### 3. **Track Your Progress**
```
- View nutrition dashboard daily
- Check weekly trends
- Monitor liver-friendly compliance
- Generate monthly reports
```

#### 4. **Stay Active**
```
- Get personalized workout plans
- Follow safe exercises for liver health
- Track consistency
```

#### 5. **Manage Medications**
```
- Add all medications
- Get safety analysis
- Set reminders
- Track adherence
```

### For Developers

#### Running in Development
```bash
streamlit run app.py --server.port 8501
```

#### Running in Production
```bash
streamlit run app.py --server.port 80 --server.address 0.0.0.0
```

#### Demo Mode (No API Keys)
The app gracefully degrades to demo mode if API keys are missing. All features work with simulated responses.

---

## 🧪 Testing

### Manual Testing Checklist

```bash
# Test 1: Authentication
✓ Registration with full profile
✓ Login with credentials
✓ Logout functionality

# Test 2: Meal Analysis
✓ Text-based meal analysis
✓ Image-based meal analysis
✓ Save to history

# Test 3: Risk Assessment
✓ Complete assessment form
✓ Generate risk report
✓ Download report

# Test 4: Workout Plans
✓ Generate custom plan
✓ View past plans

# Test 5: Medications
✓ Add medication
✓ View analysis
✓ Track adherence

# Test 6: Health Reports
✓ Generate weekly report
✓ Generate monthly report
✓ Download report
```

---

## 📊 Database Schema

### Firestore Collections

```
users/
  {user_id}/
    - email: string
    - fullName: string
    - age: number
    - phone: string
    - bloodGroup: string
    - address: object
    - created_at: timestamp
    - last_login: timestamp
    
    meal_plans/
      {meal_id}/
        - date: timestamp
        - meal_type: string
        - description: string
        - analysis: string
        - has_image: boolean
    
    nutrition_logs/
      {log_id}/
        - date: timestamp
        - meal_type: string
        - portion: string
        - analysis: string
    
    risk_assessments/
      {assessment_id}/
        - assessment_date: timestamp
        - bmi: number
        - risk_score: number
        - assessment: string
    
    workout_plans/
      {workout_id}/
        - date: timestamp
        - workout_type: string
        - duration: number
        - plan: string
    
    medications/
      {med_id}/
        - medication_name: string
        - dosage: string
        - frequency: string
        - analysis: string
```

---

## 🔒 Security & Privacy

### Data Protection
- ✅ Firebase Authentication (secure login)
- ✅ Encrypted data transmission (HTTPS)
- ✅ User data isolation (Firestore security rules)
- ✅ No sensitive data in logs
- ✅ API keys in environment variables

### HIPAA Considerations
- Medical data stored in Firebase (HIPAA-compliant infrastructure)
- No PHI in application logs
- User consent required for data usage
- Data retention policies configurable

### Best Practices
```python
# Never commit secrets
.streamlit/secrets.toml  # in .gitignore

# Use environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate user input
if not email or not password:
    return False, "Invalid input"
```

---

## 🌐 Deployment

### Deploy to Streamlit Cloud

1. **Push to GitHub**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Connect to Streamlit Cloud**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Connect your GitHub repository
- Select `app.py` as main file

3. **Add Secrets**
- In Streamlit Cloud dashboard
- Go to App Settings → Secrets
- Paste your `secrets.toml` content

### Deploy to Heroku

```bash
# Create Procfile
echo "web: streamlit run app.py --server.port $PORT" > Procfile

# Deploy
heroku create liver-buddy
git push heroku main
```

### Deploy to AWS/GCP/Azure

See detailed deployment guides in `/docs/deployment/`

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Areas for Contribution
- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🎨 UI/UX enhancements
- 🧪 Test coverage
- 🌍 Internationalization

### Contribution Process
```bash
1. Fork the repository
2. Create feature branch: git checkout -b feature-name
3. Make your changes
4. Test thoroughly
5. Commit: git commit -m "Add feature"
6. Push: git push origin feature-name
7. Create Pull Request
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- **OpenAI** - GPT-4o API
- **Firebase** - Authentication & Database
- **Streamlit** - Web framework
- **Medical advisors** - Clinical validation
- **Open source community** - Dependencies

---

## 📞 Support

### Documentation
- [User Guide](docs/user-guide.md)
- [API Documentation](docs/api.md)
- [FAQ](docs/faq.md)

### Get Help
- 📧 Email: support@liverbuddy.com
- 💬 Discord: [Join Community](https://discord.gg/liverbuddy)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/liver-buddy/issues)

---

## 🗺️ Roadmap

### Phase 1 (Current) ✅
- [x] User authentication
- [x] Meal analysis (text + image)
- [x] Risk assessment
- [x] Workout plans
- [x] Medication tracking
- [x] Health reports

### Phase 2 (Next 3 months)
- [ ] Wearable device integration (Fitbit, Apple Watch)
- [ ] Voice meal logging
- [ ] Doctor portal
- [ ] Lab results tracking (ALT, AST, FibroScan)
- [ ] Community features
- [ ] Mobile app (React Native)

### Phase 3 (6 months)
- [ ] Telemedicine integration
- [ ] AI meal recommendations
- [ ] Grocery list generation
- [ ] Recipe database
- [ ] Clinical trial matching
- [ ] Insurance integration

### Phase 4 (12 months)
- [ ] Research partnerships
- [ ] FDA validation studies
- [ ] Hospital system integration
- [ ] International expansion
- [ ] Multi-language support

---

## 📊 Impact & Metrics

### Target Audience
- 📈 **Global NAFLD patients**: 2 billion+
- 🎯 **Primary users**: Adults 30-60 years
- 🏥 **Healthcare providers**: Hepatologists, dietitians

### Success Metrics
- **User engagement**: Daily active users
- **Health outcomes**: % improvement in liver health
- **Compliance**: Meal logging consistency
- **Satisfaction**: Net Promoter Score (NPS)

---

## ⚠️ Medical Disclaimer

**IMPORTANT**: Liver Buddy is a health tracking and educational tool. It is NOT a substitute for professional medical advice, diagnosis, or treatment.

- Always consult qualified healthcare professionals
- Never disregard medical advice based on app information
- Emergency situations require immediate medical attention
- Individual results may vary
- App recommendations are general guidance

---

## 🔗 Links

- **Website**: [liverbuddy.com](https://liverbuddy.com)
- **Documentation**: [docs.liverbuddy.com](https://docs.liverbuddy.com)
- **Blog**: [blog.liverbuddy.com](https://blog.liverbuddy.com)
- **API**: [api.liverbuddy.com](https://api.liverbuddy.com)

---

## ⭐ Star History

If you find Liver Buddy helpful, please consider giving it a star! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/liver-buddy&type=Date)](https://star-history.com/#yourusername/liver-buddy)

---

<div align="center">

**Made with ❤️ for fatty liver disease patients worldwide**

[Website](https://liverbuddy.com) • [Documentation](https://docs.liverbuddy.com) • [Community](https://discord.gg/liverbuddy)

</div>

---

## 📈 Statistics

![GitHub stars](https://img.shields.io/github/stars/yourusername/liver-buddy?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/liver-buddy?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/yourusername/liver-buddy?style=social)

![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/liver-buddy)
![GitHub issues](https://img.shields.io/github/issues/yourusername/liver-buddy)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/liver-buddy)

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Status**: Active Development 🚀