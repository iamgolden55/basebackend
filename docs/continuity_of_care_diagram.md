# Continuity of Care Flow Diagram 🔄

This document provides a visual representation of how continuity of care is implemented in our doctor assignment system.

## Continuity of Care Process Flow

```mermaid
flowchart TD
    A[New Appointment Request] --> B{Has Past Appointments?}
    B -->|No| C[Standard Doctor Assignment]
    B -->|Yes| D[Retrieve Past Appointments]
    
    D --> E[Calculate Continuity Scores]
    
    subgraph "Continuity Score Calculation"
        E1[Count Past Appointments\n30% weight] 
        E2[Calculate Recency\n50% weight]
        E3[Check Department Match\n20% weight]
        E1 & E2 & E3 --> E4[Combine Weighted Scores]
    end
    
    E --> F{Appointment Type?}
    F -->|Follow-up| G[Apply 3x Weight]
    F -->|Regular| H[Apply Standard Weight]
    F -->|Emergency| I[Apply No Weight]
    
    G & H & I --> J[Integrate with Other Factors]
    
    subgraph "Doctor Score Calculation"
        J1[Experience Score]
        J2[Language Match Score]
        J3[Specialty Match Score]
        J4[Continuity Score]
        J5[Complexity Score]
        J6[Workload Penalty]
        J1 & J2 & J3 & J4 & J5 & J6 --> J7[Final Doctor Score]
    end
    
    J --> K[Rank Available Doctors]
    K --> L[Assign Highest-Scoring Doctor]
    C --> L
    
    style E1 fill:#f9f,stroke:#333,stroke-width:2px
    style E2 fill:#f9f,stroke:#333,stroke-width:2px
    style E3 fill:#f9f,stroke:#333,stroke-width:2px
    style E4 fill:#f9f,stroke:#333,stroke-width:2px
    style J4 fill:#f9f,stroke:#333,stroke-width:2px
```

## Continuity Score Calculation Detail

```mermaid
flowchart LR
    A[Past Appointments] --> B[Count Score]
    A --> C[Recency Score]
    A --> D[Department Score]
    
    B[Count Score\n30%] --> E{Count >= 5?}
    E -->|Yes| F[Score = 1.0]
    E -->|No| G[Score = count/5]
    
    C[Recency Score\n50%] --> H{Days Since Last?}
    H -->|Recent| I[High Score]
    H -->|< 1 Year| J[Decaying Score]
    H -->|> 1 Year| K[Score = 0]
    
    D[Department Score\n20%] --> L{Same Department?}
    L -->|Yes| M[Score = 1.0]
    L -->|No| N[Score = 0.5]
    
    F & G --> O[Weighted Count\n0.3 × Count Score]
    I & J & K --> P[Weighted Recency\n0.5 × Recency Score]
    M & N --> Q[Weighted Department\n0.2 × Department Score]
    
    O & P & Q --> R[Combined Score]
    R --> S{Appointment Type}
    S -->|Follow-up| T[Final Score = Combined × 15]
    S -->|Regular| U[Final Score = Combined × 5]
    S -->|Emergency| V[Final Score = 0]
    
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#f9f,stroke:#333,stroke-width:2px
    style O fill:#f9f,stroke:#333,stroke-width:2px
    style P fill:#f9f,stroke:#333,stroke-width:2px
    style Q fill:#f9f,stroke:#333,stroke-width:2px
    style R fill:#f9f,stroke:#333,stroke-width:2px
```

## Balancing Continuity with Other Factors

```mermaid
graph TD
    A[Doctor Assignment Factors] --> B[Continuity of Care]
    A --> C[Specialty Match]
    A --> D[Language Match]
    A --> E[Doctor Experience]
    A --> F[Current Workload]
    
    B --> G{Appointment Type}
    G -->|Follow-up| H[High Weight\n3x normal]
    G -->|Regular| I[Standard Weight]
    G -->|Emergency| J[No Weight]
    
    C --> K{Patient Condition}
    K -->|Complex/Specialized| L[May Override Continuity]
    K -->|Routine| M[Standard Weight]
    
    D --> N{Communication Needs}
    N -->|Critical| O[May Override Continuity]
    N -->|Standard| P[Standard Weight]
    
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#f9f,stroke:#333,stroke-width:2px
    style H fill:#f9f,stroke:#333,stroke-width:2px
    style I fill:#f9f,stroke:#333,stroke-width:2px
    style J fill:#f9f,stroke:#333,stroke-width:2px
```

## Testing Continuity of Care

```mermaid
flowchart TD
    A[Continuity Testing] --> B[Basic Continuity Test]
    A --> C[Multiple Appointments Test]
    A --> D[Recency Test]
    A --> E[Cross-Department Test]
    
    B --> B1[Create Past Appointment]
    B1 --> B2[Create New Appointment]
    B2 --> B3[Verify Same Doctor Assigned]
    
    C --> C1[Create Multiple Past Appointments]
    C1 --> C2[Create New Appointment]
    C2 --> C3[Verify Same Doctor Assigned]
    
    D --> D1[Create Old Appointment with Doctor A]
    D1 --> D2[Create Recent Appointment with Doctor B]
    D2 --> D3[Create New Appointment]
    D3 --> D4[Verify Doctor B Assigned]
    
    E --> E1[Create Past Appointment in Department X]
    E1 --> E2[Create New Appointment in Department Y]
    E2 --> E3[Verify Different Doctor Assigned]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#f9f,stroke:#333,stroke-width:2px
    style E fill:#f9f,stroke:#333,stroke-width:2px
``` 