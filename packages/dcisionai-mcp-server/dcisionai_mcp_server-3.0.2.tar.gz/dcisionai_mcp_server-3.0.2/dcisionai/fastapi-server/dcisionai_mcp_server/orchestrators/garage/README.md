# Orchestrators Garage - Archived Code

This folder contains orchestrator code that has been replaced by the **Clean Architecture Refactor**.

---

## Archived Files

### `lmea_express_orchestrator_old.py`
**Date Archived**: 2025-01-03  
**Reason**: Unnecessary layer removed in Clean Architecture refactor

**Original Purpose**:
- Wrapper around `HybridSolver.solve_express()`
- Added metadata to response
- Just passed through to hybrid solver

**Replaced By**:
- Direct call to `DcisionAISolverV2.solve_auto()` from HTTP MCP Server
- No intermediate orchestrator layer needed

**Old Flow**:
```
HTTP MCP Server → LMEAExpressOrchestrator → HybridSolver → V2 Solver
```

**New Flow**:
```
HTTP MCP Server → V2 Solver (solve_auto)
```

---

## Why Archived?

The Clean Architecture refactor eliminated unnecessary data transformation layers:
- ✅ Reduced 6-layer flow to 2-layer flow
- ✅ Single source of truth (V2 Solver)
- ✅ No data transformation/loss
- ✅ Easier to debug and maintain

See `CLEAN_ARCHITECTURE_REFACTOR_PLAN.md` for full details.

---

## Can I Delete These Files?

**Yes**, but we keep them for:
1. Reference if rollback needed
2. Understanding old architecture
3. Documenting what was removed

Safe to delete after successful production deployment of clean architecture.

