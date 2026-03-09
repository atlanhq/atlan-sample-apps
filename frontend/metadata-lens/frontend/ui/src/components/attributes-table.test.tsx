import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AttributesTable } from './attributes-table'
import type { AttributeEntry } from '../types/atlan'

const sampleAttributes: AttributeEntry[] = [
  { key: 'columnCount', value: 5 },
  { key: 'createTime', value: 1700000000000 },
  { key: 'description', value: 'A test table with sample data' },
  { key: 'isPartitioned', value: true },
  { key: 'name', value: 'my_table' },
  { key: 'ownerGroups', value: ['data-eng', 'analytics'] },
  { key: 'qualifiedName', value: 'db.schema.my_table' },
  { key: 'schemaConfig', value: { maxRows: 1000, timeout: 30 } },
]

describe('AttributesTable', () => {
  it('renders all attributes in a table', () => {
    render(
      <AttributesTable attributes={sampleAttributes} totalCount={12} entityTypeName="Table" />
    )

    expect(screen.getByText('Attribute')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
    expect(screen.getByText('name')).toBeInTheDocument()
    expect(screen.getByText('my_table')).toBeInTheDocument()
    expect(screen.getByText('qualifiedName')).toBeInTheDocument()
  })

  it('shows entity type name', () => {
    render(
      <AttributesTable attributes={sampleAttributes} totalCount={12} entityTypeName="Table" />
    )
    expect(screen.getByText('Table')).toBeInTheDocument()
  })

  it('shows attribute count', () => {
    render(
      <AttributesTable attributes={sampleAttributes} totalCount={12} entityTypeName="Table" />
    )
    expect(screen.getByText('8 of 12 attributes (non-null)')).toBeInTheDocument()
  })

  it('filters attributes by search query (key match)', () => {
    render(
      <AttributesTable attributes={sampleAttributes} totalCount={12} entityTypeName="Table" />
    )

    const searchInput = screen.getByPlaceholderText('Filter attributes by name or value...')
    fireEvent.change(searchInput, { target: { value: 'name' } })

    // Should show "name" and "qualifiedName"
    expect(screen.getByText('name')).toBeInTheDocument()
    expect(screen.getByText('qualifiedName')).toBeInTheDocument()
    // Should show filtered count
    expect(screen.getByText(/matching/)).toBeInTheDocument()
  })

  it('filters attributes by search query (value match)', () => {
    render(
      <AttributesTable attributes={sampleAttributes} totalCount={12} entityTypeName="Table" />
    )

    const searchInput = screen.getByPlaceholderText('Filter attributes by name or value...')
    fireEvent.change(searchInput, { target: { value: 'sample data' } })

    expect(screen.getByText('description')).toBeInTheDocument()
  })

  it('shows no results message when search has no matches', () => {
    render(
      <AttributesTable attributes={sampleAttributes} totalCount={12} entityTypeName="Table" />
    )

    const searchInput = screen.getByPlaceholderText('Filter attributes by name or value...')
    fireEvent.change(searchInput, { target: { value: 'xyznonexistent' } })

    expect(screen.getByText(/No attributes match/)).toBeInTheDocument()
  })

  it('renders boolean values as Yes/No', () => {
    render(
      <AttributesTable attributes={sampleAttributes} totalCount={12} entityTypeName="Table" />
    )
    expect(screen.getByText('Yes')).toBeInTheDocument()
  })

  it('renders arrays as comma-separated lists', () => {
    render(
      <AttributesTable attributes={sampleAttributes} totalCount={12} entityTypeName="Table" />
    )
    expect(screen.getByText('data-eng, analytics')).toBeInTheDocument()
  })

  it('renders objects as formatted JSON', () => {
    render(
      <AttributesTable attributes={sampleAttributes} totalCount={12} entityTypeName="Table" />
    )
    const jsonElement = screen.getByText(/maxRows/)
    expect(jsonElement).toBeInTheDocument()
    expect(jsonElement.tagName).toBe('PRE')
  })

  it('renders empty state when no attributes provided', () => {
    render(
      <AttributesTable attributes={[]} totalCount={0} entityTypeName="Table" />
    )
    expect(screen.getByText('No attributes found')).toBeInTheDocument()
    expect(screen.getByText('This asset has no non-null attributes.')).toBeInTheDocument()
  })

  it('renders without entity type name', () => {
    render(
      <AttributesTable attributes={sampleAttributes} totalCount={8} entityTypeName={null} />
    )
    expect(screen.queryByText('Table')).not.toBeInTheDocument()
    expect(screen.getByText('8 of 8 attributes (non-null)')).toBeInTheDocument()
  })

  it('formats epoch timestamps as readable dates', () => {
    const attrs: AttributeEntry[] = [{ key: 'createTime', value: 1700000000000 }]
    render(<AttributesTable attributes={attrs} totalCount={1} entityTypeName={null} />)
    // The formatted date should not be the raw number
    const cell = screen.getByText(new Date(1700000000000).toLocaleString())
    expect(cell).toBeInTheDocument()
  })
})
