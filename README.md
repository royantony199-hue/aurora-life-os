# 🌟 Aurora Life OS

AI-powered life management system that helps you organize your calendar, track goals, monitor mood, and achieve your dreams with intelligent scheduling and personalized coaching.

![Aurora Life OS](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![React](https://img.shields.io/badge/react-19.1.1-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

### 🤖 AI-Powered Assistance
- **Smart Calendar Management** - AI optimizes your schedule based on priorities
- **Eisenhower Matrix Integration** - Automatic task prioritization (Urgent/Important)
- **Intelligent Rescheduling** - Auto-adjust dependent tasks when meetings move
- **Natural Language Processing** - "Schedule my gym sessions" or "I need to learn singing"

### 📅 Calendar System
- **Google Calendar Sync** - Seamless two-way synchronization
- **AI Event Creation** - Natural language event scheduling
- **Smart Time Blocking** - Automatic time allocation for goals
- **Meeting Link Detection** - Auto-extract Zoom/Meet/Teams links

### 🎯 Goal & Task Management
- **SMART Goal Framework** - Specific, Measurable, Achievable goals
- **Automatic Task Generation** - AI breaks down goals into actionable tasks
- **Progress Tracking** - Visual progress indicators and analytics
- **Goal Coaching** - Personalized AI coaching for goal achievement

### ❤️ Mood Tracking
- **Daily Mood Logging** - Track emotional well-being
- **Mood-Calendar Correlation** - See how events affect your mood
- **AI Insights** - Personalized recommendations for well-being

### 👤 Personalization
- **Custom Work Hours** - Set your productive hours
- **Coaching Style** - Choose supportive, direct, or balanced coaching
- **Time Zone Support** - Automatic time zone handling
- **Dark/Light Mode** - Eye-friendly themes

## 🚀 Tech Stack

### Frontend
- **React 19** - Latest React with concurrent features
- **TypeScript** - Type-safe development
- **Vite** - Lightning-fast build tool
- **Tailwind CSS** - Modern styling
- **shadcn/ui** - Beautiful UI components

### Backend
- **FastAPI** - High-performance Python framework
- **SQLAlchemy** - Robust ORM with migrations
- **PostgreSQL** - Production database
- **Redis** - Caching and rate limiting
- **JWT Auth** - Secure authentication

### AI/ML
- **OpenAI GPT-4** - Natural language understanding
- **LangChain** - AI workflow orchestration
- **Custom ML Models** - Task prioritization algorithms

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional for development)

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/aurora-life-os.git
cd aurora-life-os
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your values
alembic upgrade head  # Run database migrations
uvicorn app.main:app --reload
```

3. **Frontend Setup**
```bash
cd frontend
npm install
cp .env.example .env  # Edit with your values
npm run dev
```

4. **Access the app**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🔧 Configuration

### Required Environment Variables
```env
# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# Database
DATABASE_URL=postgresql://user:pass@localhost/aurora

# External APIs
OPENAI_API_KEY=your-openai-key

# Google Calendar (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

## 📱 Mobile Support

Aurora Life OS is fully responsive and works seamlessly on:
- 📱 iOS Safari
- 🤖 Android Chrome
- 💻 Desktop browsers
- 📲 Progressive Web App (PWA) support

## 🔒 Security Features

- 🔐 JWT authentication with refresh tokens
- 🔑 Bcrypt password hashing
- 🛡️ Rate limiting & brute force protection
- 🔒 HTTPS enforcement in production
- 🔑 Encrypted sensitive data storage
- 🚫 CORS protection
- 🧹 Input sanitization & validation

## 🚀 Deployment

### Railway (Recommended)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

### Manual Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Google Calendar API
- The React and FastAPI communities
- All our amazing contributors

---

Made with ❤️ by Roy Antony

**[Live Demo](https://aurora-life-os.railway.app)** | **[Documentation](https://docs.aurora-life-os.com)** | **[Report Bug](https://github.com/yourusername/aurora-life-os/issues)**