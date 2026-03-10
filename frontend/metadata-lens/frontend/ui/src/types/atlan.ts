export interface AtlanEntity {
  typeName: string
  attributes: EntityAttributes
  guid: string
  status: string
}

export type EntityAttributes = Record<string, unknown>

export interface EntityResponse {
  entity: AtlanEntity
}

export type AttributeEntry = {
  key: string
  value: unknown
}
