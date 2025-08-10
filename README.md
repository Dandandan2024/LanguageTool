# Adaptive SRS Language Learning App

A modern spaced repetition system (SRS) for language learning, featuring FSRS v4 scheduling, adaptive placement testing, and AI-powered content generation.

## 🚀 Features

- **FSRS v4 Integration**: State-of-the-art spaced repetition scheduling
- **Adaptive Placement Testing**: Computerized Adaptive Testing (CAT) for CEFR level assessment
- **AI Content Generation**: OpenAI-powered sentence variants and difficulty adjustment
- **Multi-language Support**: Currently Russian, easily extensible
- **Modern Web Interface**: Next.js frontend with responsive design
- **RESTful API**: FastAPI backend with comprehensive endpoints

## 🏗️ Project Structure

```
adaptive-srs-monorepo/
├── api/                          # FastAPI backend
│   ├── models/                   # Data models and FSRS implementation
│   ├── services/                 # Business logic services
│   ├── llm/                      # AI content generation
│   ├── scripts/                  # Database and content management scripts
│   │   ├── db/                   # Database setup and migrations
│   │   └── content/              # Content import and generation
│   ├── tests/                    # Test files
│   └── main.py                   # FastAPI application entry point
├── apps/
│   └── web/                      # Next.js frontend
├── infra/                        # Docker infrastructure
└── docs/                         # Documentation
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+, PostgreSQL, Redis
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **SRS Engine**: FSRS v4 (Free Spaced Repetition Scheduler)
- **AI**: OpenAI GPT models for content generation
- **Database**: PostgreSQL with JSONB for flexible metadata

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 15+

### 1. Clone and Setup
```bash
git clone <repository-url>
cd adaptive-srs-monorepo
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your database and OpenAI credentials
```

### 3. Start Infrastructure
```bash
make docker-up
# Or manually:
# docker-compose -f infra/docker-compose.yml up -d
```

### 4. Install Dependencies
```bash
make install
# Or manually:
# pip install -r api/requirements.txt
```

### 5. Initialize Database
```bash
cd api/scripts/db
python init_db.py
python seed_db.py
```

### 6. Run Development Servers

**API Server:**
```bash
make run-api
# Or manually:
# cd api && uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
make run-web
# Or manually:
# cd apps/web && npm run dev
```

### 7. Access Applications
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Core Learning
- `POST /v1/sessions/next` - Get next cards for study session
- `POST /v1/reviews` - Submit review results and update scheduling
- `GET /v1/stats/{username}` - User learning statistics

### Placement Testing
- `POST /v1/placement/start` - Begin adaptive placement test
- `POST /v1/placement/answer` - Submit placement test answers

### Content Generation
- `POST /v1/generate/content` - Generate new learning content
- `POST /v1/generate/batch` - Batch content generation
- `GET /v1/generate/suggestions/{cefr_level}` - Get content suggestions

## 🧪 Development

### Code Quality
```bash
make format      # Format code with black
make lint        # Run linting checks
make test        # Run tests
make clean       # Clean up cache files
```

### Database Management
```bash
# Create new migration
cd api/scripts/db
python create_migration.py

# Run migrations
python run_sql_file.py migration_file.sql
```

### Content Management
```bash
# Import lexemes from CSV
cd api/scripts/content
python import_lexemes_from_csv.py

# Generate cards from lexemes
python generate_cards_from_lexemes.py
```

## 🐳 Docker

### Services
- **PostgreSQL**: Main database (port 5432)
- **Redis**: Caching and session storage (port 6379)

### Commands
```bash
make docker-up      # Start services
make docker-down    # Stop services
make docker-logs    # View logs
```

## 📊 FSRS v4 Integration

The app uses FSRS v4 (Free Spaced Repetition Scheduler) for optimal card scheduling:

- **Ratings**: 1=Again, 2=Hard, 3=Good, 4=Easy
- **State Tracking**: stability, difficulty, interval_days, due_date
- **Adaptive Parameters**: Automatically adjusts based on user performance
- **Offline Support**: Client-side scheduling with server sync

## 🔒 Security & Privacy

- Minimal PII collection
- Encrypted data at rest
- Safe LLM prompts
- CORS protection
- Input validation with Pydantic

## 📈 Roadmap

- [ ] Multi-language support expansion
- [ ] Advanced analytics dashboard
- [ ] Mobile app development
- [ ] Social learning features
- [ ] Advanced AI content personalization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
- Check the [API documentation](http://localhost:8000/docs)
- Review the [development roadmap](FUTURE_DEVELOPMENT_ROADMAP.md)
- Open an issue on GitHub
