# api

HTTP application boundary for canonical memory queries, artifact generation requests, correction workflows, and publication decisions.

Write operations require authenticated authorization and explicit policy checks. Search projections are read accelerators and cannot bypass canonical PostgreSQL/RLS decisions.
