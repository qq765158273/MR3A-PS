"""Public MCP arguments. Validation completes before any browser operation."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator


FieldName = Annotated[str, Field(pattern=r'^GM[A-Z0-9_]*$', min_length=3, max_length=18)]
RecordName = Annotated[str, Field(pattern=r'^GM[A-Z0-9_]*$', min_length=3, max_length=15)]
AEName = Annotated[str, Field(pattern=r'^GM[A-Z0-9_]*$', min_length=3, max_length=12)]
ExistingFieldName = Annotated[str, Field(pattern=r'^[A-Z][A-Z0-9_]*$', min_length=1, max_length=18)]
ExistingRecordName = Annotated[str, Field(pattern=r'^[A-Z][A-Z0-9_]*$', min_length=1, max_length=15)]
RecordKind = Literal['Derived/Work', 'SQL Table', 'SQL View', 'Dynamic View', 'Temporary Table']
# PSIDE's Record definition can contain more fields than the small samples used
# by the first MCP version.  Keep this explicit so the pipeline and API share a
# single contract for full physical records such as PS_DEPT_TBL (60 columns)
# plus the PROCESS_INSTANCE key required by PeopleSoft Temporary Tables.
MAX_RECORD_FIELDS = 61
ProjectName = Annotated[str, Field(pattern=r'^GM[A-Z0-9_]*$', min_length=3, max_length=15)]


class FieldRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: FieldName
    type: Literal['Character', 'Date'] = 'Character'
    length: int = Field(default=20, ge=1, le=254)
    label_id: str = Field(default='GMTEST', min_length=1, max_length=18, pattern=r'^[A-Z][A-Z0-9_]*$')
    long_name: str = Field(min_length=1, max_length=30)
    short_name: str = Field(min_length=1, max_length=15)

    @model_validator(mode='after')
    def single_line_labels(self):
        if any(character in value for value in (self.long_name, self.short_name) for character in ('\x00', '\r', '\n')):
            raise ValueError('Field labels must be single-line text without NUL')
        return self


class RecordField(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: ExistingFieldName
    key: StrictBool = False
    alternate_search_key: StrictBool = False
    listbox: StrictBool = False
    search_key: StrictBool = False

    @model_validator(mode='after')
    def supported_search_key(self):
        if self.search_key and not self.key:
            raise ValueError('Search Key requires Key in PSIDE; use Alternate Search Key for a non-key field')
        return self


RecordFields = Annotated[list[ExistingFieldName | RecordField], Field(min_length=1, max_length=MAX_RECORD_FIELDS)]


class RecordRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: RecordName
    type: RecordKind = 'Derived/Work'
    fields: RecordFields
    build: StrictBool = False
    tablespace: str = Field(default='HRAPP', min_length=1, max_length=30, pattern=r'^[A-Z][A-Z0-9_]*$')
    view_sql: str | None = Field(default=None, max_length=65536,
                                 description='SQL text for SQL View or Dynamic View; plain SELECT or a caller-supplied dynamic SQL placeholder')

    @model_validator(mode='after')
    def unique_fields(self):
        names = [item if isinstance(item, str) else item.name for item in self.fields]
        if len(set(names)) != len(names):
            raise ValueError('Record fields must be unique')
        if self.build and self.type not in {'SQL Table', 'SQL View', 'Temporary Table'}:
            raise ValueError('Build requires SQL Table, SQL View or Temporary Table')
        is_view = self.type in {'SQL View', 'Dynamic View'}
        if is_view and self.view_sql is None:
            raise ValueError('SQL View and Dynamic View require explicit view_sql')
        if not is_view and self.view_sql is not None:
            raise ValueError('view_sql is only valid for SQL View and Dynamic View')
        if self.view_sql is not None and (not self.view_sql.strip() or '\x00' in self.view_sql
                                         or len(self.view_sql.encode('utf-8')) > 65536):
            raise ValueError('view_sql must be nonblank, contain no NUL and fit in 64 KiB of UTF-8')
        return self


class AEStep(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str | None = Field(default=None, description='Step01, Step02, etc.; omit to allocate sequentially')
    type: Literal['SQL', 'PeopleCode']
    code: str = Field(min_length=1, max_length=65536)

    @model_validator(mode='after')
    def valid_payload(self):
        if not self.code.strip() or '\x00' in self.code or len(self.code.encode('utf-8')) > 65536:
            raise ValueError('Code must be nonblank, contain no NUL and fit in 64 KiB of UTF-8')
        return self


class AERequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: AEName
    steps: list[AEStep] = Field(min_length=1, max_length=4)
    state_record: ExistingRecordName | None = Field(default=None, description='Existing AET to add as the single default state record before compiling code')
    disable_restart: StrictBool | None = Field(default=None, description='Set the Disable Restart property; omit to keep its default')
    temporary_records: list[ExistingRecordName] | None = Field(
        default=None, min_length=1, max_length=10,
        description='Existing Temporary Table records to bind; omit to preserve the default empty list')

    @model_validator(mode='after')
    def sequential_steps(self):
        if self.temporary_records is not None and len(set(self.temporary_records)) != len(self.temporary_records):
            raise ValueError('temporary_records must not contain duplicate names')
        for index, step in enumerate(self.steps, 1):
            expected = f'Step{index:02d}'
            if step.name is not None and step.name != expected:
                raise ValueError(f'Expected step name {expected}; custom step names are not supported yet')
            step.name = expected
        return self


class ProjectDefinition(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: Literal['AE', 'Record', 'Field']
    name: ExistingFieldName

    @model_validator(mode='after')
    def definition_name_length(self):
        limit = {'AE': 12, 'Record': 15, 'Field': 18}[self.type]
        if len(self.name) > limit:
            raise ValueError(f'{self.type} names must fit in {limit} characters')
        return self


class ProjectRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: ProjectName
    definitions: list[ProjectDefinition] = Field(min_length=1, max_length=20)

    @model_validator(mode='after')
    def unique_definitions(self):
        identities = [(item.type, item.name) for item in self.definitions]
        if len(set(identities)) != len(identities):
            raise ValueError('Project definitions must be unique by type and name')
        return self
