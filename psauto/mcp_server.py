"""PSIDE MCP server: typed arguments -> original Maa/MR3A pipelines -> Playwright CLI."""

import argparse
import logging
from pathlib import Path
import sys
from typing import Literal
from pydantic import StrictBool

from mcp.server.fastmcp import FastMCP

from psauto.config import load_config
from psauto.objects.models import AEName, AERequest, AEStep, ExistingFieldName, ExistingRecordName, FieldName, FieldRequest, ProjectDefinition, ProjectName, ProjectRequest, RecordField, RecordFields, RecordKind, RecordName, RecordRequest
from psauto.objects.service import ObjectService


def create_server(cfg):
    server = FastMCP('PSIDE MR3A')
    service = ObjectService(cfg)

    @server.tool()
    def create_field(name: FieldName, long_name: str, short_name: str,
                     type: Literal['Character', 'Date'] = 'Character', length: int = 20,
                     label_id: str = 'GMTEST') -> dict:
        """Create and save a GM Field, then close it and leave the workspace idle. Content verification belongs to DB; existing names are rejected."""
        return service.execute(FieldRequest(name=name, type=type, length=length, label_id=label_id,
                                            long_name=long_name, short_name=short_name))

    @server.tool()
    def create_record(name: RecordName, fields: RecordFields,
                      type: RecordKind = 'Derived/Work', build: bool = False,
                      tablespace: str = 'HRAPP', view_sql: str | None = None) -> dict:
        """Create a GM SQL Table/View, Dynamic View, Derived/Work or Temporary Table. Views require view_sql, pasted through the clipboard and saved without OCR readback. Build applies to SQL Table/View or Temporary Table. Save and close; DB verifies content."""
        return service.execute(RecordRequest(name=name, fields=fields, type=type, build=build,
                                            tablespace=tablespace, view_sql=view_sql))

    @server.tool()
    def create_ae(name: AEName, steps: list[AEStep], state_record: ExistingRecordName | None = None,
                  disable_restart: StrictBool | None = None,
                  temporary_records: list[ExistingRecordName] | None = None,
                  temporary_table_instances: int = 3) -> dict:
        """Create a GM AE with 1–4 SQL/PeopleCode steps; optionally bind one default AET, 1–10 existing Temporary Table records, Disable Restart and the default three-instance pool before code compilation. Save and close; DB verifies content. This tool does not execute the AE."""
        return service.execute(AERequest(name=name, steps=steps,state_record=state_record,
                                         disable_restart=disable_restart, temporary_records=temporary_records,
                                         temporary_table_instances=temporary_table_instances))

    @server.tool()
    def save_project(name: ProjectName, definitions: list[ProjectDefinition]) -> dict:
        """Save a new GM Project containing 1–20 existing AE/Record/Field definitions and all their native Related Definitions, including code. Names are exact; existing projects are rejected. Project names are limited to 15 characters for full visual confirmation. Return to an empty Untitled workspace. DB verifies members; this does not export a file or execute AE."""
        return service.execute(ProjectRequest(name=name, definitions=definitions))

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default=str(Path(__file__).with_name('config.json')))
    args = parser.parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    cfg = load_config(args.config)
    create_server(cfg).run(transport='stdio')


if __name__ == '__main__':
    main()
