# 100-Day Execution Plan Dashboard

A comprehensive project execution dashboard for managing a 100-day workplan with tasks, critical paths, and visual Gantt chart representation.

## Overview

This dashboard provides three integrated working sections for end-to-end project management:

- **Section I**: Phase-by-phase progress tracker with status filters and real-time progress meters
- **Section II**: Task management interface with progress updates, notes, and activity feed
- **Section III**: Interactive Gantt chart with configurable timeline, critical path highlighting, and dependency visualization

## Features

### Task Management
- 34 sample tasks organized across 6 phases
- Full lifecycle tracking: Not Started → In Progress → Completed/At Risk
- Progress percentage tracking for each task
- Detailed notes and activity logging
- Predecessor dependency tracking

### Critical Path Analysis
- Automatic critical path calculation using forward/backward pass algorithm
- Visual highlighting of critical tasks in the Gantt chart
- Slack time calculation for all tasks
- Project completion timeline: 100 days

### Phase Organization
- **Phase 1**: Foundation & Planning (Days 1-15)
- **Phase 2**: Design & Requirements (Days 12-30)
- **Phase 3**: Development & Build (Days 28-65)
- **Phase 4**: Testing & QA (Days 54-75)
- **Phase 5**: Deployment & Rollout (Days 73-90)
- **Phase 6**: Operations & Optimization (Days 85-100)

### Data Persistence
- Hybrid backend support:
   - Google Sheets (shared team source of truth)
   - SQLite fallback (`plan_data.db`) when Sheets is not configured
- Task updates include user attribution and activity logs
- JSON/CSV export for board-ready reporting and backups

## Quick Start

### Run Team Dashboard (Streamlit)

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Run app:
   - `streamlit run streamlit_app.py`
3. Open browser URL shown by Streamlit (usually `http://localhost:8501`)
4. Enter your name in sidebar and start updating tasks

### Enable Google Sheets Backend (Hybrid Mode)

Set these before running (or in Streamlit Cloud secrets):
- `USE_GOOGLE_SHEETS=true`
- `GOOGLE_SHEET_ID=<sheet-id>`
- `gcp_service_account` (service account JSON in Streamlit secrets)

If Google Sheets is unavailable, app automatically falls back to SQLite.

### Static HTML Dashboard (Optional)

For read-only/simple local usage:
- Open `index.html` in browser
- Data is browser-local for static mode

### Data Management

**Export Plan Data** (JSON)
- Saves all task data, status, completion %, and activity log
- Use to create backups or share with team

**Import Plan Data** (JSON)
- Restore from previously exported file
- Useful for loading team updates

**Export CSV Report**
- Board-ready tabular format with all task details
- Includes predecessors and criticality markers

**Print Summary**
- Optimized print layout of current dashboard state
- Best viewed in landscape orientation

**Reset Sample Data**
- Clears all local storage and reloads original plan
- Useful for demo/training purposes

## Data Structure

### Tasks
Each task contains:
- `id`: Unique identifier
- `name`: Task description
- `phase`: Phase ID the task belongs to
- `startDay`: 1-based day number (1-100)
- `duration`: Task length in days
- `status`: Not Started | In Progress | Completed | At Risk
- `percentComplete`: 0-100% completion
- `predecessors`: Array of task IDs that must complete first
- `criticality`: "critical" or "normal"

### Phases
Phases organize tasks into logical segments with:
- `id`: Phase identifier
- `name`: Phase description
- `order`: Sequence in project

## Storage Notes

- Streamlit app uses hybrid storage through `data_backend.py`.
- Shared mode: Google Sheets tabs (`phases`, `tasks`, `milestones`, `task_updates`, `activity_log`).
- Fallback mode: local `plan_data.db` (SQLite).
- Static HTML mode still uses browser local storage.

## Critical Path Calculation

The dashboard automatically calculates critical path using:

1. **Forward Pass**: Compute earliest start/finish times
2. **Backward Pass**: Compute latest start/finish times
3. **Slack Analysis**: Tasks with zero slack are critical
4. **Path Identification**: Connected critical tasks form the critical path

Tasks on the critical path directly impact overall project completion date (Day 100). Delays to critical tasks delay the entire project.

## Customization

To customize the 100-day plan for your project:

1. Open `app.js` in a text editor
2. Modify `sampleData.phases` to define your phases
3. Modify `sampleData.tasks` with your tasks:
   - Update task names, durations, and start days
   - Set correct predecessor relationships (by task ID)
   - Mark critical tasks with `criticality: 'critical'`
   - Save changes and refresh browser

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Requires JavaScript enabled
- No external dependencies required

## Tips

- **Color Coding**: Bars show task status (green=completed, blue=in progress, gray=not started, orange=at risk)
- **Highlighting**: Tasks on critical path have yellow borders in Gantt
- **Activity Feed**: Recent 50 updates shown; oldest entries removed when capacity exceeded
- **Print**: Best printed in landscape mode for Gantt visibility
- **Mobile**: Phase tracker responsive; Gantt chart best on desktop

## Support

For issues or modifications, examine:
- `index.html`: Dashboard HTML structure
- `app.js`: Core logic, data management, calculations
- `styles.css`: Visual styling and layout

## Version

100-Day Plan Dashboard v1.0 - April 2026

---

**Last Updated**: April 17, 2026
