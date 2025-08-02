from typing import Optional, Dict, Any
import yaml
from pydantic import ValidationError

from app.logger import enrich_context
from app.behavior import BehaviorDefinition

class BehaviorManager:
    """Loads and stores agent behavior from Notion."""

    def __init__(self, notion_client, page_id: str):
        self.notion_client = notion_client
        self.page_id = page_id
        self.behavior: Optional[BehaviorDefinition] = None

    async def refresh(self) -> None:
        log = enrich_context(event="behavior_refresh", page_id=self.page_id)
        data = await self.notion_client.fetch_page(self.page_id)
        log.info("Behavior page retrieved")
        
        try:
            # Expect first child to be a code block with YAML
            for block in data.get("results", []):
                if block.get("type") == "code":
                    text = block["code"].get("rich_text", [])
                    content = "".join(t.get("plain_text", "") for t in text)
                    raw: Dict[str, Any] = yaml.safe_load(content) or {}
                    self.behavior = BehaviorDefinition.model_validate(raw)
                    
                    # Правильная типизация для логирования
                    behavior_dict = self.behavior.model_dump()
                    log.bind(event="behavior_parsed").debug(f"Parsed behavior: {behavior_dict}")
                    log.bind(event="behavior_loaded").info("Behavior updated")
                    return
            log.bind(event="behavior_not_found").warning("No YAML code block found")
        except ValidationError as e:
            log.bind(event="behavior_validation_error", errors=str(e.errors())).error("Behavior validation failed")
            raise
        except Exception as e:
            log.bind(event="behavior_parse_error", error=str(e)).error("Failed to parse behavior")
            raise