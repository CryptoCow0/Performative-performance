# MyGov Database Profiling Results

**Date:** 2026-06-03  
**Schema Version:** V6 (SQLCipher, plaintext JSON payloads)  
**Data Volume:** 908 appointments, 4500 inspections, 2000 vehicles, 2500 queue items  
**Environment:** Postgres 16-alpine in Docker (proxy for SQLite query planning)

## Summary

Every database query path completes in under 1.5ms. The database is not the bottleneck. Application-layer slowness comes from per-field AES-GCM encryption (35% CPU), sequential async round-trips (908 awaits in a loop), and unconditional full syncs on scope change.

## Results

### Reads - Point lookups

| Query | Method | Time |
|-------|--------|------|
| getAppointmentsModelById | `WHERE appointment_id = ?` | 0.07ms |
| getInspectionModelByInspectionId | `WHERE inspection_id = ? AND license_result_id = ?` | 0.02ms |
| getVehicleByVehicleId | `WHERE vehicle_id = ?` | 0.02ms |
| getVehicleByMobileVehicleId | `WHERE mobile_vehicle_id = ?` | 0.10ms |
| getStandardCorrectionItemById | `WHERE correction_item_id = ?` | 0.06ms |
| getStandardChecklistItem | `WHERE module = ? AND checklist_item_id = ?` | 0.09ms |
| getStandardChecklistCeById | `WHERE module = 'ce' AND checklist_id = ?` | 0.07ms |
| getStandardChecklistBlById | `WHERE module = 'bl' AND checklist_id = ?` | 0.01ms |
| getStandardChecklistPiById | `WHERE module = 'pi' AND checklist_id = ?` | 0.04ms |

### Reads - Filtered sets

| Query | Rows returned | Time |
|-------|---------------|------|
| getInspectionModelsByDirty | 241 | 0.21ms |
| getVehicleModelsByDirty | 176 | 0.32ms |
| getPendingQueueRecords (with CASE sort) | 496 | 0.40ms |
| getInspectionModelsByAppointmentId | ~5 | 0.02ms |
| **Batch getInspectionCounts (908 IDs)** | 908 | **1.41ms** |

### Reads - Full table scans

| Query | Rows | Time |
|-------|------|------|
| getAppointmentsModel | 908 | 0.15ms |
| getVehicleModels | 2000 | 0.22ms |
| getInspectionModels | 4500 | 0.68ms |
| getStandardCorrectionItems | 1000 | 0.13ms |

### Reads - Sync timestamps

| Query | Time |
|-------|------|
| getAppointmentLastSync | 0.01ms |
| getInspectionLastSync | 0.01ms |
| getStandardChecklistLastSync | 0.01ms |
| getStandardCorrectionLastSync | 0.01ms |
| getVehicleLastSync | 0.01ms |

### Writes

| Query | Time |
|-------|------|
| insertAppointment | 0.26ms |
| upsertAppointment (conflict/update) | 0.02ms |
| insertQueueRecord | 0.11ms |
| completeQueueRecord (update by id) | 0.37ms |
| deleteAppointment | 0.04ms |
| deleteInspection | 0.05ms |

## Key Comparison: Batch vs Sequential

| Approach | Total time for 908 appointments |
|----------|--------------------------------|
| Old: 908 sequential `await getInspectionCountByAppointmentId()` | ~2,500ms (async overhead) |
| New: 1 batch `WHERE appointment_id IN (...) GROUP BY` | 1.41ms |
| **Improvement** | **~1,770x** |

## Identified Bottlenecks (Application Layer)

| Issue | Impact | Fix |
|-------|--------|-----|
| Per-field AES-GCM encrypt/decrypt (pure Dart) | 35% CPU on main thread, causes jank | SQLCipher whole-DB encryption (MG5-24010) |
| 908 sequential `await` calls in `buildList()` | ~2.5s per scope build | Batch query with `WHERE IN` (MG5-24010) |
| 300ms delay + retry in `retrieveAppointments` | Unnecessary wait on every sync | Removed (MG5-24010) |
| `doSync(true)` on every scope switch | Full sync on tab change | Separate ticket (double-sync) |
| `retrieveImages` loads ALL vehicles + inspections | Memory pressure | Separate ticket |

## Indexes (V5/V6)

```sql
CREATE UNIQUE INDEX idx_appointments_appointment_id ON appointments (appointment_id);
CREATE UNIQUE INDEX idx_corrections_correction_item_id ON standard_correction_items (correction_item_id);
CREATE UNIQUE INDEX idx_checklists_module_checklist_id ON standard_checklist (module, checklist_id);
CREATE UNIQUE INDEX idx_checklist_items_module_item_id ON standard_checklist_item (module, checklist_item_id);
CREATE INDEX idx_inspections_inspection_id_result_id ON inspections (inspection_id, license_result_id);
CREATE INDEX idx_inspections_appointment_id ON inspections (appointment_id);
CREATE INDEX idx_inspections_is_dirty ON inspections (is_dirty);
CREATE INDEX idx_vehicles_vehicle_id ON vehicles (vehicle_id);
CREATE INDEX idx_vehicles_mobile_vehicle_id ON vehicles (mobile_vehicle_id);
CREATE INDEX idx_vehicles_is_dirty ON vehicles (is_dirty);
CREATE INDEX idx_queue_completed ON queue (completed);
```
