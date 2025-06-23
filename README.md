# Blogger CRM Backend

This project is the backend for the Blogger CRM application, built using FastAPI, Supabase, and OpenAI.

## Features

- Real-time communication through a single WebSocket connection.
- Integration with Supabase for database operations.
- Interaction with OpenAI Assistants for chat and parsing.

## Setup

1. Ensure you have Python and Poetry installed.
2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```
3. Set up your environment variables in the `.env` file.

## Running the Application

To run the application, use the following command:

```bash
poetry run uvicorn src.main:app --reload
```

## License

This project is licensed under the MIT License.
