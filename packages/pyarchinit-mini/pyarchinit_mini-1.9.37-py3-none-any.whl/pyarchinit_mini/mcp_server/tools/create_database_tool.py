"""
Create Database Tool

Creates empty PyArchInit-Mini databases with full schema.
Supports both SQLite and PostgreSQL databases.
"""

import logging
from typing import Dict, Any
from .base_tool import BaseTool, ToolDescription

logger = logging.getLogger(__name__)


class CreateDatabaseTool(BaseTool):
    """Create Database - Creates empty PyArchInit-Mini database with schema"""

    def to_tool_description(self) -> ToolDescription:
        return ToolDescription(
            name="create_database",
            description=(
                "Create an empty PyArchInit-Mini database with full schema. "
                "Supports SQLite and PostgreSQL. Creates all necessary tables "
                "for sites, stratigraphic units, inventories, relationships, etc."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "db_type": {
                        "type": "string",
                        "enum": ["sqlite", "postgresql"],
                        "description": "Database type: sqlite or postgresql"
                    },
                    "db_path": {
                        "type": "string",
                        "description": "For SQLite: file path (e.g., 'data/new_project.db'). For PostgreSQL: database name"
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "If true, overwrite existing database. Default: false",
                        "default": False
                    },
                    "postgres_config": {
                        "type": "object",
                        "description": "PostgreSQL connection configuration (required for postgresql)",
                        "properties": {
                            "host": {"type": "string", "description": "PostgreSQL host", "default": "localhost"},
                            "port": {"type": "integer", "description": "PostgreSQL port", "default": 5432},
                            "user": {"type": "string", "description": "PostgreSQL user"},
                            "password": {"type": "string", "description": "PostgreSQL password"},
                        }
                    }
                },
                "required": ["db_type", "db_path"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database creation"""
        try:
            db_type = arguments.get("db_type")
            db_path = arguments.get("db_path")
            overwrite = arguments.get("overwrite", False)
            postgres_config = arguments.get("postgres_config", {})

            if not db_type or not db_path:
                return self._format_error("Both db_type and db_path are required")

            logger.info(f"Creating {db_type} database: {db_path}")

            if db_type == "sqlite":
                result = self._create_sqlite(db_path, overwrite)
            elif db_type == "postgresql":
                result = self._create_postgresql(db_path, postgres_config, overwrite)
            else:
                return self._format_error(f"Invalid db_type: {db_type}")

            if result.get('success'):
                return self._format_success(result, f"Successfully created {db_type} database with {result.get('tables_created', 0)} tables")
            else:
                return self._format_error(result.get('message', 'Database creation failed'))

        except Exception as e:
            logger.error(f"Database creation error: {str(e)}", exc_info=True)
            return self._format_error(f"Failed to create database: {str(e)}")

    def _create_sqlite(self, db_path: str, overwrite: bool) -> Dict[str, Any]:
        """Create SQLite database"""
        from pyarchinit_mini.database.database_creator import create_sqlite_database
        try:
            return create_sqlite_database(db_path, overwrite=overwrite)
        except FileExistsError as e:
            return {'success': False, 'message': f'Database already exists: {db_path}. Set overwrite=true to replace it.'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def _create_postgresql(self, db_name: str, config: Dict[str, Any], overwrite: bool) -> Dict[str, Any]:
        """Create PostgreSQL database"""
        from pyarchinit_mini.database.database_creator import create_postgresql_database
        try:
            host = config.get('host', 'localhost')
            port = config.get('port', 5432)
            user = config.get('user')
            password = config.get('password')

            if not user:
                return {'success': False, 'message': 'PostgreSQL user is required in postgres_config'}

            return create_postgresql_database(
                db_name=db_name,
                host=host,
                port=port,
                user=user,
                password=password,
                overwrite=overwrite
            )
        except Exception as e:
            return {'success': False, 'message': str(e)}
