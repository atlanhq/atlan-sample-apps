"""
This file contains the transformer for the SQL metadata extraction application.
The transformer is responsible for transforming the raw metadata into the Atlan Type.

Read More: ./models/README.md
"""

from typing import Any, Dict, Optional, Type

from application_sdk.common.logger_adaptors import get_logger
from application_sdk.transformers.atlas import AtlasTransformer
from application_sdk.transformers.common.utils import build_atlas_qualified_name

logger = get_logger(__name__)


class MySQLDatabase:
    """Represents a MySQL database entity in Atlan.

    This class handles the transformation of MySQL database metadata into Atlan entity format.
    """

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Transform MySQL database metadata into Atlan entity attributes.

        Args:
            obj: Dictionary containing the raw MySQL database metadata.

        Returns:
            Dict[str, Any]: Dictionary containing the transformed attributes and custom attributes.
        """
        attributes = {
            "name": obj.get("database_name", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""), obj.get("database_name", "")
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
        }
        return {
            "attributes": attributes,
            "custom_attributes": {},
        }


class MySQLSchema:
    """Represents a MySQL schema entity in Atlan.

    This class handles the transformation of MySQL schema metadata into Atlan entity format.
    """

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Transform MySQL schema metadata into Atlan entity attributes.

        Args:
            obj: Dictionary containing the raw MySQL schema metadata.

        Returns:
            Dict[str, Any]: Dictionary containing the transformed attributes and custom attributes.
        """
        attributes = {
            "name": obj.get("schema_name", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""),
                obj.get("catalog_name", ""),
                obj.get("schema_name", ""),
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
            "databaseName": obj.get("catalog_name", ""),
            "tableCount": obj.get("table_count", 0),
            "viewCount": obj.get("table_count", 0),
        }
        return {
            "attributes": attributes,
            "custom_attributes": {},
        }


class MySQLTable:
    """Represents a MySQL table entity in Atlan.

    This class handles the transformation of MySQL table metadata into Atlan entity format.
    """

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Transform MySQL table metadata into Atlan entity attributes.

        Args:
            obj: Dictionary containing the raw MySQL table metadata.

        Returns:
            Dict[str, Any]: Dictionary containing the transformed attributes and custom attributes.
        """
        attributes = {
            "name": obj.get("table_name", ""),
            "schemaName": obj.get("table_schema", ""),
            "databaseName": obj.get("table_catalog", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""),
                obj.get("table_catalog", ""),
                obj.get("table_schema", ""),
                obj.get("table_name", ""),
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
        }
        return {
            "attributes": attributes,
            "custom_attributes": {
                "isPartitioned": obj.get("is_partitioned", "NO") == "YES",
            },
        }


class MySQLColumn:
    """Represents a MySQL column entity in Atlan.

    This class handles the transformation of MySQL column metadata into Atlan entity format.
    """

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Transform MySQL column metadata into Atlan entity attributes.

        Args:
            obj: Dictionary containing the raw MySQL column metadata.

        Returns:
            Dict[str, Any]: Dictionary containing the transformed attributes and custom attributes.
        """
        attributes = {
            "name": obj.get("column_name", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""),
                obj.get("table_catalog", ""),
                obj.get("table_schema", ""),
                obj.get("table_name", ""),
                obj.get("column_name", ""),
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
            "tableName": obj.get("table_name", ""),
            "schemaName": obj.get("table_schema", ""),
            "databaseName": obj.get("table_catalog", ""),
            "isNullable": obj.get("is_nullable", "NO") == "YES",
            "dataType": obj.get("data_type", ""),
            "order": obj.get("ordinal_position", 1),
        }

        custom_attributes = {
            "is_autoincrement": obj.get("is_autoincrement", "NO"),
        }

        return {
            "attributes": attributes,
            "custom_attributes": custom_attributes,
        }


class SQLAtlasTransformer(AtlasTransformer):
    def __init__(self, connector_name: str, tenant_id: str, **kwargs: Any):
        super().__init__(connector_name, tenant_id, **kwargs)

        self.entity_class_definitions["DATABASE"] = MySQLDatabase
        self.entity_class_definitions["SCHEMA"] = MySQLSchema
        self.entity_class_definitions["TABLE"] = MySQLTable
        self.entity_class_definitions["COLUMN"] = MySQLColumn

    def transform_metadata(
        self,
        typename: str,
        data: Dict[str, Any],
        workflow_id: str,
        workflow_run_id: str,
        entity_class_definitions: Dict[str, Type[Any]] | None = None,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Transform metadata into an Atlas entity.

        This method transforms the provided metadata into an Atlas entity based on
        the specified type. It also enriches the entity with workflow metadata.

        Args:
            typename (str): Type of the entity to create.
            data (Dict[str, Any]): Metadata to transform.
            workflow_id (str): ID of the workflow.
            workflow_run_id (str): ID of the workflow run.
            entity_class_definitions (Dict[str, Type[Any]], optional): Custom entity
                class definitions. Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
            Optional[Dict[str, Any]]: The transformed entity as a dictionary, or None
                if transformation fails.

        Raises:
            Exception: If there's an error during entity deserialization.
        """
        typename = typename.upper()
        self.entity_class_definitions = (
            entity_class_definitions or self.entity_class_definitions
        )

        connection_qualified_name = kwargs.get("connection_qualified_name", None)
        connection_name = kwargs.get("connection_name", None)

        data.update(
            {
                "connection_qualified_name": connection_qualified_name,
                "connection_name": connection_name,
            }
        )

        creator = self.entity_class_definitions.get(typename)
        if creator:
            try:
                entity_attributes = creator.get_attributes(data)
                # enrich the entity with workflow metadata
                enriched_data = self._enrich_entity_with_metadata(
                    workflow_id, workflow_run_id, data
                )

                entity_attributes["attributes"].update(enriched_data["attributes"])
                entity_attributes["custom_attributes"].update(
                    enriched_data["custom_attributes"]
                )

                entity = {
                    "typeName": typename,
                    "attributes": entity_attributes["attributes"],
                    "customAttributes": entity_attributes["custom_attributes"],
                    "status": "ACTIVE",
                }

                return entity
            except Exception as e:
                logger.error(
                    "Error transforming {} entity: {}",
                    typename,
                    str(e),
                    extra={"data": data},
                )
                return None
        else:
            logger.error(f"Unknown typename: {typename}")
            return None
