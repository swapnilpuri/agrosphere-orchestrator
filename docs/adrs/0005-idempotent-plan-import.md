# Immutable milestone import and scoped task identity

Status: Accepted for AEO-1

Decision: Import an entire validated milestone atomically. Use unique project/milestone and milestone/task keys, compare content on repeated import and return existing task UUIDs.

Consequences: Safe repeat imports create no duplicate events. Changed plan content needs a new milestone ID; concurrent writers are outside AEO-1 scope.
