# Bot PR Management Workflow Diagram

## Overview Flowchart

```mermaid
graph TD
    A[New Bot PR Created] --> B{PR Event Type}
    B -->|opened| C[Label Bot PRs Job]
    B -->|opened| D[Detect Duplicates Job]
    B -->|opened| E[Bot Coordination Job]
    B -->|opened| F[PR Health Check Job]
    B -->|synchronize| C
    
    C --> C1[Identify Bot Type]
    C1 --> C2[Dependabot?]
    C1 --> C3[Copilot?]
    C1 --> C4[CodeRabbit?]
    C1 --> C5[Others?]
    
    C2 --> C6[Calculate PR Size]
    C3 --> C6
    C4 --> C6
    C5 --> C6
    
    C6 --> C7[Apply Labels]
    C7 --> C8{Is Dependabot?}
    C8 -->|Yes| G[Auto-Merge Job]
    C8 -->|No| END1[End]
    
    G --> G1{Update Type?}
    G1 -->|Patch/Minor| G2[Auto-Approve]
    G1 -->|Major| G3[Add Warning Comment]
    
    G2 --> G4[Wait for CI Checks]
    G4 --> G5{All Checks Pass?}
    G5 -->|Yes| G6[Enable Auto-Merge]
    G5 -->|No| END2[Manual Review Needed]
    G6 --> END3[PR Auto-Merged]
    G3 --> END2
    
    D --> D1[Extract Title Key Phrase]
    D1 --> D2[Compare with Open PRs]
    D2 --> D3{Duplicates Found?}
    D3 -->|Yes| D4[Add Comment with Links]
    D3 -->|No| END4[No Action]
    D4 --> D5[Add possible-duplicate Label]
    D5 --> END4
    
    E --> E1[Check for Issue References]
    E1 --> E2{Has Issue Refs?}
    E2 -->|Yes| E3[Find Other Bot PRs]
    E2 -->|No| END5[Skip Check]
    E3 --> E4{Multiple Bots?}
    E4 -->|Yes| E5[Add Coordination Alert]
    E4 -->|No| END5
    E5 --> E6[Add bot-coordination-needed Label]
    E6 --> END5
    
    F --> F1[Check PR Description]
    F --> F2[Check File Count]
    F --> F3[Check PR Age]
    F --> F4[Check Merge Status]
    F1 --> F5{Issues Found?}
    F2 --> F5
    F3 --> F5
    F4 --> F5
    F5 -->|Yes| F6[Add Health Check Comment]
    F5 -->|No| END6[Healthy PR]
    F6 --> END6
    
    SCHED[Daily Schedule Trigger] --> H[Mark Stale PRs Job]
    H --> H1[Get All Open PRs]
    H1 --> H2{PR Inactive > 30 Days?}
    H2 -->|Yes| H3{Has Exempt Label?}
    H2 -->|No| END7[Skip]
    H3 -->|Yes| END7
    H3 -->|No| H4[Mark as Stale]
    H4 --> H5{Stale > 7 Days?}
    H5 -->|Yes| H6[Close PR]
    H5 -->|No| END7
    H6 --> END7
    
    style A fill:#e1f5ff
    style G6 fill:#d4edda
    style H6 fill:#f8d7da
    style D4 fill:#fff3cd
    style E5 fill:#fff3cd
    style F6 fill:#fff3cd
    style G3 fill:#fff3cd
```

## Job Flow Details

### 1. Label Bot PRs Flow

```mermaid
sequenceDiagram
    participant PR as New PR
    participant WF as Workflow
    participant GH as GitHub API
    
    PR->>WF: PR opened event
    WF->>WF: Extract author username
    WF->>WF: Identify bot type
    WF->>WF: Calculate PR size (additions + deletions)
    WF->>WF: Detect PR type from title
    WF->>GH: Check if labels exist
    GH-->>WF: Label status
    WF->>GH: Create missing labels
    WF->>GH: Apply labels to PR
    GH-->>PR: PR labeled
```

### 2. Duplicate Detection Flow

```mermaid
sequenceDiagram
    participant PR as New PR
    participant WF as Workflow
    participant GH as GitHub API
    
    PR->>WF: PR opened event
    WF->>GH: List all open PRs
    GH-->>WF: Open PRs list
    WF->>WF: Extract key phrase from title
    WF->>WF: Compare with other PR titles
    alt Duplicates Found
        WF->>GH: Create comment with duplicate list
        WF->>GH: Add possible-duplicate label
        GH-->>PR: Alert added
    else No Duplicates
        WF->>WF: No action needed
    end
```

### 3. Dependabot Auto-Merge Flow

```mermaid
sequenceDiagram
    participant PR as Dependabot PR
    participant WF as Workflow
    participant DM as Dependabot Metadata
    participant CI as CI Checks
    participant GH as GitHub API
    
    PR->>WF: PR opened/updated
    WF->>DM: Fetch update metadata
    DM-->>WF: Update type (major/minor/patch)
    
    alt Patch or Minor Update
        WF->>GH: Approve PR
        WF->>CI: Monitor check status
        CI-->>WF: All checks passed
        WF->>GH: Enable auto-merge
        GH-->>PR: PR auto-merged
    else Major Update
        WF->>GH: Comment about breaking changes
        WF->>GH: Add needs-review label
        GH-->>PR: Manual review required
    end
```

### 4. Stale PR Management Flow

```mermaid
sequenceDiagram
    participant CRON as Daily Schedule
    participant WF as Workflow
    participant GH as GitHub API
    participant PR as Stale PR
    
    CRON->>WF: Trigger daily run
    WF->>GH: List all open PRs
    GH-->>WF: PR list with timestamps
    
    loop For Each PR
        WF->>WF: Calculate days inactive
        alt Inactive > 30 days AND Not exempt
            WF->>GH: Add stale label
            WF->>GH: Post stale comment
            GH-->>PR: Marked as stale
            
            alt Stale > 7 more days
                WF->>GH: Close PR
                WF->>GH: Post closure comment
                GH-->>PR: PR closed
            end
        end
    end
```

## Label Hierarchy

```mermaid
graph LR
    subgraph Bot Type Labels
        L1[bot:dependabot]
        L2[bot:copilot]
        L3[bot:coderabbit]
        L4[bot:jules]
        L5[bot:others...]
    end
    
    subgraph Size Labels
        S1[size:XS<10]
        S2[size:S<100]
        S3[size:M<500]
        S4[size:L<1000]
        S5[size:XL>1000]
    end
    
    subgraph Type Labels
        T1[bug-fix]
        T2[enhancement]
        T3[refactoring]
        T4[tests]
        T5[documentation]
    end
    
    subgraph Status Labels
        ST1[auto-merge-candidate]
        ST2[needs-review]
        ST3[possible-duplicate]
        ST4[bot-coordination-needed]
        ST5[stale]
    end
    
    subgraph Update Type
        U1[patch-update]
        U2[minor-update]
        U3[major-update]
    end
    
    style L1 fill:#bfd4f2
    style S3 fill:#c5def5
    style T1 fill:#d4edda
    style ST2 fill:#fff3cd
    style U3 fill:#f8d7da
```

## Decision Tree

```mermaid
graph TD
    START[Bot PR Created] --> Q1{Is Bot PR?}
    Q1 -->|Yes| Q2{Which Bot?}
    Q1 -->|No| END1[Use Regular PR Flow]
    
    Q2 -->|Dependabot| Q3{Update Type?}
    Q2 -->|Other Bots| Q6[Apply Bot Label]
    
    Q3 -->|Patch/Minor| Q4[Auto-Approve + Auto-Merge]
    Q3 -->|Major| Q5[Flag for Manual Review]
    
    Q6 --> Q7{Duplicate?}
    Q7 -->|Yes| Q8[Alert Maintainers]
    Q7 -->|No| Q9{Coordination Issue?}
    
    Q9 -->|Yes| Q10[Alert Maintainers]
    Q9 -->|No| Q11{PR Healthy?}
    
    Q11 -->|Yes| END2[Ready for Review]
    Q11 -->|No| Q12[Provide Recommendations]
    
    Q4 --> Q13{CI Passing?}
    Q13 -->|Yes| END3[Auto-Merged]
    Q13 -->|No| END4[Wait for CI]
    
    Q5 --> END5[Awaiting Maintainer]
    Q8 --> END2
    Q10 --> END2
    Q12 --> END2
    
    style Q4 fill:#d4edda
    style Q5 fill:#fff3cd
    style END3 fill:#d4edda
    style END5 fill:#fff3cd
```

## State Machine

```mermaid
stateDiagram-v2
    [*] --> New: PR Created
    New --> Labeled: Auto-label Job
    Labeled --> Reviewed: Duplicate Check
    Reviewed --> Coordinated: Bot Coordination Check
    Coordinated --> Healthy: Health Check
    
    Healthy --> AutoMerge: Dependabot Patch/Minor
    Healthy --> ManualReview: Major Update or Issues
    Healthy --> Active: Regular Bot PR
    
    AutoMerge --> CIWait: Approve PR
    CIWait --> Merged: CI Passes
    CIWait --> ManualReview: CI Fails
    
    Active --> Stale: 30 Days Inactive
    Stale --> Active: New Activity
    Stale --> Closed: 7 More Days Inactive
    
    ManualReview --> Active: Maintainer Engages
    ManualReview --> Closed: Manually Closed
    
    Merged --> [*]
    Closed --> [*]
    
    note right of AutoMerge
        Only for safe
        dependency updates
    end note
    
    note right of Stale
        Can be prevented with
        keep-open label
    end note
```

## Integration Points

```mermaid
graph TB
    subgraph External Systems
        GH[GitHub API]
        DM[Dependabot Metadata]
        CI[CI/CD Systems]
    end
    
    subgraph Workflow Jobs
        J1[Label Bot PRs]
        J2[Detect Duplicates]
        J3[Auto-Merge Dependabot]
        J4[Mark Stale PRs]
        J5[Bot Coordination]
        J6[PR Health Check]
    end
    
    subgraph Outputs
        O1[Labels Applied]
        O2[Comments Added]
        O3[PRs Auto-Merged]
        O4[PRs Closed]
        O5[Notifications Sent]
    end
    
    GH --> J1
    GH --> J2
    GH --> J4
    GH --> J5
    GH --> J6
    
    DM --> J3
    CI --> J3
    
    J1 --> O1
    J2 --> O2
    J3 --> O3
    J3 --> O2
    J4 --> O4
    J4 --> O2
    J5 --> O2
    J6 --> O2
    
    O1 --> GH
    O2 --> GH
    O3 --> GH
    O4 --> GH
    O5 --> GH
```

## Timeline

```mermaid
gantt
    title Bot PR Lifecycle Timeline
    dateFormat X
    axisFormat %d
    
    section PR Lifecycle
    PR Created           :a1, 0, 1d
    Auto-Labeled         :a2, 0, 1d
    Health Check         :a3, 0, 1d
    Duplicate Detection  :a4, 0, 1d
    Active State         :a5, 1, 29d
    Marked Stale         :milestone, m1, 30
    Grace Period         :a6, 30, 7d
    Auto-Closed          :milestone, m2, 37
    
    section Dependabot Only
    Auto-Approval        :b1, 0, 1d
    CI Checks            :b2, 0, 2d
    Auto-Merge           :milestone, m3, 2
```

## Success Metrics

```mermaid
pie title Expected PR Distribution After Implementation
    "Auto-Merged (Dependabot)" : 40
    "Under Review" : 25
    "Awaiting CI" : 15
    "Stale (To Be Closed)" : 10
    "Duplicates Identified" : 10
```

---

*These diagrams illustrate the comprehensive bot PR management workflow implemented in `.github/workflows/bot-pr-management.yml`*
