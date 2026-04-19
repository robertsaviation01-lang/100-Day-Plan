const app = {
    // Sample 100-day plan data structure
    sampleData: {
        phases: [
            { id: 'phase1', name: 'SPV Activation & Treasury Setup (Day 0-20)', order: 1 },
            { id: 'phase2', name: 'Intercompany Loan Execution (Day 15-35)', order: 2 },
            { id: 'phase3', name: 'Demonstrator Acquisition & PMI (Day 30-70)', order: 3 },
            { id: 'phase4', name: 'BEST Procurement & Engineering (Day 35-100)', order: 4 },
            { id: 'phase5', name: 'UK OpCo Demonstrator Setup (Day 40-100)', order: 5 },
            { id: 'phase6', name: 'Governance & Compliance (Day 0-100)', order: 6 }
        ],
        tasks: [
            // Phase 1: SPV Activation & Treasury Setup (Day 0-20)
            { id: 't1', name: 'Open SPV Bank Accounts', phase: 'phase1', startDay: 1, duration: 5, status: 'Completed', percentComplete: 100, predecessors: [], criticality: 'critical' },
            { id: 't2', name: 'Complete KYC/AML', phase: 'phase1', startDay: 2, duration: 11, status: 'In Progress', percentComplete: 70, predecessors: ['t1'], criticality: 'critical' },
            { id: 't3', name: 'Establish Treasury Controls', phase: 'phase1', startDay: 4, duration: 9, status: 'In Progress', percentComplete: 55, predecessors: ['t1'], criticality: 'critical' },
            { id: 't4', name: 'Adopt Treasury Policy', phase: 'phase1', startDay: 10, duration: 4, status: 'Not Started', percentComplete: 0, predecessors: ['t2', 't3'], criticality: 'critical' },
            { id: 't5', name: 'Approve Delegated Authorities Matrix', phase: 'phase1', startDay: 10, duration: 5, status: 'Not Started', percentComplete: 0, predecessors: ['t2', 't3'], criticality: 'critical' },
            { id: 't6', name: 'Board Resolution: Treasury Policy', phase: 'phase1', startDay: 14, duration: 3, status: 'Not Started', percentComplete: 0, predecessors: ['t4', 't5'], criticality: 'critical' },
            { id: 't7', name: 'Board Resolution: Intercompany Loan Agreements', phase: 'phase1', startDay: 16, duration: 4, status: 'Not Started', percentComplete: 0, predecessors: ['t6'], criticality: 'critical' },
            { id: 't8', name: 'Capital Entry Readiness Confirmed', phase: 'phase1', startDay: 18, duration: 3, status: 'Not Started', percentComplete: 0, predecessors: ['t2', 't3', 't6', 't7'], criticality: 'critical' },

            // Phase 2: Intercompany Loan Execution (Day 15-35)
            { id: 't9', name: 'Execute Loan A (SPV to US HoldCo)', phase: 'phase2', startDay: 15, duration: 7, status: 'Not Started', percentComplete: 0, predecessors: ['t7'], criticality: 'critical' },
            { id: 't10', name: 'Execute Loan B (US HoldCo to US OpCo)', phase: 'phase2', startDay: 17, duration: 8, status: 'Not Started', percentComplete: 0, predecessors: ['t7'], criticality: 'critical' },
            { id: 't11', name: 'Execute Loan C (SPV to UK OpCo)', phase: 'phase2', startDay: 19, duration: 8, status: 'Not Started', percentComplete: 0, predecessors: ['t7'], criticality: 'critical' },
            { id: 't12', name: 'Create Intercompany Loan Register', phase: 'phase2', startDay: 24, duration: 6, status: 'Not Started', percentComplete: 0, predecessors: ['t9', 't10', 't11'], criticality: 'critical' },
            { id: 't13', name: 'Activate Drawdown Templates', phase: 'phase2', startDay: 28, duration: 4, status: 'Not Started', percentComplete: 0, predecessors: ['t12'], criticality: 'critical' },
            { id: 't14', name: 'Activate Compliance Certificates', phase: 'phase2', startDay: 29, duration: 6, status: 'Not Started', percentComplete: 0, predecessors: ['t12'], criticality: 'critical' },

            // Phase 3: Demonstrator Acquisition & PMI (Day 30-70)
            { id: 't15', name: 'Loan A Drawdown to US HoldCo', phase: 'phase3', startDay: 30, duration: 5, status: 'Not Started', percentComplete: 0, predecessors: ['t9', 't13'], criticality: 'critical' },
            { id: 't16', name: 'Escrow Funded', phase: 'phase3', startDay: 33, duration: 5, status: 'Not Started', percentComplete: 0, predecessors: ['t15'], criticality: 'critical' },
            { id: 't17', name: 'PMI Scheduled', phase: 'phase3', startDay: 35, duration: 4, status: 'Not Started', percentComplete: 0, predecessors: ['t16'], criticality: 'critical' },
            { id: 't18', name: 'Depot-Level PMI and Acceptance', phase: 'phase3', startDay: 39, duration: 14, status: 'Not Started', percentComplete: 0, predecessors: ['t17'], criticality: 'critical' },
            { id: 't19', name: 'FAA Conformity', phase: 'phase3', startDay: 50, duration: 10, status: 'Not Started', percentComplete: 0, predecessors: ['t18'], criticality: 'critical' },
            { id: 't20', name: 'N-Reg Documentation', phase: 'phase3', startDay: 52, duration: 10, status: 'Not Started', percentComplete: 0, predecessors: ['t18'], criticality: 'critical' },
            { id: 't21', name: 'Insurance Binding (SPV as Loss Payee)', phase: 'phase3', startDay: 54, duration: 8, status: 'Not Started', percentComplete: 0, predecessors: ['t18'], criticality: 'critical' },
            { id: 't22', name: 'Demonstrator Airworthy and EU-Ready', phase: 'phase3', startDay: 62, duration: 9, status: 'Not Started', percentComplete: 0, predecessors: ['t19', 't20', 't21'], criticality: 'critical' },

            // Phase 4: BEST Procurement & Engineering (Day 35-100)
            { id: 't23', name: 'Loan B Drawdowns', phase: 'phase4', startDay: 35, duration: 8, status: 'Not Started', percentComplete: 0, predecessors: ['t10', 't13'], criticality: 'critical' },
            { id: 't24', name: 'Pre-Buy Inspections', phase: 'phase4', startDay: 42, duration: 10, status: 'Not Started', percentComplete: 0, predecessors: ['t23'], criticality: 'critical' },
            { id: 't25', name: 'Long-Lead Procurement', phase: 'phase4', startDay: 48, duration: 18, status: 'Not Started', percentComplete: 0, predecessors: ['t24'], criticality: 'critical' },
            { id: 't26', name: 'MRO and Depot-Level Work', phase: 'phase4', startDay: 54, duration: 24, status: 'Not Started', percentComplete: 0, predecessors: ['t24'], criticality: 'critical' },
            { id: 't27', name: 'Integration Baseline Creation', phase: 'phase4', startDay: 70, duration: 12, status: 'Not Started', percentComplete: 0, predecessors: ['t25', 't26'], criticality: 'critical' },
            { id: 't28', name: 'Engineering Documentation', phase: 'phase4', startDay: 76, duration: 16, status: 'Not Started', percentComplete: 0, predecessors: ['t27'], criticality: 'critical' },
            { id: 't29', name: 'Component Tracking Activation', phase: 'phase4', startDay: 86, duration: 10, status: 'Not Started', percentComplete: 0, predecessors: ['t28'], criticality: 'critical' },
            { id: 't30', name: 'Export Control Screening', phase: 'phase4', startDay: 88, duration: 10, status: 'Not Started', percentComplete: 0, predecessors: ['t28'], criticality: 'critical' },
            { id: 't31', name: 'Procurement Logs and Engineering Change Control', phase: 'phase4', startDay: 90, duration: 11, status: 'Not Started', percentComplete: 0, predecessors: ['t28'], criticality: 'critical' },

            // Phase 5: UK OpCo Demonstrator Programme Setup (Day 40-100)
            { id: 't32', name: 'Loan C Drawdown', phase: 'phase5', startDay: 40, duration: 7, status: 'Not Started', percentComplete: 0, predecessors: ['t11', 't13'], criticality: 'critical' },
            { id: 't33', name: 'Poland Base Setup', phase: 'phase5', startDay: 47, duration: 15, status: 'Not Started', percentComplete: 0, predecessors: ['t32'], criticality: 'critical' },
            { id: 't34', name: 'Crew Training', phase: 'phase5', startDay: 56, duration: 14, status: 'Not Started', percentComplete: 0, predecessors: ['t22', 't33'], criticality: 'critical' },
            { id: 't35', name: 'SMS Activation (UK OpCo)', phase: 'phase5', startDay: 60, duration: 12, status: 'Not Started', percentComplete: 0, predecessors: ['t33'], criticality: 'critical' },
            { id: 't36', name: 'Ops Manual (N-Reg) Adoption', phase: 'phase5', startDay: 68, duration: 10, status: 'Not Started', percentComplete: 0, predecessors: ['t34', 't35'], criticality: 'critical' },
            { id: 't37', name: 'CAA and EASA Part NCC Declarations', phase: 'phase5', startDay: 76, duration: 12, status: 'Not Started', percentComplete: 0, predecessors: ['t36'], criticality: 'critical' },
            { id: 't38', name: 'EU Demo Schedule Finalization', phase: 'phase5', startDay: 88, duration: 7, status: 'Not Started', percentComplete: 0, predecessors: ['t22', 't37'], criticality: 'critical' },
            { id: 't39', name: 'Operational Readiness Logs (Flight, Maintenance, MOR, Safety)', phase: 'phase5', startDay: 90, duration: 10, status: 'Not Started', percentComplete: 0, predecessors: ['t37'], criticality: 'critical' },
            { id: 't40', name: 'Customer Demo Procedures', phase: 'phase5', startDay: 93, duration: 8, status: 'Not Started', percentComplete: 0, predecessors: ['t38', 't39'], criticality: 'critical' },

            // Phase 6: Governance & Compliance (Day 0-100)
            { id: 't41', name: 'SMS Governance Framework Activation', phase: 'phase6', startDay: 1, duration: 30, status: 'In Progress', percentComplete: 35, predecessors: [], criticality: 'critical' },
            { id: 't42', name: 'MOR and Safety Reporting Setup', phase: 'phase6', startDay: 10, duration: 35, status: 'In Progress', percentComplete: 30, predecessors: ['t41'], criticality: 'critical' },
            { id: 't43', name: 'Procurement and Engineering Compliance Framework', phase: 'phase6', startDay: 20, duration: 45, status: 'Not Started', percentComplete: 0, predecessors: ['t41'], criticality: 'critical' },
            { id: 't44', name: 'MEL Adoption', phase: 'phase6', startDay: 35, duration: 25, status: 'Not Started', percentComplete: 0, predecessors: ['t41'], criticality: 'critical' },
            { id: 't45', name: 'ERP Activation', phase: 'phase6', startDay: 40, duration: 35, status: 'Not Started', percentComplete: 0, predecessors: ['t41'], criticality: 'critical' },
            { id: 't46', name: 'Monthly Treasury Reporting Cadence', phase: 'phase6', startDay: 18, duration: 83, status: 'In Progress', percentComplete: 20, predecessors: ['t8'], criticality: 'critical' }
        ],
        milestones: [
            { id: 'm1', name: 'Gate 1: SPV Activated', day: 20, taskId: 't8' },
            { id: 'm2', name: 'Gate 2: Loan Architecture Live', day: 35, taskId: 't14' },
            { id: 'm3', name: 'Gate 3: Demonstrator EU-Ready', day: 70, taskId: 't22' },
            { id: 'm4', name: 'Gate 4: BEST Baseline Locked', day: 82, taskId: 't27' },
            { id: 'm5', name: 'Gate 5: UK OpCo Ops Ready', day: 95, taskId: 't40' },
            { id: 'm6', name: 'Gate 6: 100-Day Closeout', day: 100, taskId: 't46' }
        ]
    },

    // Current plan data
    planData: null,
    activityLog: [],

    // Initialize app
    init() {
        this.loadData();
        this.populatePhaseFilter();
        this.populateTaskSelect();
        this.updatePhaseDisplay();
        this.updateGanttChart();
        this.updateCriticalSummary();
        this.updateBoardView();
        this.displayActivityLog();
    },

    // Load data from localStorage or use sample
    loadData() {
        const stored = localStorage.getItem('100dayPlanData');
        if (stored) {
            this.planData = JSON.parse(stored);
        } else {
            this.planData = JSON.parse(JSON.stringify(this.sampleData));
            this.saveData();
        }
    },

    // Save data to localStorage
    saveData() {
        localStorage.setItem('100dayPlanData', JSON.stringify(this.planData));
    },

    // Reset to sample data
    resetData() {
        if (confirm('Reset all data to sample? This cannot be undone.')) {
            this.planData = JSON.parse(JSON.stringify(this.sampleData));
            this.activityLog = [];
            localStorage.removeItem('100dayPlanData');
            localStorage.removeItem('100dayActivityLog');
            this.saveData();
            location.reload();
        }
    },

    // Populate phase filter dropdown
    populatePhaseFilter() {
        const select = document.getElementById('phaseFilter');
        this.planData.phases.forEach(phase => {
            const option = document.createElement('option');
            option.value = phase.id;
            option.textContent = phase.name;
            select.appendChild(option);
        });
    },

    // Populate task select dropdown
    populateTaskSelect() {
        const select = document.getElementById('taskSelect');
        this.planData.tasks.forEach(task => {
            const phaseName = this.planData.phases.find(p => p.id === task.phase)?.name || task.phase;
            const option = document.createElement('option');
            option.value = task.id;
            option.textContent = `${task.name} (${phaseName})`;
            select.appendChild(option);
        });
    },

    // Update phase display based on filters
    updatePhaseDisplay() {
        const statusFilter = document.getElementById('statusFilter').value;
        const phaseFilter = document.getElementById('phaseFilter').value;
        const container = document.getElementById('phaseTracker');
        container.innerHTML = '';

        const phasesToShow = phaseFilter ? this.planData.phases.filter(p => p.id === phaseFilter) : this.planData.phases;

        phasesToShow.forEach(phase => {
            const phaseTasks = this.planData.tasks.filter(t => t.phase === phase.id);
            const filteredTasks = statusFilter ? phaseTasks.filter(t => t.status === statusFilter) : phaseTasks;

            if (filteredTasks.length === 0 && statusFilter) return;

            const phaseEl = document.createElement('div');
            phaseEl.className = 'phase-group';
            
            const phaseHeader = document.createElement('h3');
            phaseHeader.className = 'phase-header';
            phaseHeader.textContent = phase.name;
            phaseEl.appendChild(phaseHeader);

            const phaseProgress = this.calculatePhaseProgress(phaseTasks);
            const progressBar = document.createElement('div');
            progressBar.className = 'progress-bar-container';
            progressBar.innerHTML = `
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${phaseProgress}%"></div>
                </div>
                <span class="progress-text">${Math.round(phaseProgress)}%</span>
            `;
            phaseEl.appendChild(progressBar);

            const taskList = document.createElement('div');
            taskList.className = 'task-list';

            filteredTasks.forEach(task => {
                const taskEl = document.createElement('div');
                taskEl.className = `task-item status-${task.status.replace(/\s+/g, '-').toLowerCase()} criticality-${task.criticality}`;
                
                const taskInfo = document.createElement('div');
                taskInfo.className = 'task-info';
                taskInfo.innerHTML = `
                    <div class="task-name">${task.name}</div>
                    <div class="task-meta">
                        <span class="status-badge">${task.status}</span>
                        <span class="day-range">Days ${task.startDay}-${task.startDay + task.duration - 1}</span>
                        <span class="critical-badge" style="display: ${task.criticality === 'critical' ? 'inline' : 'none'}">CRITICAL</span>
                    </div>
                `;
                taskEl.appendChild(taskInfo);

                const taskMetrics = document.createElement('div');
                taskMetrics.className = 'task-metrics';
                taskMetrics.innerHTML = `
                    <div class="task-progress">
                        <div class="progress-bar small">
                            <div class="progress-fill" style="width: ${task.percentComplete}%"></div>
                        </div>
                        <span class="percent-text">${task.percentComplete}%</span>
                    </div>
                `;
                taskEl.appendChild(taskMetrics);

                taskList.appendChild(taskEl);
            });

            phaseEl.appendChild(taskList);
            container.appendChild(phaseEl);
        });
    },

    // Calculate phase progress
    calculatePhaseProgress(phaseTasks) {
        if (phaseTasks.length === 0) return 0;
        const totalProgress = phaseTasks.reduce((sum, task) => sum + task.percentComplete, 0);
        return totalProgress / phaseTasks.length;
    },

    // Update task status and progress
    updateTask(event) {
        event.preventDefault();
        
        const taskId = document.getElementById('taskSelect').value;
        const status = document.getElementById('taskStatus').value;
        const percentComplete = parseInt(document.getElementById('percentComplete').value);
        const notes = document.getElementById('taskNotes').value;

        const task = this.planData.tasks.find(t => t.id === taskId);
        if (task) {
            task.status = status;
            task.percentComplete = percentComplete;
            
            this.saveData();
            this.addActivity(`Updated ${task.name} to ${status} (${percentComplete}%)`, notes);
            this.updatePhaseDisplay();
            this.updateGanttChart();
            this.updateCriticalSummary();
            this.updateBoardView();
            this.displayActivityLog();
            
            // Reset form
            document.getElementById('taskSelect').value = '';
            document.getElementById('taskStatus').value = 'Not Started';
            document.getElementById('percentComplete').value = '0';
            document.getElementById('taskNotes').value = '';
        }
    },

    // Add activity log entry
    addActivity(action, details = '') {
        const timestamp = new Date().toLocaleString();
        this.activityLog.unshift({ timestamp, action, details });
        if (this.activityLog.length > 50) this.activityLog.pop();
        localStorage.setItem('100dayActivityLog', JSON.stringify(this.activityLog));
    },

    // Display activity log
    displayActivityLog() {
        const log = localStorage.getItem('100dayActivityLog');
        this.activityLog = log ? JSON.parse(log) : [];

        const container = document.getElementById('activityLog');
        container.innerHTML = '';

        if (this.activityLog.length === 0) {
            container.innerHTML = '<p class="empty-log">No activity yet. Make an update to get started.</p>';
            return;
        }

        this.activityLog.forEach(entry => {
            const entryEl = document.createElement('div');
            entryEl.className = 'activity-entry';
            entryEl.innerHTML = `
                <div class="activity-timestamp">${entry.timestamp}</div>
                <div class="activity-action">${entry.action}</div>
                ${entry.details ? `<div class="activity-details">${entry.details}</div>` : ''}
            `;
            container.appendChild(entryEl);
        });
    },

    // Calculate critical path
    calculateCriticalPath() {
        const tasks = this.planData.tasks;
        const taskMap = {};
        tasks.forEach(t => taskMap[t.id] = t);

        // Calculate earliest finish times
        const earlyFinish = {};
        const earlyStart = {};

        const calculateEarly = (taskId, visited = new Set()) => {
            if (visited.has(taskId)) return 0;
            visited.add(taskId);

            const task = taskMap[taskId];
            let maxPredecessorFinish = 0;

            task.predecessors.forEach(predId => {
                const predEarlyFinish = calculateEarly(predId, visited);
                maxPredecessorFinish = Math.max(maxPredecessorFinish, predEarlyFinish);
            });

            earlyStart[taskId] = Math.max(task.startDay, maxPredecessorFinish + 1);
            earlyFinish[taskId] = earlyStart[taskId] + task.duration - 1;
            return earlyFinish[taskId];
        };

        tasks.forEach(t => calculateEarly(t.id));

        // Calculate latest finish times
        const projectEnd = Math.max(...Object.values(earlyFinish));
        const lateFinish = {};
        const lateStart = {};

        tasks.forEach(t => lateFinish[t.id] = projectEnd);

        const calculateLate = (taskId, visited = new Set()) => {
            if (visited.has(taskId)) return projectEnd;
            visited.add(taskId);

            const task = taskMap[taskId];
            let minSuccessorStart = projectEnd + 1;

            tasks.forEach(t => {
                if (t.predecessors.includes(taskId)) {
                    const successorLateStart = calculateLate(t.id, visited);
                    minSuccessorStart = Math.min(minSuccessorStart, successorLateStart);
                }
            });

            if (minSuccessorStart === projectEnd + 1) {
                lateStart[taskId] = projectEnd - task.duration + 1;
            } else {
                lateStart[taskId] = Math.min(lateFinish[taskId], minSuccessorStart - task.duration);
            }
            lateFinish[taskId] = lateStart[taskId] + task.duration - 1;
            return lateStart[taskId];
        };

        tasks.forEach(t => calculateLate(t.id));

        // Identify critical path
        const criticalPath = [];
        tasks.forEach(t => {
            const slack = lateStart[t.id] - earlyStart[t.id];
            if (slack <= 0) {
                criticalPath.push(t.id);
            }
        });

        return { earlyStart, earlyFinish, lateStart, lateFinish, criticalPath };
    },

    // Provide milestone list with fallback defaults
    getMilestones() {
        if (Array.isArray(this.planData.milestones) && this.planData.milestones.length > 0) {
            return this.planData.milestones;
        }
        return [
            { id: 'm1', name: 'Gate 1: SPV Activated', day: 20, taskId: 't8' },
            { id: 'm2', name: 'Gate 2: Loan Architecture Live', day: 35, taskId: 't14' },
            { id: 'm3', name: 'Gate 3: Demonstrator EU-Ready', day: 70, taskId: 't22' },
            { id: 'm4', name: 'Gate 4: BEST Baseline Locked', day: 82, taskId: 't27' },
            { id: 'm5', name: 'Gate 5: UK OpCo Ops Ready', day: 95, taskId: 't40' },
            { id: 'm6', name: 'Gate 6: 100-Day Closeout', day: 100, taskId: 't46' }
        ];
    },

    // Render critical path summary and board-gate status
    updateCriticalSummary() {
        const container = document.getElementById('criticalSummary');
        if (!container) return;

        const { criticalPath, earlyStart, earlyFinish } = this.calculateCriticalPath();
        const criticalTasks = this.planData.tasks
            .filter(t => criticalPath.includes(t.id))
            .sort((a, b) => (earlyStart[a.id] || a.startDay) - (earlyStart[b.id] || b.startDay));

        const projectedDay = Object.values(earlyFinish).length ? Math.max(...Object.values(earlyFinish)) : 0;
        const completed = criticalTasks.filter(t => t.status === 'Completed').length;
        const atRisk = criticalTasks.filter(t => t.status === 'At Risk').length;
        const nextCritical = criticalTasks.find(t => t.status !== 'Completed');

        const milestoneRows = this.getMilestones()
            .sort((a, b) => a.day - b.day)
            .map(m => {
                const task = this.planData.tasks.find(t => t.id === m.taskId);
                const isDone = task && task.status === 'Completed';
                const statusText = task ? `${task.status} (${task.percentComplete}%)` : 'No linked task';
                return `<div class="${isDone ? 'done' : 'pending'}">Day ${m.day} - ${m.name}: ${statusText}</div>`;
            })
            .join('');

        container.innerHTML = `
            <h3>Critical Path Summary</h3>
            <div class="critical-summary-grid">
                <div class="critical-kpi">
                    <div class="critical-kpi-label">Projected Finish</div>
                    <div class="critical-kpi-value">Day ${projectedDay}</div>
                </div>
                <div class="critical-kpi">
                    <div class="critical-kpi-label">Critical Tasks</div>
                    <div class="critical-kpi-value">${criticalTasks.length}</div>
                </div>
                <div class="critical-kpi">
                    <div class="critical-kpi-label">Completed</div>
                    <div class="critical-kpi-value">${completed}</div>
                </div>
                <div class="critical-kpi">
                    <div class="critical-kpi-label">At Risk</div>
                    <div class="critical-kpi-value">${atRisk}</div>
                </div>
            </div>
            <div class="critical-summary-list">
                <div>${nextCritical ? `Next critical task: ${nextCritical.name} (Day ${nextCritical.startDay})` : 'All critical tasks completed'}</div>
                ${milestoneRows}
            </div>
        `;
    },

    // Render compact board-pack summary with KPIs, milestones, and top 10 critical tasks
    updateBoardView() {
        const container = document.getElementById('boardView');
        if (!container) return;

        const { criticalPath, earlyFinish } = this.calculateCriticalPath();
        const criticalTasks = this.planData.tasks
            .filter(t => criticalPath.includes(t.id))
            .sort((a, b) => {
                const aDone = a.status === 'Completed' ? 1 : 0;
                const bDone = b.status === 'Completed' ? 1 : 0;
                if (aDone !== bDone) return aDone - bDone;
                return a.startDay - b.startDay;
            });

        const projectedDay = Object.values(earlyFinish).length ? Math.max(...Object.values(earlyFinish)) : 0;
        const completed = criticalTasks.filter(t => t.status === 'Completed').length;
        const atRisk = criticalTasks.filter(t => t.status === 'At Risk').length;
        const inProgress = criticalTasks.filter(t => t.status === 'In Progress').length;
        const milestones = this.getMilestones().sort((a, b) => a.day - b.day);

        const milestoneLines = milestones.map(m => {
            const linked = this.planData.tasks.find(t => t.id === m.taskId);
            const status = linked ? `${linked.status} (${linked.percentComplete}%)` : 'No linked task';
            return `<div>Day ${m.day} - ${m.name}: <strong>${status}</strong></div>`;
        }).join('');

        const top10 = criticalTasks.slice(0, 10).map(task => {
            const endDay = task.startDay + task.duration - 1;
            return `
                <tr>
                    <td>${task.name}</td>
                    <td>Day ${task.startDay}-${endDay}</td>
                    <td>${task.status}</td>
                    <td>${task.percentComplete}%</td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <div class="board-cards">
                <div class="board-card">
                    <div class="board-card-label">Projected Finish</div>
                    <div class="board-card-value">Day ${projectedDay}</div>
                </div>
                <div class="board-card">
                    <div class="board-card-label">Critical Tasks</div>
                    <div class="board-card-value">${criticalTasks.length}</div>
                </div>
                <div class="board-card">
                    <div class="board-card-label">Completed</div>
                    <div class="board-card-value">${completed}</div>
                </div>
                <div class="board-card">
                    <div class="board-card-label">In Progress</div>
                    <div class="board-card-value">${inProgress}</div>
                </div>
                <div class="board-card">
                    <div class="board-card-label">At Risk</div>
                    <div class="board-card-value">${atRisk}</div>
                </div>
            </div>

            <div class="board-grid">
                <div class="board-panel">
                    <h3>Board-Gate Milestones</h3>
                    <div class="board-list">
                        ${milestoneLines}
                    </div>
                </div>

                <div class="board-panel">
                    <h3>Top 10 Critical Tasks</h3>
                    <table class="board-table">
                        <thead>
                            <tr>
                                <th>Task</th>
                                <th>Window</th>
                                <th>Status</th>
                                <th>Progress</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${top10}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    },

    // Draw vertical milestone markers over the Gantt area
    renderMilestoneMarkers(container, startDay, endDay, cellWidth) {
        const chartHeight = container.scrollHeight;
        this.getMilestones().forEach(milestone => {
            if (milestone.day < startDay || milestone.day > endDay) {
                return;
            }
            const marker = document.createElement('div');
            marker.className = 'milestone-marker';
            marker.style.left = `${300 + (milestone.day - startDay) * cellWidth}px`;
            marker.style.height = `${Math.max(chartHeight, 80)}px`;

            const label = document.createElement('span');
            label.className = 'milestone-label';
            label.textContent = `${milestone.name} (D${milestone.day})`;
            marker.appendChild(label);
            container.appendChild(marker);
        });
    },

    // Update Gantt chart
    updateGanttChart() {
        const weekRange = parseInt(document.getElementById('ganttWeekRange').value);
        const startWeek = parseInt(document.getElementById('ganttStartWeek').value);
        const cellWidth = parseInt(document.getElementById('ganttCellWidth').value);
        const showCriticalPath = document.getElementById('showCriticalPath').checked;
        const showDependencies = document.getElementById('showDependencies').checked;

        const container = document.getElementById('ganttChart');
        container.innerHTML = '';
        container.style.minWidth = (weekRange * 7 * cellWidth + 300) + 'px';

        const { criticalPath } = this.calculateCriticalPath();

        // Header with week numbers
        const headerRow = document.createElement('div');
        headerRow.className = 'gantt-row header';
        const taskNameHeader = document.createElement('div');
        taskNameHeader.className = 'gantt-cell task-name-cell header-cell';
        taskNameHeader.textContent = 'Task';
        headerRow.appendChild(taskNameHeader);

        for (let week = startWeek; week < startWeek + weekRange; week++) {
            const cell = document.createElement('div');
            cell.className = 'gantt-cell header-cell';
            cell.style.width = (7 * cellWidth) + 'px';
            cell.textContent = `W${week}`;
            cell.title = `Week ${week}`;
            headerRow.appendChild(cell);
        }
        container.appendChild(headerRow);

        // Calculate day boundaries
        const startDay = (startWeek - 1) * 7 + 1;
        const endDay = startDay + weekRange * 7 - 1;

        // Task rows
        let tasksToShow = this.planData.tasks;
        if (showCriticalPath) {
            tasksToShow = tasksToShow.filter(t => criticalPath.includes(t.id));
        }

        tasksToShow.forEach(task => {
            const row = document.createElement('div');
            row.className = 'gantt-row';
            if (criticalPath.includes(task.id)) {
                row.classList.add('critical-path');
            }

            const taskNameCell = document.createElement('div');
            taskNameCell.className = 'gantt-cell task-name-cell';
            taskNameCell.title = `${task.name} (Days ${task.startDay}-${task.startDay + task.duration - 1})`;
            taskNameCell.textContent = task.name.substring(0, 25);
            row.appendChild(taskNameCell);

            for (let week = startWeek; week < startWeek + weekRange; week++) {
                const weekStartDay = (week - 1) * 7 + 1;
                const weekEndDay = week * 7;
                const cell = document.createElement('div');
                cell.className = 'gantt-cell';
                cell.style.width = (7 * cellWidth) + 'px';

                // Check if task spans this week
                if (task.startDay <= weekEndDay && task.startDay + task.duration - 1 >= weekStartDay) {
                    const barContainer = document.createElement('div');
                    barContainer.className = 'gantt-bar-container';

                    const bar = document.createElement('div');
                    bar.className = 'gantt-bar';
                    if (criticalPath.includes(task.id)) bar.classList.add('critical');
                    bar.style.backgroundColor = this.getStatusColor(task.status);
                    
                    const completionOverlay = document.createElement('div');
                    completionOverlay.className = 'gantt-completion';
                    completionOverlay.style.width = task.percentComplete + '%';
                    bar.appendChild(completionOverlay);

                    const label = document.createElement('span');
                    label.className = 'gantt-label';
                    label.textContent = task.name.substring(0, 15);
                    bar.appendChild(label);

                    barContainer.appendChild(bar);
                    cell.appendChild(barContainer);
                }

                row.appendChild(cell);
            }

            container.appendChild(row);
        });

        // Draw dependency lines if enabled
        if (showDependencies && !showCriticalPath) {
            this.drawDependencyLines(container, tasksToShow, cellWidth, startWeek);
        }

        this.renderMilestoneMarkers(container, startDay, endDay, cellWidth);
        this.updateCriticalSummary();
        this.updateBoardView();
    },

    // Draw dependency lines between tasks
    drawDependencyLines(container, tasks, cellWidth, startWeek) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'gantt-dependencies');
        svg.setAttribute('width', container.scrollWidth);
        svg.setAttribute('height', container.scrollHeight);

        const taskMap = {};
        container.querySelectorAll('.gantt-row:not(.header)').forEach((row, index) => {
            const taskName = row.querySelector('.task-name-cell').textContent;
            taskMap[taskName] = index;
        });

        this.planData.tasks.forEach(task => {
            task.predecessors.forEach(predId => {
                const pred = this.planData.tasks.find(t => t.id === predId);
                if (pred && taskMap[task.name] !== undefined && taskMap[pred.name] !== undefined) {
                    const y1 = taskMap[pred.name] * 30 + 45;
                    const y2 = taskMap[task.name] * 30 + 45;
                    const x = 300;

                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    line.setAttribute('d', `M${x},${y1} L${x},${(y1 + y2) / 2} L${x},${y2}`);
                    line.setAttribute('stroke', '#999');
                    line.setAttribute('stroke-width', '1');
                    line.setAttribute('fill', 'none');
                    svg.appendChild(line);
                }
            });
        });

        container.appendChild(svg);
    },

    // Get color by status
    getStatusColor(status) {
        const colors = {
            'Completed': '#4caf50',
            'In Progress': '#2196f3',
            'Not Started': '#e0e0e0',
            'At Risk': '#ff9800'
        };
        return colors[status] || '#e0e0e0';
    },

    // Export plan data as JSON
    exportPlanData() {
        const data = {
            planData: this.planData,
            activityLog: this.activityLog,
            exportDate: new Date().toISOString()
        };
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `100-day-plan-${new Date().getTime()}.json`;
        a.click();
    },

    // Import plan data from JSON
    importPlanData() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (event) => {
                try {
                    const data = JSON.parse(event.target.result);
                    this.planData = data.planData;
                    this.activityLog = data.activityLog || [];
                    this.saveData();
                    localStorage.setItem('100dayActivityLog', JSON.stringify(this.activityLog));
                    location.reload();
                } catch (err) {
                    alert('Error importing data: ' + err.message);
                }
            };
            reader.readAsText(file);
        };
        input.click();
    },

    // Export as CSV
    exportCSV() {
        let csv = 'Task ID,Task Name,Phase,Start Day,Duration,End Day,Status,% Complete,Predecessors,Criticality\n';
        
        this.planData.tasks.forEach(task => {
            const phase = this.planData.phases.find(p => p.id === task.phase).name;
            const endDay = task.startDay + task.duration - 1;
            const predIds = task.predecessors.join(';');
            csv += `"${task.id}","${task.name}","${phase}",${task.startDay},${task.duration},${endDay},"${task.status}",${task.percentComplete},"${predIds}","${task.criticality}"\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `100-day-plan-report-${new Date().getTime()}.csv`;
        a.click();
    },

    // Export compact board-pack CSV (KPI snapshot + milestones + top critical tasks)
    exportBoardPackCSV() {
        const { criticalPath, earlyFinish } = this.calculateCriticalPath();
        const criticalTasks = this.planData.tasks
            .filter(t => criticalPath.includes(t.id))
            .sort((a, b) => {
                const aDone = a.status === 'Completed' ? 1 : 0;
                const bDone = b.status === 'Completed' ? 1 : 0;
                if (aDone !== bDone) return aDone - bDone;
                return a.startDay - b.startDay;
            });

        const projectedDay = Object.values(earlyFinish).length ? Math.max(...Object.values(earlyFinish)) : 0;
        const completed = criticalTasks.filter(t => t.status === 'Completed').length;
        const inProgress = criticalTasks.filter(t => t.status === 'In Progress').length;
        const atRisk = criticalTasks.filter(t => t.status === 'At Risk').length;

        let csv = 'BOARD PACK KPI SNAPSHOT\n';
        csv += 'Metric,Value\n';
        csv += `Projected Finish,Day ${projectedDay}\n`;
        csv += `Critical Tasks,${criticalTasks.length}\n`;
        csv += `Completed,${completed}\n`;
        csv += `In Progress,${inProgress}\n`;
        csv += `At Risk,${atRisk}\n\n`;

        csv += 'BOARD GATE MILESTONES\n';
        csv += 'Day,Milestone,Linked Task,Status,Progress\n';
        this.getMilestones().sort((a, b) => a.day - b.day).forEach(m => {
            const linked = this.planData.tasks.find(t => t.id === m.taskId);
            const linkedName = linked ? linked.name : 'N/A';
            const status = linked ? linked.status : 'N/A';
            const progress = linked ? `${linked.percentComplete}%` : 'N/A';
            csv += `${m.day},"${m.name}","${linkedName}",${status},${progress}\n`;
        });

        csv += '\nTOP 10 CRITICAL TASKS\n';
        csv += 'Task,Window,Status,Progress\n';
        criticalTasks.slice(0, 10).forEach(task => {
            const endDay = task.startDay + task.duration - 1;
            csv += `"${task.name}","Day ${task.startDay}-${endDay}",${task.status},${task.percentComplete}%\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `board-pack-${new Date().getTime()}.csv`;
        a.click();
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => app.init());
