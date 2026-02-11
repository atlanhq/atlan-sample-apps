"""
Transformer for Starburst Enterprise (SEP) metadata.

Maps raw metadata from both REST API and SQL extraction into Atlan entity format.
Covers all SEP object types: Domain, DataProduct, Dataset, DatasetColumn,
Catalog, Schema, Table, View, Column.
"""

from typing import Any, Dict, Optional, Type

from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.transformers.atlas import AtlasTransformer
from application_sdk.transformers.common.utils import build_atlas_qualified_name

logger = get_logger(__name__)


# ─── REST API Object Types ─────────────────────────────────────────────


class SEPDomain:
    """Starburst Enterprise Domain entity."""

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        attributes = {
            "name": obj.get("name", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""),
                obj.get("name", ""),
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
            "description": obj.get("description", ""),
            "schemaLocationUri": obj.get("schemaLocation", ""),
        }
        custom_attributes = {
            "type": obj.get("type", ""),
        }
        return {"attributes": attributes, "custom_attributes": custom_attributes}


class SEPDataProduct:
    """Starburst Enterprise Data Product entity.

    A Data Product maps 1:1 to a schema in the catalog.
    """

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        # Build owners list as serializable value
        owners = obj.get("owners", [])
        owners_value = [
            {"name": o.get("name", ""), "email": o.get("email", "")}
            for o in owners
        ] if owners else []

        attributes = {
            "name": obj.get("name", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""),
                obj.get("catalogName", ""),
                obj.get("schemaName", obj.get("name", "")),
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
            "summary": obj.get("summary", ""),
            "description": obj.get("description", ""),
            "catalogName": obj.get("catalogName", ""),
            "schemaName": obj.get("schemaName", ""),
            "status": obj.get("status", ""),
            "domainId": obj.get("dataDomainId", ""),
            "domainName": obj.get("domainName", ""),
            "owners": owners_value,
            "publishedAt": obj.get("publishedAt", ""),
            "publishedBy": obj.get("publishedBy", ""),
        }
        # Extract access metadata
        access_metadata = obj.get("accessMetadata", {})
        custom_attributes = {
            "visibility": obj.get("type", obj.get("visibility", "")),
            "lastQueriedAt": access_metadata.get("lastQueriedAt", ""),
            "lastQueriedBy": access_metadata.get("lastQueriedBy", ""),
        }
        return {"attributes": attributes, "custom_attributes": custom_attributes}


class SEPDataset:
    """Starburst Enterprise Dataset entity (view or materialized view within a Data Product)."""

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        attributes = {
            "name": obj.get("dataset_name", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""),
                obj.get("catalog_name", ""),
                obj.get("schema_name", ""),
                obj.get("dataset_name", ""),
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
            "description": obj.get("dataset_description", ""),
            "viewDefinition": obj.get("view_definition", ""),
            "schemaName": obj.get("schema_name", ""),
            "databaseName": obj.get("catalog_name", ""),
            "dataProductName": obj.get("data_product_name", ""),
            "status": obj.get("status", ""),
        }
        # Build custom attributes including MV-specific fields
        definition_props = obj.get("definition_properties", {})
        custom_attributes = {
            "is_materialized": obj.get("is_materialized", False),
            "viewSecurityMode": obj.get("view_security_mode", ""),
            "refreshSchedule": definition_props.get("refresh_schedule", ""),
            "refreshScheduleTimezone": definition_props.get(
                "refresh_schedule_timezone", ""
            ),
        }
        return {"attributes": attributes, "custom_attributes": custom_attributes}


class SEPDatasetColumn:
    """Starburst Enterprise Dataset Column entity (from Data Product REST API)."""

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        attributes = {
            "name": obj.get("column_name", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""),
                obj.get("catalog_name", ""),
                obj.get("schema_name", ""),
                obj.get("dataset_name", ""),
                obj.get("column_name", ""),
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
            "dataType": obj.get("data_type", ""),
            "description": obj.get("description", ""),
            "tableName": obj.get("dataset_name", ""),
            "schemaName": obj.get("schema_name", ""),
            "databaseName": obj.get("catalog_name", ""),
        }
        return {"attributes": attributes, "custom_attributes": {}}


# ─── SQL Object Types ──────────────────────────────────────────────────


class SEPCatalog:
    """Starburst Enterprise Catalog entity (from SQL system.metadata.catalogs)."""

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        attributes = {
            "name": obj.get("catalog_name", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""),
                obj.get("catalog_name", ""),
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
        }
        custom_attributes = {
            "connector_id": obj.get("connector_id", ""),
            "connector_name": obj.get("connector_name", ""),
            "state": obj.get("state", ""),
        }
        return {"attributes": attributes, "custom_attributes": custom_attributes}


class SEPSchema:
    """Starburst Enterprise Schema entity (from SQL INFORMATION_SCHEMA)."""

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        attributes = {
            "name": obj.get("schema_name", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""),
                obj.get("catalog_name", ""),
                obj.get("schema_name", ""),
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
            "databaseName": obj.get("catalog_name", ""),
        }
        return {"attributes": attributes, "custom_attributes": {}}


class SEPTable:
    """Starburst Enterprise Table entity (from SQL INFORMATION_SCHEMA)."""

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        attributes = {
            "name": obj.get("table_name", ""),
            "qualifiedName": build_atlas_qualified_name(
                obj.get("connection_qualified_name", ""),
                obj.get("table_catalog", ""),
                obj.get("table_schema", ""),
                obj.get("table_name", ""),
            ),
            "connectionQualifiedName": obj.get("connection_qualified_name", ""),
            "schemaName": obj.get("table_schema", ""),
            "databaseName": obj.get("table_catalog", ""),
        }
        custom_attributes = {
            "table_type": obj.get("table_type", "TABLE"),
        }
        return {"attributes": attributes, "custom_attributes": custom_attributes}


class SEPColumn:
    """Starburst Enterprise Column entity (from SQL INFORMATION_SCHEMA)."""

    @classmethod
    def get_attributes(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
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
            "isNullable": obj.get("is_nullable", "YES") == "YES",
            "dataType": obj.get("data_type", ""),
            "description": obj.get("comment", "") or "",
            "order": obj.get("ordinal_position", 1),
        }
        custom_attributes = {
            "column_default": obj.get("column_default", ""),
        }
        return {"attributes": attributes, "custom_attributes": custom_attributes}


# ─── Transformer ───────────────────────────────────────────────────────


class SEPAtlasTransformer(AtlasTransformer):
    """Atlas transformer for Starburst Enterprise metadata.

    Registers entity class definitions for all SEP object types from
    both REST API and SQL extraction streams.
    """

    def __init__(self, connector_name: str, tenant_id: str, **kwargs: Any):
        super().__init__(connector_name, tenant_id, **kwargs)

        # REST API object types
        self.entity_class_definitions["DOMAIN"] = SEPDomain
        self.entity_class_definitions["DATA_PRODUCT"] = SEPDataProduct
        self.entity_class_definitions["DATASET"] = SEPDataset
        self.entity_class_definitions["DATASET_COLUMN"] = SEPDatasetColumn

        # SQL object types
        self.entity_class_definitions["CATALOG"] = SEPCatalog
        self.entity_class_definitions["SCHEMA"] = SEPSchema
        self.entity_class_definitions["TABLE"] = SEPTable
        self.entity_class_definitions["COLUMN"] = SEPColumn

    def transform_row(
        self,
        typename: str,
        data: Dict[str, Any],
        workflow_id: str,
        workflow_run_id: str,
        entity_class_definitions: Dict[str, Type[Any]] | None = None,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
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
                enriched_data = self._enrich_entity_with_metadata(
                    workflow_id, workflow_run_id, data
                )

                entity_attributes["attributes"].update(enriched_data["attributes"])
                entity_attributes["custom_attributes"].update(
                    enriched_data["custom_attributes"]
                )

                return {
                    "typeName": typename,
                    "attributes": entity_attributes["attributes"],
                    "customAttributes": entity_attributes["custom_attributes"],
                    "status": "ACTIVE",
                }
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
