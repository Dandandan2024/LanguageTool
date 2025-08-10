# Development Guide

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git

### Development Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd adaptive-srs-monorepo
   ```

2. **Install Python dependencies**
   ```bash
   make install-dev
   # Or manually:
   # pip install -r api/requirements.txt
   # pip install pytest pytest-asyncio black flake8 mypy
   ```

3. **Install Node.js dependencies**
   ```bash
   cd apps/web
   npm install
   cd ../..
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Start infrastructure services**
   ```bash
   make docker-up
   ```

## Project Structure

```
adaptive-srs-monorepo/
├── api/                          # FastAPI backend
│   ├── models/                   # Data models and FSRS implementation
│   │   ├── __init__.py
│   │   └── fsrs.py              # FSRS v4 scheduler
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── placement_cat.py     # Placement testing service
│   │   └── contextual_learning.py # Contextual learning logic
│   ├── llm/                      # AI content generation
│   │   ├── __init__.py
│   │   ├── content_generator.py # OpenAI integration
│   │   └── generation_api.py    # Generation API endpoints
│   ├── scripts/                  # Database and content management
│   │   ├── db/                   # Database setup and migrations
│   │   └── content/              # Content import and generation
│   ├── tests/                    # Test files
│   ├── main.py                   # FastAPI application entry point
│   └── requirements.txt          # Python dependencies
├── apps/
│   └── web/                      # Next.js frontend
├── infra/                        # Docker infrastructure
├── docs/                         # Documentation
├── Makefile                      # Development commands
├── pyproject.toml               # Python project configuration
└── README.md                    # Project overview
```

## Development Workflow

### Code Quality Standards

- **Python**: Follow PEP 8 with 88 character line length (Black)
- **Type Hints**: Use type hints for all function parameters and return values
- **Documentation**: Docstrings for all public functions and classes
- **Testing**: Unit tests for all business logic, integration tests for API endpoints

### Code Style

Run the following commands before committing:

```bash
make format      # Format code with Black
make lint        # Run linting checks
make test        # Run tests
```

### Git Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation if needed

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

4. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Use conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest api/tests/test_specific.py -v

# Run tests with coverage
pytest api/tests/ --cov=api --cov-report=html

# Run only unit tests
pytest api/tests/ -m "unit"

# Run only integration tests
pytest api/tests/ -m "integration"
```

### Test Structure

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test API endpoints and database interactions
- **Fixtures**: Use pytest fixtures for common test data

### Example Test

```python
import pytest
from api.models.fsrs import FSRS, Card, Rating

class TestFSRS:
    def test_schedule_card_new(self):
        """Test scheduling a new card"""
        fsrs = FSRS()
        card = Card(id="1", stability=0.0, difficulty=0.0)
        
        result = fsrs.schedule_card(card, Rating.GOOD)
        
        assert result.interval_days > 0
        assert result.stability > 0.0
```

## Database Development

### Schema Changes

1. **Create a new migration file**
   ```bash
   cd api/scripts/db
   # Create SQL file with your changes
   ```

2. **Test the migration**
   ```bash
   python run_sql_file.py your_migration.sql
   ```

3. **Update the schema documentation**
   - Document new tables/columns
   - Update data models if needed

### Database Models

- Use Pydantic models for API request/response validation
- Keep database schema and API models in sync
- Use JSONB for flexible metadata storage

## API Development

### Adding New Endpoints

1. **Define the endpoint in main.py**
   ```python
   @app.post("/v1/new-endpoint")
   async def new_endpoint(request: NewRequestModel):
       # Implementation
       pass
   ```

2. **Create Pydantic models for request/response**
   ```python
   class NewRequestModel(BaseModel):
       field1: str
       field2: int
   
   class NewResponseModel(BaseModel):
       result: str
       status: str
   ```

3. **Add tests for the endpoint**
   ```python
   def test_new_endpoint():
       # Test implementation
       pass
   ```

4. **Update API documentation**
   - Add endpoint to docs/API.md
   - Include request/response examples

### Error Handling

- Use appropriate HTTP status codes
- Return consistent error response format
- Log errors for debugging
- Provide user-friendly error messages

## Frontend Development

### Next.js Structure

- **Components**: Reusable UI components in `components/`
- **Pages**: Route components in `app/`
- **Hooks**: Custom React hooks in `hooks/`
- **Utils**: Utility functions in `utils/`

### Styling

- Use TailwindCSS for styling
- Follow responsive design principles
- Maintain consistent design system

### State Management

- Use React hooks for local state
- Consider Context API for global state
- Keep state as close to where it's used as possible

## Performance Considerations

### Backend

- Use database indexes for frequently queried fields
- Implement caching for expensive operations
- Use async/await for I/O operations
- Monitor database query performance

### Frontend

- Implement lazy loading for components
- Use React.memo for expensive components
- Optimize bundle size
- Implement proper error boundaries

## Security

### Input Validation

- Validate all user inputs with Pydantic
- Sanitize data before database storage
- Use parameterized queries to prevent SQL injection

### Authentication & Authorization

- Implement proper user authentication
- Validate user permissions for protected endpoints
- Use HTTPS in production
- Implement rate limiting

## Deployment

### Environment Configuration

- Use environment variables for configuration
- Never commit sensitive data
- Use different configurations for dev/staging/prod

### Docker

- Keep Docker images lightweight
- Use multi-stage builds when possible
- Implement health checks
- Use proper logging

## Monitoring & Logging

### Logging

- Use structured logging
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Include request IDs for tracing
- Don't log sensitive information

### Monitoring

- Monitor API response times
- Track error rates
- Monitor database performance
- Set up alerts for critical issues

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check if Docker services are running
   - Verify environment variables
   - Check database logs

2. **Import errors**
   - Ensure virtual environment is activated
   - Check Python path
   - Verify package installation

3. **CORS errors**
   - Check allowed origins in main.py
   - Verify frontend URL configuration

### Debug Mode

Enable debug mode for development:

```bash
# Set environment variable
export DEBUG=1

# Or in .env file
DEBUG=1
```

## Contributing Guidelines

1. **Follow the existing code style**
2. **Write tests for new functionality**
3. **Update documentation**
4. **Use descriptive commit messages**
5. **Keep pull requests focused and small**
6. **Respond to review feedback promptly**

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [FSRS v4 Paper](https://github.com/open-spaced-repetition/fsrs4anki/wiki)
- [CEFR Guidelines](https://www.coe.int/en/web/common-european-framework-reference-languages)
