"""
Create Harris Matrix Tool

Interactive Harris Matrix creation tool for stratigraphic data.
Allows creating and editing matrices with nodes and relationships.
"""

import logging
from typing import Dict, Any, List, Optional
from .base_tool import BaseTool, ToolDescription

logger = logging.getLogger(__name__)


class CreateHarrisMatrixTool(BaseTool):
    """Create/Edit Harris Matrix - Interactive matrix creation with nodes and relationships"""

    def __init__(self, db_session, config):
        """Initialize with db_session and config, create db_manager"""
        super().__init__(db_session, config)
        # Create db_manager from session's bind (engine)
        from pyarchinit_mini.database.manager import DatabaseManager
        from pyarchinit_mini.database.connection import DatabaseConnection
        # Get database URL from config or environment
        import os
        db_url = getattr(config, 'database_url', None) or os.getenv('DATABASE_URL', 'sqlite:///pyarchinit_mini.db')
        connection = DatabaseConnection.from_url(db_url)
        self.db_manager = DatabaseManager(connection)

    def to_tool_description(self) -> ToolDescription:
        return ToolDescription(
            name="create_harris_matrix",
            description=(
                "Create or edit Harris Matrix diagrams for stratigraphic analysis. "
                "Add nodes (US units) with properties and relationships between them. "
                "Supports Extended Matrix node types and standard stratigraphic relationships. "
                "Automatically saves to database and can optionally export to GraphML/DOT formats."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "site_name": {
                        "type": "string",
                        "description": "Archaeological site name"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["create", "edit"],
                        "description": "Mode: 'create' for new matrix, 'edit' to update existing",
                        "default": "create"
                    },
                    "nodes": {
                        "type": "array",
                        "description": "Array of US nodes to create/update",
                        "items": {
                            "type": "object",
                            "properties": {
                                "us_number": {
                                    "type": "string",
                                    "description": "US number/identifier (e.g., '1001', 'USM_5')"
                                },
                                "unit_type": {
                                    "type": "string",
                                    "description": "Node type: US, USM, USVA, USVB, USVC, TU, USD, SF, VSF, CON, DOC, etc.",
                                    "default": "US"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Stratigraphic description of the unit"
                                },
                                "area": {
                                    "type": "string",
                                    "description": "Excavation area (e.g., 'Area A', 'Sector 3')"
                                },
                                "period": {
                                    "type": "string",
                                    "description": "Archaeological period (e.g., 'Medieval', 'Roman')"
                                },
                                "phase": {
                                    "type": "string",
                                    "description": "Phase within period (e.g., 'Early', 'Late')"
                                },
                                "file_path": {
                                    "type": "string",
                                    "description": "Optional file path for documentation/photos"
                                }
                            },
                            "required": ["us_number"]
                        }
                    },
                    "relationships": {
                        "type": "array",
                        "description": "Array of stratigraphic relationships",
                        "items": {
                            "type": "object",
                            "properties": {
                                "from_us": {
                                    "type": "string",
                                    "description": "Source US number"
                                },
                                "to_us": {
                                    "type": "string",
                                    "description": "Target US number"
                                },
                                "relationship": {
                                    "type": "string",
                                    "description": "Relationship type: Covers, Covered_by, Fills, Filled_by, Cuts, Cut_by, Bonds_to, Equal_to, Leans_on, >, <, >>, <<, Continuity",
                                    "enum": [
                                        "Covers", "Covered_by", "Fills", "Filled_by",
                                        "Cuts", "Cut_by", "Bonds_to", "Equal_to",
                                        "Leans_on", "Continuity",
                                        ">", "<", ">>", "<<"
                                    ]
                                }
                            },
                            "required": ["from_us", "to_us", "relationship"]
                        }
                    },
                    "export_format": {
                        "type": "string",
                        "enum": ["none", "graphml", "dot"],
                        "description": "Export format after saving (none, graphml, or dot)",
                        "default": "none"
                    }
                },
                "required": ["site_name", "nodes"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Harris Matrix creation/editing"""
        try:
            site_name = arguments.get("site_name")
            mode = arguments.get("mode", "create")
            nodes = arguments.get("nodes", [])
            relationships = arguments.get("relationships", [])
            export_format = arguments.get("export_format", "none")

            # Validate inputs
            if not site_name:
                return self._format_error("Site name is required")

            if not nodes:
                return self._format_error("At least one node is required")

            logger.info(f"Creating Harris Matrix: site={site_name}, nodes={len(nodes)}, rels={len(relationships)}")

            # Save matrix to database
            result = self._save_matrix_to_database(
                site_name=site_name,
                nodes=nodes,
                relationships=relationships
            )

            if not result.get('success'):
                return self._format_error(result.get('message', 'Unknown error'))

            # Optional export
            export_result = None
            if export_format in ['graphml', 'dot']:
                export_result = self._export_matrix(site_name, export_format)

            # Build response
            response_data = {
                'success': True,
                'site_name': site_name,
                'nodes_created': result.get('nodes_created', 0),
                'nodes_updated': result.get('nodes_updated', 0),
                'relationships_created': result.get('relationships_created', 0),
                'relationships_updated': result.get('relationships_updated', 0),
            }

            if export_result and export_result.get('success'):
                response_data['exported_file'] = export_result.get('filepath')
                response_data['export_format'] = export_format

            message = (
                f"Successfully saved Harris Matrix for site '{site_name}': "
                f"{result.get('nodes_created', 0)} nodes created, "
                f"{result.get('nodes_updated', 0)} nodes updated, "
                f"{result.get('relationships_created', 0)} relationships created, "
                f"{result.get('relationships_updated', 0)} relationships updated"
            )

            if export_result and export_result.get('success'):
                message += f". Exported to {export_format.upper()}: {export_result.get('filepath')}"

            return self._format_success(response_data, message)

        except Exception as e:
            logger.error(f"Harris Matrix creation error: {str(e)}", exc_info=True)
            return self._format_error(f"Failed to create Harris Matrix: {str(e)}")

    def _save_matrix_to_database(
        self,
        site_name: str,
        nodes: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Save Harris Matrix nodes and relationships to database"""
        from pyarchinit_mini.models.site import Site
        from pyarchinit_mini.models.us import US
        from pyarchinit_mini.models.harris_matrix import USRelationships, Periodizzazione
        from pyarchinit_mini.services.relationship_sync_service import RelationshipSyncService

        try:
            with self.db_manager.connection.get_session() as db:
                # Get or create site
                site = db.query(Site).filter_by(sito=site_name).first()
                if not site:
                    site = Site(sito=site_name, definizione_sito='Created via MCP Harris Matrix Creator')
                    db.add(site)
                    db.flush()

                nodes_created = 0
                nodes_updated = 0

                # Save nodes
                for node_data in nodes:
                    us_number = node_data.get('us_number')
                    if not us_number:
                        continue

                    # Check if exists
                    us = db.query(US).filter_by(
                        sito=site_name,
                        us=us_number
                    ).first()

                    if us:
                        # Update existing US
                        nodes_updated += 1
                        us.unita_tipo = node_data.get('unit_type', 'US')
                        us.d_stratigrafica = node_data.get('description') or None
                        us.area = node_data.get('area') or None
                        us.periodo_iniziale = node_data.get('period') or None
                        us.fase_iniziale = node_data.get('phase') or None
                        us.file_path = node_data.get('file_path') or None
                    else:
                        # Create new US
                        nodes_created += 1
                        us_create_data = {
                            'sito': site_name,
                            'us': us_number,
                            'unita_tipo': node_data.get('unit_type', 'US'),
                            'd_stratigrafica': node_data.get('description') or None,
                            'area': node_data.get('area') or None,
                            'periodo_iniziale': node_data.get('period') or None,
                            'fase_iniziale': node_data.get('phase') or None,
                            'file_path': node_data.get('file_path') or None
                        }
                        us = self.db_manager.create(US, us_create_data)

                    # Create or update periodizzazione if period/phase specified
                    periodo = node_data.get('period', '')
                    fase = node_data.get('phase', '')

                    if periodo or fase:
                        # Create datazione_estesa
                        if periodo and fase:
                            datazione_estesa = f"{periodo} - {fase}"
                        elif periodo:
                            datazione_estesa = periodo
                        else:
                            datazione_estesa = fase

                        # Check if exists
                        periodizzazione = db.query(Periodizzazione).filter_by(
                            sito=site_name,
                            us=us_number
                        ).first()

                        if periodizzazione:
                            periodizzazione.periodo_iniziale = periodo or None
                            periodizzazione.fase_iniziale = fase or None
                            periodizzazione.datazione_estesa = datazione_estesa
                            periodizzazione.area = node_data.get('area') or None
                        else:
                            periodizzazione = Periodizzazione(
                                sito=site_name,
                                area=node_data.get('area') or None,
                                us=us_number,
                                periodo_iniziale=periodo or None,
                                fase_iniziale=fase or None,
                                datazione_estesa=datazione_estesa
                            )
                            db.add(periodizzazione)

                db.flush()

                relationships_created = 0
                relationships_updated = 0

                # Save relationships
                for rel_data in relationships:
                    from_us = rel_data.get('from_us')
                    to_us = rel_data.get('to_us')
                    rel_type = rel_data.get('relationship')

                    if not all([from_us, to_us, rel_type]):
                        continue

                    # Check if exists
                    existing_rel = db.query(USRelationships).filter_by(
                        sito=site_name,
                        us_from=from_us,
                        us_to=to_us
                    ).first()

                    if existing_rel:
                        existing_rel.relationship_type = rel_type
                        relationships_updated += 1
                    else:
                        relationship = USRelationships(
                            sito=site_name,
                            us_from=from_us,
                            us_to=to_us,
                            relationship_type=rel_type
                        )
                        db.add(relationship)
                        relationships_created += 1

                # Synchronize relationships to rapporti field
                try:
                    affected_us = set()
                    for rel in db.query(USRelationships).filter_by(sito=site_name).all():
                        affected_us.add(rel.us_from)

                    sync_service = RelationshipSyncService(self.db_manager)

                    for us_number in affected_us:
                        rapporti_text = sync_service.sync_relationships_table_to_rapporti(
                            sito=site_name,
                            us_number=us_number,
                            session=db
                        )

                        us_record = db.query(US).filter_by(sito=site_name, us=us_number).first()
                        if us_record:
                            us_record.rapporti = rapporti_text

                    db.flush()

                except Exception as sync_error:
                    logger.warning(f"Failed to sync relationships to rapporti field: {sync_error}")

                # Commit all changes
                db.commit()

                return {
                    'success': True,
                    'nodes_created': nodes_created,
                    'nodes_updated': nodes_updated,
                    'relationships_created': relationships_created,
                    'relationships_updated': relationships_updated
                }

        except Exception as e:
            logger.error(f"Database save error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Database save failed: {str(e)}'
            }

    def _export_matrix(self, site_name: str, format: str) -> Dict[str, Any]:
        """Export matrix to GraphML or DOT format"""
        from pyarchinit_mini.harris_matrix.matrix_generator import HarrisMatrixGenerator
        from pyarchinit_mini.services.us_service import USService
        from pyarchinit_mini.graphml_converter.graphml_exporter import GraphMLExporter
        import tempfile
        import os
        from datetime import datetime

        try:
            us_service = USService(self.db_manager)
            generator = HarrisMatrixGenerator(self.db_manager, us_service)

            # Generate graph
            graph = generator.generate_matrix(site_name)

            if not graph or graph.number_of_nodes() == 0:
                return {
                    'success': False,
                    'message': 'No nodes found for this site'
                }

            # Export to temp directory
            output_dir = tempfile.mkdtemp()
            base_name = site_name.replace(' ', '_').replace('/', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{base_name}_{timestamp}.{format}"
            output_path = os.path.join(output_dir, filename)

            if format == 'graphml':
                result_path = generator.export_to_graphml(
                    graph=graph,
                    output_path=output_path,
                    use_extended_labels=True,
                    site_name=site_name,
                    include_periods=True
                )
                if not result_path:
                    return {'success': False, 'message': 'GraphML export failed'}
            else:  # dot
                exporter = GraphMLExporter()
                dot_path = output_path.replace('.dot', '') + '.dot'
                exporter.export_to_dot(graph, dot_path, site_name=site_name)
                output_path = dot_path

            return {
                'success': True,
                'filepath': output_path,
                'format': format
            }

        except Exception as e:
            logger.error(f"Export error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Export failed: {str(e)}'
            }
