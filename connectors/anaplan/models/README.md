# Models Directory

This directory contains the Atlan type definitions (typedefs) that serve as contracts for data transformation. These JSON files define the structure and attributes of various Atlan entities like anaplan apps, anaplan pages, etc.

## Purpose

The models directory serves as a contract layer between raw data and Atlan's data model. Each JSON file represents an Atlan entity type definition that:

1. Defines the structure of entities in Atlan
2. Specifies required and optional attributes
3. Establishes relationships between different entities
4. Serves as a reference for implementing transformers

## Sample Contracts

The directory includes sample contracts for common anaplan entities:

- `anaplanapp.json`: Defines the AnaplanApp entity type and it's super type
- `anaplanpage.json`: Defines the AnaplanPage entity type with attributes like `anaplanAppQualifiedName`

These contracts are used by the transformer (`transformer.py`) to map raw data into Atlan's expected format.

## Implementation

The transformer (`transformer.py`) implements these contracts through classes like:
- `App`
- `Page`

Each class maps raw data to the corresponding Atlan entity type defined in these contracts.

## Atlan Type References

For detailed information about each entity type, refer to the official Atlan documentation:

- [Anaplan Models Overview](https://developer.atlan.com/models/anaplan/)
- [AnaplanApp Entity](https://developer.atlan.com/models/entities/anaplanapp/)
- [AnaplanPage Entity](https://developer.atlan.com/models/entities/anaplanpage/)

## Additional Resources

- [Atlan Python SDK](https://github.com/atlanhq/atlan-python/tree/main): Provides a rich collection of Atlan types and utilities for working with Atlan entities.