# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend Development
From `/plugins/baserow_vocabai_plugin/backend/`:
- `make lint` - Run linting (flake8, black, bandit)
- `make format` - Format code with black
- `make test` - Run tests
- `make test-parallel` - Run tests in parallel

### Frontend Development
From `/plugins/baserow_vocabai_plugin/web-frontend/`:
- `yarn eslint` - Lint JavaScript/Vue files
- `yarn stylelint` - Lint SCSS files  
- `yarn lint` - Run all linters
- `yarn dev` - Start development server
- `yarn build` - Build for production
- `yarn start` - Start production server

### Docker Development
```bash
# Set required environment variables first
source env.dev.sh
source ~/secrets/cloudlanguagetools/cloudlanguagetools_core_secret.sh
source ~/secrets/vocabai/dev.sh

# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# View logs
docker logs --since 1h -f baserow-vocabai-plugin

# Run backend tests in container
docker compose -f docker-compose.dev.yml exec baserow-vocabai-plugin /baserow.sh backend-cmd bash -c "pytest baserow/data/plugins/baserow_vocabai_plugin/backend/tests"

# Run tests with real CloudLanguageTools services
CLOUDLANGUAGETOOLS_CORE_TEST_SERVICES=yes pytest baserow_vocabai_plugin/cloudlanguagetools/test_clt.py
```

## Architecture

This is a Baserow plugin that extends the platform with AI-powered language learning features. The plugin follows Baserow's plugin architecture and consists of:

### Backend (Django/Python)
- **Custom Field Types**: Located in `/plugins/baserow_vocabai_plugin/backend/src/baserow_vocabai_plugin/fields/`
  - Translation fields - Automatic translation between languages
  - Transliteration fields - Converting between writing systems
  - Dictionary fields - Word definitions lookup
  - Chinese romanization - Pinyin/Jyutping conversion
  - Language text fields - Text with language metadata

- **CloudLanguageTools Integration**: `/plugins/baserow_vocabai_plugin/backend/src/baserow_vocabai_plugin/cloudlanguagetools/`
  - Provides AI language services
  - Handles API authentication and requests
  - Supports async processing via Celery

- **API Layer**: `/plugins/baserow_vocabai_plugin/backend/src/baserow_vocabai_plugin/api/`
  - RESTful endpoints for field operations
  - Integrates with Baserow's API framework

### Frontend (Vue.js/Nuxt)
- **Field Components**: `/plugins/baserow_vocabai_plugin/web-frontend/modules/baserow-vocabai-plugin/components/`
  - Vue components for each custom field type
  - Handles field rendering and editing UI
  
- **Services**: `/plugins/baserow_vocabai_plugin/web-frontend/modules/baserow-vocabai-plugin/services/`
  - API client for backend communication
  - Field dependency management

### Key Concepts
- **Field Dependencies**: Translation/transformation fields depend on source fields
- **Async Processing**: Language operations are processed via Celery workers
- **Baserow Integration**: Plugin extends Baserow's field registry and follows its patterns
- **Version Compatibility**: Check `baserow_clt_versions.sh` for compatible Baserow versions

## Testing

- Backend tests use pytest with Django test utilities from Baserow
- Tests can run with mocked or real CloudLanguageTools services
- Frontend uses Jest and Vue Test Utils
- Always run linting before committing: `make lint` (backend) and `yarn lint` (frontend)

## Deployment

The plugin supports multiple deployment modes via different docker-compose files:
- `docker-compose.yml` - Simple single container
- `docker-compose.dev.yml` - Development with hot reloading
- `docker-compose.multi-service.yml` - Production with separate services