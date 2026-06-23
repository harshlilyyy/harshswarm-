# NYX Phoenix Migration - Architecture Diagram

## N-Tier Decoupled Architecture

```mermaid
graph TB
    subgraph "Tier 1: Frontend (Next.js 14 on Vercel)"
        A[User Browser] --> B[Next.js App Router]
        B --> C[React Query Hooks]
        C --> D[UI Components]
        D --> E[Live Dashboard]
        D --> F[Agent Terrain Map]
        D --> G[Key Health Monitor]
    end
    
    subgraph "Tier 2: Backend (FastAPI on Render)"
        H[API Gateway] --> I[CORS Middleware]
        I --> J[REST Endpoints]
        I --> K[WebSocket Handler]
        
        J --> L[Simulation Controller]
        J --> M[Generation Controller]
        J --> N[Analytics Controller]
        J --> O[Config Controller]
        
        K --> P[Real-time Stream]
    end
    
    subgraph "Tier 3: Core Services"
        L --> Q[KeyRotator Service]
        M --> Q
        Q --> R[Circuit Breaker]
        Q --> S[Weighted Round-Robin]
        
        N --> T[DatabaseRetriever]
        T --> U[SQL Adapter]
        T --> V[Vector DB Adapter]
        
        L --> W[NYX Kernel]
        N --> W
    end
    
    subgraph "Tier 4: External Services"
        Q --> X[Groq API]
        Q --> Y[Google Gemini]
        Q --> Z[Mistral AI]
        Q --> AA[Other LLMs]
        
        U --> AB[PostgreSQL/SQLite]
        V --> AC[Qdrant/Pinecone]
    end
    
    subgraph "Enhancement Layer"
        R --> AD[Cool-down Timer]
        S --> AE[Adaptive Throttling]
        P --> AF[Simulation Recorder]
        O --> AG[Hot-Reload Config]
    end
```

## Data Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant KeyRotator
    participant LLM
    participant Kernel
    
    User->>Frontend: Configure simulation
    Frontend->>Backend: POST /api/simulate
    Backend->>Kernel: run_simulation()
    Kernel-->>Backend: Deterministic results
    Backend-->>Frontend: Simulation ID + Results
    Frontend->>Backend: WebSocket connect
    Backend-->>Frontend: Stream ticks
    
    Note over KeyRotator: Circuit Breaker Active
    Frontend->>Backend: POST /api/generate
    Backend->>KeyRotator: generate_async()
    KeyRotator->>LLM: Try provider #1 (weighted)
    alt Provider fails
        LLM-->>KeyRotator: 429 Rate Limit
        KeyRotator->>KeyRotator: Record failure
        KeyRotator->>LLM: Try provider #2
    else Provider succeeds
        LLM-->>KeyRotator: Response
        KeyRotator->>KeyRotator: Record success
        KeyRotator-->>Backend: Response + Provider
    end
    Backend-->>Frontend: Generated text
```

## Component Responsibilities

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| Next.js Frontend | React 18, TypeScript | UI/UX, real-time visualization |
| FastAPI Backend | Python 3.12, AsyncIO | API orchestration, validation |
| KeyRotator | Custom | Multi-provider fallback with circuit breaker |
| DatabaseRetriever | SQLAlchemy, Vector Clients | RAG pipeline for context injection |
| NYX Kernel | Preserved from legacy | Deterministic agent simulation |
| WebSocket Server | FastAPI WebSockets | Real-time simulation streaming |

## Deployment Topology

```
┌─────────────────────────────────────────────────────────────┐
│                      VERCEL (Frontend)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Next.js Static Export (dist/)                        │   │
│  │  - _redirects for SPA routing                         │   │
│  │  - vercel.json rewrites to backend                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS (API calls)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   RENDER (Backend)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI Application (uvicorn)                        │   │
│  │  - REST endpoints                                       │   │
│  │  - WebSocket server                                     │   │
│  │  - Background tasks                                     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Persistent Disk (1GB)                                │   │
│  │  - SQLite database                                      │   │
│  │  - Simulation archives                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ API Calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  EXTERNAL APIS                               │
│  - Groq, Google, Mistral, etc. (LLM providers)              │
│  - Qdrant/Pinecone (Vector databases)                       │
└─────────────────────────────────────────────────────────────┘
```

## Security Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                    SECURITY ZONES                        │
├─────────────────────────────────────────────────────────┤
│ Zone 1: Public Internet                                  │
│ - Vercel CDN                                              │
│ - Static assets                                           │
├─────────────────────────────────────────────────────────┤
│ Zone 2: API Layer (CORS Protected)                       │
│ - FastAPI endpoints                                       │
│ - Rate limiting                                           │
│ - Input validation (Pydantic)                             │
├─────────────────────────────────────────────────────────┤
│ Zone 3: Service Layer                                    │
│ - KeyRotator (keys never exposed)                         │
│ - Circuit breaker state                                   │
├─────────────────────────────────────────────────────────┤
│ Zone 4: Environment Secrets                              │
│ - API keys via Render env vars                            │
│ - Never committed to git                                  │
└─────────────────────────────────────────────────────────┘
```
