from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .core.health import health_router
from .observability.tracing import setup_tracing
from .logger import enrich_context
from .core.config import get_settings
from .core.db import init_db
from .integrations.notion_client import NotionClient
from .integrations.behavior_manager import BehaviorManager

from crewai import Crew
import os

def create_app() -> FastAPI:
   app = FastAPI(
       title="Chat Microservice",
       version="0.1.0"
   )

   settings = get_settings()
   enrich_context(event="app_creation_start").info("Starting app creation")

   @app.on_event("startup")
   def _init_db() -> None:
       enrich_context(event="startup_init_db_start").info("Starting database initialization")
       try:
           init_db()
           enrich_context(event="startup_init_db_success").info("Database initialization completed")
       except Exception as e:
           enrich_context(event="startup_init_db_error", error=str(e)).error("Database initialization failed")
           raise

   if settings.notion_token and settings.notion_page_id:
       enrich_context(event="notion_config_found").info("Notion configuration found")
       notion_client = NotionClient(settings.notion_token)
       behavior_manager = BehaviorManager(notion_client, settings.notion_page_id)
       app.state.behavior_manager = behavior_manager

       @app.on_event("startup")
       async def load_behavior():
           enrich_context(event="startup_behavior_start").info("Starting behavior loading")
           try:
               await behavior_manager.refresh()
               enrich_context(event="startup_behavior_success").info("Behavior loading completed")
           except Exception as e:
               enrich_context(event="startup_behavior_error", error=str(e)).error("Behavior loading failed")
               # Не падаем на этой ошибке
   else:
       enrich_context(event="notion_config_missing").info("Notion configuration not found, skipping behavior loading")

   # CrewAI YAML
   @app.on_event("startup")
   async def load_crew():
       enrich_context(event="startup_crew_start").info("Starting crew loading")
       try:
           yaml_path = os.path.join(os.path.dirname(__file__), "..", "crew-infra-cluster.yaml")
           if os.path.exists(yaml_path):
               app.state.crew = Crew.load(yaml_path)
               enrich_context(event="crew_loaded", file=yaml_path).info("Crew loaded from YAML")
               # app.state.crew.kickoff()  # автостарт агентов
           else:
               enrich_context(event="crew_file_missing", file=yaml_path).info("Crew YAML file not found, skipping")
           enrich_context(event="startup_crew_success").info("Crew loading completed")
       except Exception as e:
           enrich_context(event="startup_crew_error", error=str(e)).error("Crew loading failed")
           # Не падаем на этой ошибке

   enrich_context(event="middleware_setup_start").info("Setting up middleware")

   # CORS
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

   enrich_context(event="routes_setup_start").info("Setting up routes")

   # Роуты
   app.include_router(api_router)
   app.include_router(health_router)

   enrich_context(event="tracing_setup_start").info("Setting up tracing")

   # Трейсинг и лог старта
   setup_tracing(app)
   enrich_context(event="startup").info("Application initialized")

   @app.get("/")
   async def root():
       enrich_context(event="root_called").info("Root endpoint accessed")
       return {
           "status": "ok",
           "service": app.title,
           "version": app.version
       }

   enrich_context(event="app_creation_complete").info("App creation completed")
   return app


app = create_app()

if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)