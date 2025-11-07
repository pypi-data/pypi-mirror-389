"""Constants used throughout the Gitizi CLI"""

# Error messages
class ERRORS:
    NOT_AUTHENTICATED = "❌ Not authenticated. Please run: izi auth"
    AUTHENTICATION_FAILED = "Authentication failed"
    SEARCH_FAILED = "Search failed"
    CLONE_FAILED = "Clone failed"
    PUSH_FAILED = "Push failed"
    UPDATE_FAILED = "Update failed"
    TOKEN_EMPTY = "Token cannot be empty"
    NAME_REQUIRED = "Name is required"
    DESCRIPTION_REQUIRED = "Description is required"
    NAME_TOO_LONG = "Name must be 100 characters or less"
    DESCRIPTION_TOO_LONG = "Description must be 500 characters or less"
    CONTENT_TOO_LARGE = "Content must be 100KB or less"

    @staticmethod
    def FILE_NOT_FOUND(file: str) -> str:
        return f"❌ File not found: {file}"

    @staticmethod
    def INVALID_FILE_EXTENSION(file: str) -> str:
        return f"Invalid file extension. Expected .md, got: {file}"


# URLs
class URLS:
    BASE_URL = "https://gitizi.com/api"
    TOKEN_SETTINGS = "https://gitizi.com/settings/tokens"

    @staticmethod
    def PROMPTS(id: str) -> str:
        return f"https://gitizi.com/prompts/{id}"


# Supabase configuration
class SUPABASE:
    URL = "https://sewwdxmqorokboxzpsxu.supabase.co"
    ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNld3dkeG1xb3Jva2JveHpwc3h1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg5NDU4NTcsImV4cCI6MjA1NDUyMTg1N30.I0BElLPrcNKBIHDlhPAjZl5eRmEWqNnYEeJqrGbgAHc"


# Success messages
class MESSAGES:
    USING_EXISTING_AUTH = "✓ Using existing authentication"
    AUTH_SUCCESS = "Authentication successful!"
    PROMPT_PUSHED = "Prompt pushed successfully!"
    PROMPT_UPDATED = "Prompt updated successfully!"
    PROMPT_CLONED = "Prompt cloned successfully!"
    TOKEN_SAVED = "\nYour token has been saved securely."
    NO_PROMPTS_FOUND = "\nNo prompts found matching your query."
    REAUTH_PROMPT = "You are already authenticated. Do you want to re-authenticate?"

    @staticmethod
    def WELCOME(username: str) -> str:
        return f"Welcome, {username}! 🎉"


# Tips
class TIPS:
    CLONE_GENERAL = '💡 Tip: Use "izi clone <prompt-id>" to download a prompt'

    @staticmethod
    def CLONE(id: str) -> str:
        return f"💡 Share your prompt or clone it with: izi clone {id}"

    @staticmethod
    def PUSH(file: str) -> str:
        return f'💡 Use "izi push {file}" to upload this prompt to gitizi.com'

    @staticmethod
    def PUSH_UPDATE(output: str, id: str) -> str:
        return f"💡 Edit the prompt and push changes with: izi push {output} --id {id}"

    @staticmethod
    def GET_TOKEN() -> list:
        return [
            "\nTo get your API token:",
            "1. Visit https://gitizi.com/settings/tokens",
            "2. Generate a new token",
            "3. Run: izi auth --token YOUR_TOKEN",
        ]


# Limits
class LIMITS:
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500
    MAX_CONTENT_SIZE = 100 * 1024  # 100KB
    MAX_TAG_LENGTH = 30
    MAX_TAGS_COUNT = 10
    DEFAULT_SEARCH_LIMIT = 10
    API_TIMEOUT = 30  # 30 seconds
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1  # 1 second


# ASCII Art
CAT_ASCII = r"""
   /\_/\
  ( o.o )
   > ^ <
"""
