import os
from pathlib import Path
from dotenv import load_dotenv

# Load ai_agent/.env (separate from the framework's config/.env.*)
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    load_dotenv(dotenv_path=_env_file, override=True)


class AgentConfig:
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Jira
    JIRA_SERVER: str = os.getenv("JIRA_SERVER", "")
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")

    # Azure DevOps
    ADO_ORGANIZATION: str = os.getenv("ADO_ORGANIZATION", "")
    ADO_PROJECT: str = os.getenv("ADO_PROJECT", "")
    ADO_PAT: str = os.getenv("ADO_PAT", "")

    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set.\n"
                "Copy ai_agent/.env.example → ai_agent/.env and add your key."
            )

    @classmethod
    def has_jira(cls) -> bool:
        return bool(cls.JIRA_SERVER and cls.JIRA_EMAIL and cls.JIRA_API_TOKEN)

    @classmethod
    def has_ado(cls) -> bool:
        return bool(cls.ADO_ORGANIZATION and cls.ADO_PROJECT and cls.ADO_PAT)
