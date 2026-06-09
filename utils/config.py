import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve the config directory relative to this file's location
CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_config():
    env = os.getenv("ENV", "local")
    env_file = CONFIG_DIR / f".env.{env}"

    if not env_file.exists():
        raise FileNotFoundError(
            f"Config file not found: {env_file}\n"
            f"Available envs: {[f.name for f in CONFIG_DIR.glob('.env.*')]}"
        )

    load_dotenv(dotenv_path=env_file, override=True)


# Load config once at import time
load_config()


class Config:
    # Browser / Platform
    BASE_URL: str = os.getenv("BASE_URL", "https://www.ambitionbox.com")
    BROWSER: str = os.getenv("BROWSER", "chromium")
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"
    PLATFORM: str = os.getenv("PLATFORM", "web")
    SLOW_MO: int = int(os.getenv("SLOW_MO", "0"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30000"))

    # Artifacts
    SCREENSHOT_ON_FAILURE: bool = os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true"
    VIDEO_ON_FAILURE: bool = os.getenv("VIDEO_ON_FAILURE", "false").lower() == "true"

    @classmethod
    def summary(cls) -> str:
        return (
            f"ENV={os.getenv('ENV', 'local')} | "
            f"PLATFORM={cls.PLATFORM} | "
            f"BROWSER={cls.BROWSER} | "
            f"HEADLESS={cls.HEADLESS} | "
            f"BASE_URL={cls.BASE_URL}"
        )
