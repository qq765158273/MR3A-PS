"""PSIDE MCP server: typed arguments -> original Maa/MR3A pipelines -> Playwright CLI."""

import argparse
import logging
from pathlib import Path
import sys
from typing import Literal

from mcp.server.fastmcp import FastMCP

from psauto.config import load_config
from psauto.objects.models import AEName, AERequest, AEStep, ExistingFieldName, FieldName, FieldRequest, RecordField, RecordName, RecordRequest
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
    def create_record(name: RecordName, fields: list[ExistingFieldName | RecordField],
                      type: Literal['Derived/Work', 'SQL Table'] = 'Derived/Work', build: bool = False,
                      tablespace: str = 'HRAPP') -> dict:
        """Create a GM Record with field key/alternate_search_key/listbox/search_key options; optionally Build a new SQL Table. Save and close; DB verifies content."""
        return service.execute(RecordRequest(name=name, fields=fields, type=type, build=build, tablespace=tablespace))

    @server.tool()
    def create_ae(name: AEName, steps: list[AEStep]) -> dict:
        """Create a GM AE in MAIN with 1–4 SQL/PeopleCode steps, paste code, save and close all its editors. DB verifies content; the AE is not executed."""
        return service.execute(AERequest(name=name, steps=steps))

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
