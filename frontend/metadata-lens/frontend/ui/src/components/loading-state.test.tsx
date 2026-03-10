import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingState } from './loading-state'

describe('LoadingState', () => {
  it('renders initializing state', () => {
    render(<LoadingState authStatus="initializing" metadataLoading={false} error={null} />)
    expect(screen.getByText('Connecting to Atlan')).toBeInTheDocument()
    expect(screen.getByText('Initializing authentication...')).toBeInTheDocument()
  })

  it('renders error state', () => {
    render(<LoadingState authStatus="error" metadataLoading={false} error="Something broke" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Something broke')).toBeInTheDocument()
  })

  it('renders metadata loading state', () => {
    render(<LoadingState authStatus="authenticated" metadataLoading={true} error={null} />)
    expect(screen.getByText('Loading metadata')).toBeInTheDocument()
    expect(screen.getByText('Fetching asset attributes...')).toBeInTheDocument()
  })

  it('renders logged out state', () => {
    render(<LoadingState authStatus="logged_out" metadataLoading={false} error={null} />)
    expect(screen.getByText('Logged out')).toBeInTheDocument()
    expect(screen.getByText('Your session has ended. Please log in again.')).toBeInTheDocument()
  })

  it('renders nothing when authenticated and not loading', () => {
    const { container } = render(
      <LoadingState authStatus="authenticated" metadataLoading={false} error={null} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('prioritizes error over other states', () => {
    render(<LoadingState authStatus="initializing" metadataLoading={true} error="Error message" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Error message')).toBeInTheDocument()
    expect(screen.queryByText('Connecting to Atlan')).not.toBeInTheDocument()
  })
})
