"""
Configurazione centralizzata — carica tutto da .env
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent


@dataclass
class Settings:
    # === Anthropic ===
    ANTHROPIC_API_KEY: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    CLAUDE_MODEL: str = field(default_factory=lambda: os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"))
    MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "4096")))
    TEMPERATURE: float = field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.0")))

    # === Telegram ===
    TELEGRAM_BOT_TOKEN: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    TELEGRAM_CHAT_ID: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))

    # === Agent ===
    AGENT_MAX_ITERATIONS: int = field(default_factory=lambda: int(os.getenv("AGENT_MAX_ITERATIONS", "10")))

    # === Percorsi ===
    DATA_INPUT_PATH: Path = field(default_factory=lambda: BASE_DIR / "data" / "input")
    DATA_OUTPUT_PATH: Path = field(default_factory=lambda: BASE_DIR / "data" / "output")

    def __post_init__(self):
        # Crea cartelle output se non esistono
        self.DATA_INPUT_PATH.mkdir(parents=True, exist_ok=True)
        self.DATA_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    def validate(self):
        errors = []
        if not self.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY mancante")
        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN mancante")
        if not self.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID mancante")
        if errors:
            raise ValueError(f"❌ Configurazione incompleta:\n" + "\n".join(f"  - {e}" for e in errors))


settings = Settings()
