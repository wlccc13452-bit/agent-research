# API Contract - Cross-Stack Source of Truth

## Contract Metadata

| Field | Value |
|-------|-------|
| Contract ID | STOCK-PEG-API-CONTRACT-V1 |
| Status | Active |
| Effective Date | 2026-03-21 |
| Decision Link | D044 |
| Contract MD5 | `62b714ab1d9f6981dfb03888076dfda9` |

## Contract Workflow

1. Backend-Node updates this contract before any API schema change.
2. Frontend-Node regenerates or synchronizes types from this contract.
3. Progress entry must include:
   - `Executed By: [Agent_ID]`
   - `Agent: [Backend-Node/Frontend-Node/Bot-Node]`
   - `Contract: [api-contract.md#md5=<hash>]`
   - `Evidence: [test/temp/<task>/...]`

## Endpoint Contracts

### GET /api/indicators/force-index/{code_or_name}

- Method: GET
- Path Params:
  - `code_or_name` (string, required)
- Query Params:
  - `days` (integer, optional, default: 60)
  - `include_history` (boolean, optional, default: false)
- Response 200:

```json
{
  "code": "600519",
  "name": "Kweichow Moutai",
  "force_index": 12345.67,
  "period_days": 60,
  "updated_at": "2026-03-21T09:30:00Z"
}
```

### POST /api/indicators/force-index-batch

- Method: POST
- Body:

```json
{
  "codes": ["600519", "000001"],
  "days": 60
}
```

- Response 200:

```json
{
  "results": [
    {
      "code": "600519",
      "force_index": 12345.67,
      "updated_at": "2026-03-21T09:30:00Z"
    }
  ],
  "errors": []
}
```

## Contract Change Log

- 2026-03-21: Initialized contract-first governance for federated multi-agent execution (D044).
