# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2025-11-03

### Added
- **`default_visible_stages` parameter**: New Python parameter to control which stages are visible by default when the kanban board loads
  - Accepts `None` (default behavior: show all except 'rejected' and 'deleted')
  - Accepts empty list `[]` (no stages visible by default)
  - Accepts list of stage IDs `["stage1", "stage2"]` (only specified stages visible)
  - Users can still toggle any stage on/off via the "Stages (#)" filter button
  - Documentation and examples added in `example_default_visible_stages.py` and `DEFAULT_VISIBLE_STAGES.md`

### Changed
- Updated `FilterPanel.tsx` to accept and use `defaultVisibleStages` prop from Python
- Updated `StreamlitKanbanBoard.tsx` to pass `default_visible_stages` to FilterPanel
- Frontend build updated with new functionality

### Fixed
- Stage visibility now properly respects Python-side configuration on initial load

## [1.2.0] - Previous Release

### Features
- DLA V2 pre-computed permissions architecture
- Drag-and-drop functionality with role-based permissions
- Business rules engine
- Advanced filtering and sorting
- Smart search with suggestions
- Multi-currency support
- Ready-to-be-moved toggle for deals

## Installation

```bash
pip install streamlit-kanban-board-goviceversa==1.2.1
```

## Usage Example

```python
from streamlit_kanban_board_goviceversa import kanban_board

result = kanban_board(
    stages=stages,
    deals=deals,
    default_visible_stages=["initial_review", "underwriting", "approved"],
    # ... other parameters
)
```
