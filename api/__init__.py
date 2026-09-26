"""FastAPI backend package for the Baghewala digital twin (SIH26120).

`api.main` builds the app via `create_app()`. Everything else in this
package (settings, schemas, db, jobs, routers/*) only shapes HTTP around the
`twin` and `ml` packages -- it must never reimplement physics or ML logic.
"""
