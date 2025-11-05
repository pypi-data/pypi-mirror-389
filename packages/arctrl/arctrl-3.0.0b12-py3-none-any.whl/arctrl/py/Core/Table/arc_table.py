from __future__ import annotations
from collections.abc import Callable
from typing import Any
from ...fable_modules.fable_library.array_ import (iterate as iterate_2, sort_descending)
from ...fable_modules.fable_library.list import (FSharpList, is_empty, iterate, append)
from ...fable_modules.fable_library.map_util import get_item_from_dict
from ...fable_modules.fable_library.option import (default_arg, map as map_1)
from ...fable_modules.fable_library.range import range_big_int
from ...fable_modules.fable_library.reflection import (TypeInfo, class_type)
from ...fable_modules.fable_library.seq import (to_array, delay, map, remove_at, iterate as iterate_1, try_find_index, length, collect, singleton, choose, indexed, to_list, map_indexed, append as append_1)
from ...fable_modules.fable_library.string_ import (to_fail, printf, join)
from ...fable_modules.fable_library.system_text import (StringBuilder__ctor, StringBuilder__AppendLine_Z721C83C5)
from ...fable_modules.fable_library.types import (Array, to_string)
from ...fable_modules.fable_library.util import (ignore, IEnumerable_1, get_enumerator, compare_primitives, equals, dispose, safe_hash)
from ..Helper.collections_ import (ResizeArray_map, ResizeArray_iteri, ResizeArray_singleton, ResizeArray_iter, ResizeArray_init, ResizeArray_choose, ResizeArray_mapi, ResizeArray_groupBy, ResizeArray_indexed)
from ..Helper.hash_codes import (box_hash_array, box_hash_seq)
from ..ontology_annotation import OntologyAnnotation
from .arc_table_aux import (SanityChecks_validateArcTableValues, ArcTableValues, Unchecked_tryGetCellAt, SanityChecks_validateColumnIndex, SanityChecks_validateRowIndex, Unchecked_getCellWithDefault, Unchecked_setCellAt, try_find_duplicate_unique, SanityChecks_validateColumn, Unchecked_addColumn, Unchecked_addColumnFill, Unchecked_removeHeader, Unchecked_removeColumnCells, try_find_duplicate_unique_in_array, Unchecked_removeColumnCells_withIndexChange, ColumnValueRefs, get_empty_cell_for_header, Unchecked_moveColumnTo, Unchecked_addRow, Unchecked_addEmptyRow, Unchecked_addRows, Unchecked_removeRowCells_withIndexChange, Unchecked_alignByHeaders, SanityChecks_validateCellColumns)
from .composite_cell import CompositeCell
from .composite_column import CompositeColumn
from .composite_header import CompositeHeader

def _expr806() -> TypeInfo:
    return class_type("ARCtrl.ArcTable", None, ArcTable)


class ArcTable:
    def __init__(self, name: str, headers: Array[CompositeHeader] | None=None, columns: Array[Array[CompositeCell]] | None=None) -> None:
        headers_1: Array[CompositeHeader] = default_arg(headers, [])
        columns_1: Array[Array[CompositeCell]] = default_arg(columns, [])
        valid: bool = SanityChecks_validateCellColumns(headers_1, columns_1, True)
        self._values: ArcTableValues = ArcTableValues.from_cell_columns(columns_1)
        self._name: str = name
        self._headers: Array[CompositeHeader] = headers_1

    @property
    def ValueMap(self, __unit: None=None) -> Any:
        this: ArcTable = self
        return this._values.ValueMap

    @ValueMap.setter
    def ValueMap(self, value_map: Any) -> None:
        this: ArcTable = self
        this._values.ValueMap = value_map

    @property
    def ColumnRefs(self, __unit: None=None) -> Any:
        this: ArcTable = self
        return this._values.Columns

    @ColumnRefs.setter
    def ColumnRefs(self, internal_column_refs: Any) -> None:
        this: ArcTable = self
        this._values.Columns = internal_column_refs

    @property
    def Headers(self, __unit: None=None) -> Array[CompositeHeader]:
        this: ArcTable = self
        return this._headers

    @Headers.setter
    def Headers(self, new_headers: Array[CompositeHeader]) -> None:
        this: ArcTable = self
        ignore(SanityChecks_validateArcTableValues(new_headers, this._values, True))
        this._headers = new_headers

    @property
    def Values(self, __unit: None=None) -> ArcTableValues:
        this: ArcTable = self
        return this._values

    @property
    def Name(self, __unit: None=None) -> str:
        this: ArcTable = self
        return this._name

    @Name.setter
    def Name(self, new_name: str) -> None:
        this: ArcTable = self
        this._name = new_name

    @staticmethod
    def create(name: str, headers: Array[CompositeHeader], values: Array[Array[CompositeCell]]) -> ArcTable:
        return ArcTable(name, headers, values)

    @staticmethod
    def init(name: str) -> ArcTable:
        return ArcTable(name, [], [])

    @staticmethod
    def from_arc_table_values(name: str, headers: Array[CompositeHeader], values: ArcTableValues) -> ArcTable:
        t: ArcTable = ArcTable.init(name)
        t.Headers = headers
        t.ValueMap = values.ValueMap
        t.ColumnRefs = values.Columns
        t.RowCount = values.RowCount or 0
        return t

    @staticmethod
    def create_from_rows(name: str, headers: Array[CompositeHeader], rows: Array[Array[CompositeCell]]) -> ArcTable:
        t: ArcTable = ArcTable(name, headers)
        t.AddRows(rows)
        return t

    def Validate(self, raise_exception: bool | None=None) -> bool:
        this: ArcTable = self
        raise_exception_1: bool = default_arg(raise_exception, True)
        return SanityChecks_validateArcTableValues(this.Headers, this.Values, raise_exception_1)

    @staticmethod
    def validate(raise_exception: bool | None=None) -> Callable[[ArcTable], bool]:
        def _arrow733(table: ArcTable) -> bool:
            return table.Validate(raise_exception)

        return _arrow733

    @property
    def ColumnCount(self, __unit: None=None) -> int:
        this: ArcTable = self
        return len(this.Headers)

    @staticmethod
    def column_count(table: ArcTable) -> int:
        return table.ColumnCount

    @property
    def RowCount(self, __unit: None=None) -> int:
        this: ArcTable = self
        return this._values.RowCount

    @RowCount.setter
    def RowCount(self, new_row_count: int) -> None:
        this: ArcTable = self
        this._values.RowCount = new_row_count or 0

    @staticmethod
    def row_count(table: ArcTable) -> int:
        return table.RowCount

    @staticmethod
    def set_row_count(new_row_count: int) -> Callable[[ArcTable], ArcTable]:
        def _arrow737(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.RowCount = new_row_count or 0
            return new_table

        return _arrow737

    @property
    def Columns(self, __unit: None=None) -> Array[CompositeColumn]:
        this: ArcTable = self
        def _arrow740(__unit: None=None) -> IEnumerable_1[CompositeColumn]:
            def _arrow739(i: int) -> CompositeColumn:
                return this.GetColumn(i)

            return map(_arrow739, range_big_int(0, 1, this.ColumnCount - 1))

        return list(to_array(delay(_arrow740)))

    def Copy(self, __unit: None=None) -> ArcTable:
        this: ArcTable = self
        def f(h: CompositeHeader) -> CompositeHeader:
            return h.Copy()

        next_headers: Array[CompositeHeader] = ResizeArray_map(f, this.Headers)
        next_values: ArcTableValues = this._values.Copy()
        return ArcTable.from_arc_table_values(this.Name, next_headers, next_values)

    def TryGetCellAt(self, column: int, row: int) -> CompositeCell | None:
        this: ArcTable = self
        return Unchecked_tryGetCellAt(column, row, this._values)

    @staticmethod
    def try_get_cell_at(column: int, row: int) -> Callable[[ArcTable], CompositeCell | None]:
        def _arrow741(table: ArcTable) -> CompositeCell | None:
            return table.TryGetCellAt(column, row)

        return _arrow741

    def GetCellAt(self, column: int, row: int) -> CompositeCell:
        this: ArcTable = self
        SanityChecks_validateColumnIndex(column, this.ColumnCount, False)
        SanityChecks_validateRowIndex(row, this.RowCount, False)
        return Unchecked_getCellWithDefault(column, row, this._headers, this._values)

    @staticmethod
    def get_cell_at(column: int, row: int) -> Callable[[ArcTable], CompositeCell]:
        def _arrow744(table: ArcTable) -> CompositeCell:
            return table.GetCellAt(column, row)

        return _arrow744

    def IterColumns(self, action: Callable[[CompositeColumn], None]) -> None:
        this: ArcTable = self
        for column_index in range(0, (this.ColumnCount - 1) + 1, 1):
            action(this.GetColumn(column_index))

    @staticmethod
    def iter_columns(action: Callable[[CompositeColumn], None]) -> Callable[[ArcTable], ArcTable]:
        def _arrow745(table: ArcTable) -> ArcTable:
            copy: ArcTable = table.Copy()
            copy.IterColumns(action)
            return copy

        return _arrow745

    def IteriColumns(self, action: Callable[[int, CompositeColumn], None]) -> None:
        this: ArcTable = self
        for column_index in range(0, (this.ColumnCount - 1) + 1, 1):
            action(column_index, this.GetColumn(column_index))

    @staticmethod
    def iteri_columns(action: Callable[[int, CompositeColumn], None]) -> Callable[[ArcTable], ArcTable]:
        def _arrow748(table: ArcTable) -> ArcTable:
            copy: ArcTable = table.Copy()
            copy.IteriColumns(action)
            return copy

        return _arrow748

    def UpdateCellAt(self, column_index: int, row_index: int, c: CompositeCell, skip_validation: bool | None=None) -> None:
        this: ArcTable = self
        if not default_arg(skip_validation, False):
            SanityChecks_validateColumnIndex(column_index, this.ColumnCount, False)
            SanityChecks_validateRowIndex(row_index, this.RowCount, False)
            ignore(c.ValidateAgainstHeader(this.Headers[column_index], True))

        Unchecked_setCellAt(column_index, row_index, c, this._values)

    @staticmethod
    def update_cell_at(column_index: int, row_index: int, cell: CompositeCell, skip_validation: bool | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow749(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.UpdateCellAt(column_index, row_index, cell, skip_validation)
            return new_table

        return _arrow749

    def SetCellAt(self, column_index: int, row_index: int, c: CompositeCell, skip_validation: bool | None=None) -> None:
        this: ArcTable = self
        if not default_arg(skip_validation, False):
            SanityChecks_validateColumnIndex(column_index, this.ColumnCount, False)
            ignore(c.ValidateAgainstHeader(this.Headers[column_index], True))

        Unchecked_setCellAt(column_index, row_index, c, this._values)

    @staticmethod
    def set_cell_at(column_index: int, row_index: int, cell: CompositeCell, skip_validation: bool | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow750(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.SetCellAt(column_index, row_index, cell, skip_validation)
            return new_table

        return _arrow750

    def UpdateCellsBy(self, f: Callable[[int, int, CompositeCell], CompositeCell], skip_validation: bool | None=None) -> None:
        this: ArcTable = self
        skip_validation_1: bool = default_arg(skip_validation, False)
        with get_enumerator(this._values) as enumerator:
            while enumerator.System_Collections_IEnumerator_MoveNext():
                kv: Any = enumerator.System_Collections_Generic_IEnumerator_1_get_Current()
                pattern_input: tuple[int, int] = kv[0]
                ri: int = pattern_input[1] or 0
                ci: int = pattern_input[0] or 0
                new_cell: CompositeCell = f(ci, ri, kv[1])
                if not skip_validation_1:
                    ignore(new_cell.ValidateAgainstHeader(this.Headers[ci], True))

                Unchecked_setCellAt(ci, ri, new_cell, this._values)

    @staticmethod
    def update_cells_by(f: Callable[[int, int, CompositeCell], CompositeCell], skip_validation: bool | None=None) -> Callable[[ArcTable], None]:
        def _arrow751(table: ArcTable) -> None:
            new_table: ArcTable = table.Copy()
            new_table.UpdateCellsBy(f, skip_validation)

        return _arrow751

    def UpdateCellBy(self, column_index: int, row_index: int, f: Callable[[CompositeCell], CompositeCell], skip_validation: bool | None=None) -> None:
        this: ArcTable = self
        skip_validation_1: bool = default_arg(skip_validation, False)
        if not skip_validation_1:
            SanityChecks_validateColumnIndex(column_index, this.ColumnCount, False)
            SanityChecks_validateRowIndex(row_index, this.RowCount, False)

        new_cell: CompositeCell = f(this.GetCellAt(column_index, row_index))
        if not skip_validation_1:
            ignore(new_cell.ValidateAgainstHeader(this.Headers[column_index], True))

        Unchecked_setCellAt(column_index, row_index, new_cell, this._values)

    @staticmethod
    def update_cell_by(column_index: int, row_index: int, f: Callable[[CompositeCell], CompositeCell], skip_validation: bool | None=None) -> Callable[[ArcTable], None]:
        def _arrow752(table: ArcTable) -> None:
            new_table: ArcTable = table.Copy()
            new_table.UpdateCellBy(column_index, row_index, f, skip_validation)

        return _arrow752

    def UpdateHeader(self, index: int, new_header: CompositeHeader, force_convert_cells: bool | None=None) -> None:
        this: ArcTable = self
        force_convert_cells_1: bool = default_arg(force_convert_cells, False)
        SanityChecks_validateColumnIndex(index, this.ColumnCount, False)
        header: CompositeHeader = new_header
        match_value: int | None = try_find_duplicate_unique(header, remove_at(index, this.Headers))
        if match_value is not None:
            raise Exception(((("Invalid input. Tried setting unique header `" + str(header)) + "`, but header of same type already exists at index ") + str(match_value)) + ".")

        c: CompositeColumn = CompositeColumn(new_header, this.GetColumn(index).Cells)
        if c.Validate():
            set_header: None
            this.Headers[index] = new_header

        elif force_convert_cells_1:
            def f(c_1: CompositeCell) -> CompositeCell:
                if c_1.is_free_text:
                    return c_1.ToTermCell()

                else: 
                    return c_1


            def f_1(c_2: CompositeCell) -> CompositeCell:
                return c_2.ToFreeTextCell()

            converted_cells: Array[CompositeCell] = ResizeArray_map(f, c.Cells) if new_header.IsTermColumn else ResizeArray_map(f_1, c.Cells)
            this.UpdateColumn(index, new_header, converted_cells)

        else: 
            raise Exception("Tried setting header for column with invalid type of cells. Set `forceConvertCells` flag to automatically convert cells into valid CompositeCell type.")


    @staticmethod
    def update_header(index: int, header: CompositeHeader) -> Callable[[ArcTable], ArcTable]:
        def _arrow753(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.UpdateHeader(index, header)
            return new_table

        return _arrow753

    def AddColumn(self, header: CompositeHeader, cells: Array[CompositeCell] | None=None, index: int | None=None, force_replace: bool | None=None) -> None:
        this: ArcTable = self
        index_1: int = default_arg(index, this.ColumnCount) or 0
        cells_1: Array[CompositeCell] = default_arg(cells, [])
        force_replace_1: bool = default_arg(force_replace, False)
        SanityChecks_validateColumnIndex(index_1, this.ColumnCount, True)
        SanityChecks_validateColumn(CompositeColumn.create(header, cells_1))
        Unchecked_addColumn(header, cells_1, index_1, force_replace_1, False, this.Headers, this._values)

    @staticmethod
    def add_column(header: CompositeHeader, cells: Array[CompositeCell] | None=None, index: int | None=None, force_replace: bool | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow754(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.AddColumn(header, cells, index, force_replace)
            return new_table

        return _arrow754

    def AddColumnFill(self, header: CompositeHeader, cell: CompositeCell, index: int | None=None, force_replace: bool | None=None) -> None:
        this: ArcTable = self
        index_1: int = default_arg(index, this.ColumnCount) or 0
        force_replace_1: bool = default_arg(force_replace, False)
        SanityChecks_validateColumnIndex(index_1, this.ColumnCount, True)
        SanityChecks_validateColumn(CompositeColumn.create(header, [cell]))
        Unchecked_addColumnFill(header, cell, index_1, force_replace_1, False, this.Headers, this._values)

    @staticmethod
    def add_column_fill(header: CompositeHeader, cell: CompositeCell, index: int | None=None, force_replace: bool | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow755(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.AddColumnFill(header, cell, index, force_replace)
            return new_table

        return _arrow755

    def UpdateColumn(self, column_index: int, header: CompositeHeader, cells: Array[CompositeCell] | None=None) -> None:
        this: ArcTable = self
        SanityChecks_validateColumnIndex(column_index, this.ColumnCount, False)
        column: CompositeColumn = CompositeColumn.create(header, cells)
        SanityChecks_validateColumn(column)
        header_1: CompositeHeader = column.Header
        match_value: int | None = try_find_duplicate_unique(header_1, remove_at(column_index, this.Headers))
        if match_value is not None:
            raise Exception(((("Invalid input. Tried setting unique header `" + str(header_1)) + "`, but header of same type already exists at index ") + str(match_value)) + ".")

        Unchecked_removeHeader(column_index, this.Headers)
        Unchecked_removeColumnCells(column_index, this._values)
        this.Headers.insert(column_index, column.Header)
        def f(row_index: int, v: CompositeCell) -> None:
            Unchecked_setCellAt(column_index, row_index, v, this._values)

        ResizeArray_iteri(f, column.Cells)

    @staticmethod
    def update_column(column_index: int, header: CompositeHeader, cells: Array[CompositeCell] | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow756(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.UpdateColumn(column_index, header, cells)
            return new_table

        return _arrow756

    def InsertColumn(self, index: int, header: CompositeHeader, cells: Array[CompositeCell] | None=None) -> None:
        this: ArcTable = self
        this.AddColumn(header, cells, index, False)

    @staticmethod
    def insert_column(index: int, header: CompositeHeader, cells: Array[CompositeCell] | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow757(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.InsertColumn(index, header, cells)
            return new_table

        return _arrow757

    def AppendColumn(self, header: CompositeHeader, cells: Array[CompositeCell] | None=None) -> None:
        this: ArcTable = self
        this.AddColumn(header, cells, this.ColumnCount, False)

    @staticmethod
    def append_column(header: CompositeHeader, cells: Array[CompositeCell] | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow758(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.AppendColumn(header, cells)
            return new_table

        return _arrow758

    def AddColumns(self, columns: IEnumerable_1[CompositeColumn], index: int | None=None, force_replace: bool | None=None) -> None:
        this: ArcTable = self
        index_1: int = default_arg(index, this.ColumnCount) or 0
        force_replace_1: bool = default_arg(force_replace, False)
        SanityChecks_validateColumnIndex(index_1, this.ColumnCount, True)
        def mapping(x: CompositeColumn) -> CompositeHeader:
            return x.Header

        duplicates: FSharpList[dict[str, Any]] = try_find_duplicate_unique_in_array(map(mapping, columns))
        if not is_empty(duplicates):
            sb: Any = StringBuilder__ctor()
            ignore(StringBuilder__AppendLine_Z721C83C5(sb, "Found duplicate unique columns in `columns`."))
            def action(x_1: dict[str, Any]) -> None:
                ignore(StringBuilder__AppendLine_Z721C83C5(sb, ((((("Duplicate `" + str(x_1["HeaderType"])) + "` at index ") + str(x_1["Index1"])) + " and ") + str(x_1["Index2"])) + "."))

            iterate(action, duplicates)
            raise Exception(to_string(sb))

        def action_1(x_2: CompositeColumn) -> None:
            SanityChecks_validateColumn(x_2)

        iterate_1(action_1, columns)
        def action_2(col: CompositeColumn) -> None:
            nonlocal index_1
            prev_headers_count: int = len(this.Headers) or 0
            Unchecked_addColumn(col.Header, col.Cells, index_1, force_replace_1, False, this.Headers, this._values)
            if len(this.Headers) > prev_headers_count:
                index_1 = (index_1 + 1) or 0


        iterate_1(action_2, columns)

    @staticmethod
    def add_columns(columns: Array[CompositeColumn], index: int | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow759(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.AddColumns(columns, index)
            return new_table

        return _arrow759

    def RemoveColumn(self, index: int) -> None:
        this: ArcTable = self
        SanityChecks_validateColumnIndex(index, this.ColumnCount, False)
        column_count: int = this.ColumnCount or 0
        Unchecked_removeHeader(index, this.Headers)
        Unchecked_removeColumnCells_withIndexChange(index, column_count, this._values)

    @staticmethod
    def remove_column(index: int) -> Callable[[ArcTable], ArcTable]:
        def _arrow760(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.RemoveColumn(index)
            return new_table

        return _arrow760

    def RemoveColumns(self, index_arr: Array[int]) -> None:
        this: ArcTable = self
        def _arrow761(index: int) -> None:
            SanityChecks_validateColumnIndex(index, this.ColumnCount, False)

        iterate_2(_arrow761, index_arr)
        def _arrow762(index_1: int) -> None:
            this.RemoveColumn(index_1)

        class ObjectExpr763:
            @property
            def Compare(self) -> Callable[[int, int], int]:
                return compare_primitives

        iterate_2(_arrow762, sort_descending(index_arr, ObjectExpr763()))

    @staticmethod
    def remove_columns(index_arr: Array[int]) -> Callable[[ArcTable], ArcTable]:
        def _arrow764(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.RemoveColumns(index_arr)
            return new_table

        return _arrow764

    def GetColumn(self, column_index: int, fail_on_missing_cell: bool | None=None) -> CompositeColumn:
        this: ArcTable = self
        fail_on_missing_cell_1: bool = default_arg(fail_on_missing_cell, False)
        SanityChecks_validateColumnIndex(column_index, this.ColumnCount, False)
        h: CompositeHeader = this.Headers[column_index]
        cells: Array[CompositeCell] = []
        if this.RowCount != 0:
            col: ColumnValueRefs = get_item_from_dict(this._values.Columns, column_index)
            if col.tag == 1:
                vals: Any = col.fields[0]
                empty_cell: CompositeCell = get_empty_cell_for_header(h, None)
                for row_index in range(0, (this.RowCount - 1) + 1, 1):
                    if row_index in vals:
                        (cells.append(get_item_from_dict(this._values.ValueMap, get_item_from_dict(vals, row_index))))

                    elif fail_on_missing_cell_1:
                        to_fail(printf("Could not return column: Unable to find cell for index: (%i, %i)"))(column_index)(row_index)

                    else: 
                        (cells.append(empty_cell))


            else: 
                c: CompositeCell = get_item_from_dict(this._values.ValueMap, col.fields[0])
                for i in range(0, (this.RowCount - 1) + 1, 1):
                    (cells.append(c))


        return CompositeColumn.create(h, cells)

    @staticmethod
    def get_column(index: int, fail_on_missing_cell: bool | None=None) -> Callable[[ArcTable], CompositeColumn]:
        def _arrow765(table: ArcTable) -> CompositeColumn:
            return table.GetColumn(index, fail_on_missing_cell)

        return _arrow765

    def TryGetColumnByHeader(self, header: CompositeHeader, fail_on_missing_cell: bool | None=None) -> CompositeColumn | None:
        this: ArcTable = self
        def mapping(i: int) -> CompositeColumn:
            return this.GetColumn(i, fail_on_missing_cell)

        def predicate(x: CompositeHeader) -> bool:
            return equals(x, header)

        return map_1(mapping, try_find_index(predicate, this.Headers))

    @staticmethod
    def try_get_column_by_header(header: CompositeHeader, fail_on_missing_cell: bool | None=None) -> Callable[[ArcTable], CompositeColumn | None]:
        def _arrow766(table: ArcTable) -> CompositeColumn | None:
            return table.TryGetColumnByHeader(header, fail_on_missing_cell)

        return _arrow766

    def TryGetColumnByHeaderBy(self, header_predicate: Callable[[CompositeHeader], bool], fail_on_missing_cell: bool | None=None) -> CompositeColumn | None:
        this: ArcTable = self
        def mapping(i: int) -> CompositeColumn:
            return this.GetColumn(i, fail_on_missing_cell)

        return map_1(mapping, try_find_index(header_predicate, this.Headers))

    @staticmethod
    def try_get_column_by_header_by(header_predicate: Callable[[CompositeHeader], bool], fail_on_missing_cell: bool | None=None) -> Callable[[ArcTable], CompositeColumn | None]:
        def _arrow767(table: ArcTable) -> CompositeColumn | None:
            return table.TryGetColumnByHeaderBy(header_predicate, fail_on_missing_cell)

        return _arrow767

    def GetColumnByHeader(self, header: CompositeHeader, fail_on_missing_cell: bool | None=None) -> CompositeColumn:
        this: ArcTable = self
        match_value: CompositeColumn | None = this.TryGetColumnByHeader(header, fail_on_missing_cell)
        if match_value is None:
            arg: str = this.Name
            return to_fail(printf("Unable to find column with header in table %s: %O"))(arg)(header)

        else: 
            return match_value


    @staticmethod
    def get_column_by_header(header: CompositeHeader, fail_on_missing_cell: bool | None=None) -> Callable[[ArcTable], CompositeColumn]:
        def _arrow768(table: ArcTable) -> CompositeColumn:
            return table.GetColumnByHeader(header, fail_on_missing_cell)

        return _arrow768

    def TryGetInputColumn(self, __unit: None=None) -> CompositeColumn | None:
        this: ArcTable = self
        def mapping(i: int) -> CompositeColumn:
            return this.GetColumn(i)

        def predicate(x: CompositeHeader) -> bool:
            return x.is_input

        return map_1(mapping, try_find_index(predicate, this.Headers))

    @staticmethod
    def try_get_input_column(__unit: None=None) -> Callable[[ArcTable], CompositeColumn | None]:
        def _arrow769(table: ArcTable) -> CompositeColumn | None:
            return table.TryGetInputColumn()

        return _arrow769

    def GetInputColumn(self, __unit: None=None) -> CompositeColumn:
        this: ArcTable = self
        match_value: CompositeColumn | None = this.TryGetInputColumn()
        if match_value is None:
            arg: str = this.Name
            return to_fail(printf("Unable to find input column in table %s"))(arg)

        else: 
            return match_value


    @staticmethod
    def get_input_column(__unit: None=None) -> Callable[[ArcTable], CompositeColumn]:
        def _arrow770(table: ArcTable) -> CompositeColumn:
            return table.GetInputColumn()

        return _arrow770

    def TryGetOutputColumn(self, __unit: None=None) -> CompositeColumn | None:
        this: ArcTable = self
        def mapping(i: int) -> CompositeColumn:
            return this.GetColumn(i)

        def predicate(x: CompositeHeader) -> bool:
            return x.is_output

        return map_1(mapping, try_find_index(predicate, this.Headers))

    @staticmethod
    def try_get_output_column(__unit: None=None) -> Callable[[ArcTable], CompositeColumn | None]:
        def _arrow771(table: ArcTable) -> CompositeColumn | None:
            return table.TryGetOutputColumn()

        return _arrow771

    def GetOutputColumn(self, __unit: None=None) -> CompositeColumn:
        this: ArcTable = self
        match_value: CompositeColumn | None = this.TryGetOutputColumn()
        if match_value is None:
            arg: str = this.Name
            return to_fail(printf("Unable to find output column in table %s"))(arg)

        else: 
            return match_value


    @staticmethod
    def get_output_column(__unit: None=None) -> Callable[[ArcTable], CompositeColumn]:
        def _arrow772(table: ArcTable) -> CompositeColumn:
            return table.GetOutputColumn()

        return _arrow772

    def MoveColumn(self, start_col: int, end_col: int) -> None:
        this: ArcTable = self
        if start_col == end_col:
            pass

        elif True if (start_col < 0) else (start_col >= this.ColumnCount):
            to_fail(printf("Cannt move column. Invalid start column index: %i"))(start_col)

        elif True if (end_col < 0) else (end_col >= this.ColumnCount):
            to_fail(printf("Cannt move column. Invalid end column index: %i"))(end_col)

        else: 
            Unchecked_moveColumnTo(start_col, end_col, this.Headers, this._values)


    @staticmethod
    def move_column(start_col: int, end_col: int) -> Callable[[ArcTable], ArcTable]:
        def _arrow773(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.MoveColumn(start_col, end_col)
            return new_table

        return _arrow773

    def AddRow(self, cells: Array[CompositeCell] | None=None, index: int | None=None) -> None:
        this: ArcTable = self
        index_1: int = default_arg(index, this.RowCount) or 0
        SanityChecks_validateRowIndex(index_1, this.RowCount, True)
        if cells is not None:
            cells_1: Array[CompositeCell] = cells
            column_count: int = this.ColumnCount or 0
            new_cells_count: int = length(cells_1) or 0
            if column_count == 0:
                raise Exception("Table contains no columns! Cannot add row to empty table!")

            elif new_cells_count != column_count:
                raise Exception(((("Cannot add a new row with " + str(new_cells_count)) + " cells, as the table has ") + str(column_count)) + " columns.")

            for column_index in range(0, (this.ColumnCount - 1) + 1, 1):
                h: CompositeHeader = this.Headers[column_index]
                column: CompositeColumn = CompositeColumn.create(h, [cells_1[column_index]])
                ignore(cells_1[column_index].ValidateAgainstHeader(h, True))
            Unchecked_addRow(index_1, cells_1, this.Headers, this._values)

        else: 
            Unchecked_addEmptyRow(index_1, this._values)


    @staticmethod
    def add_row(cells: Array[CompositeCell] | None=None, index: int | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow774(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.AddRow(cells, index)
            return new_table

        return _arrow774

    def UpdateRow(self, row_index: int, cells: Array[CompositeCell]) -> None:
        this: ArcTable = self
        SanityChecks_validateRowIndex(row_index, this.RowCount, False)
        column_count: int = this.RowCount or 0
        new_cells_count: int = length(cells) or 0
        if column_count == 0:
            raise Exception("Table contains no columns! Cannot add row to empty table!")

        elif new_cells_count != column_count:
            raise Exception(((("Cannot add a new row with " + str(new_cells_count)) + " cells, as the table has ") + str(column_count)) + " columns.")

        def f(i: int, cell: CompositeCell) -> None:
            h: CompositeHeader = this.Headers[i]
            SanityChecks_validateColumn(CompositeColumn.create(h, ResizeArray_singleton(cell)))

        ResizeArray_iteri(f, cells)
        def f_1(column_index: int, cell_1: CompositeCell) -> None:
            Unchecked_setCellAt(column_index, row_index, cell_1, this._values)

        ResizeArray_iteri(f_1, cells)

    @staticmethod
    def update_row(row_index: int, cells: Array[CompositeCell]) -> Callable[[ArcTable], ArcTable]:
        def _arrow775(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.UpdateRow(row_index, cells)
            return new_table

        return _arrow775

    def AppendRow(self, cells: Array[CompositeCell] | None=None) -> None:
        this: ArcTable = self
        this.AddRow(cells, this.RowCount)

    @staticmethod
    def append_row(cells: Array[CompositeCell] | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow776(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.AppendRow(cells)
            return new_table

        return _arrow776

    def InsertRow(self, index: int, cells: Array[CompositeCell] | None=None) -> None:
        this: ArcTable = self
        this.AddRow(cells, index)

    @staticmethod
    def insert_row(index: int, cells: Array[CompositeCell] | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow777(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.AddRow(cells, index)
            return new_table

        return _arrow777

    def AddRows(self, rows: Array[Array[CompositeCell]], index: int | None=None) -> None:
        this: ArcTable = self
        index_1: int = default_arg(index, this.RowCount) or 0
        SanityChecks_validateRowIndex(index_1, this.RowCount, True)
        def f(row: Array[CompositeCell]) -> None:
            column_count: int = this.ColumnCount or 0
            new_cells_count: int = length(row) or 0
            if column_count == 0:
                raise Exception("Table contains no columns! Cannot add row to empty table!")

            elif new_cells_count != column_count:
                raise Exception(((("Cannot add a new row with " + str(new_cells_count)) + " cells, as the table has ") + str(column_count)) + " columns.")


        ResizeArray_iter(f, rows)
        enumerator: Any = get_enumerator(rows)
        try: 
            while enumerator.System_Collections_IEnumerator_MoveNext():
                row_1: Array[CompositeCell] = enumerator.System_Collections_Generic_IEnumerator_1_get_Current()
                for column_index in range(0, (this.ColumnCount - 1) + 1, 1):
                    h: CompositeHeader = this.Headers[column_index]
                    ignore(row_1[column_index].ValidateAgainstHeader(h, True))

        finally: 
            dispose(enumerator)

        Unchecked_addRows(index_1, rows, this.Headers, this._values)

    @staticmethod
    def add_rows(rows: Array[Array[CompositeCell]], index: int | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow778(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.AddRows(rows, index)
            return new_table

        return _arrow778

    def AddRowsEmpty(self, row_count: int, index: int | None=None) -> None:
        this: ArcTable = self
        def _arrow780(__unit: None=None) -> IEnumerable_1[CompositeCell]:
            def _arrow779(column_index: int) -> IEnumerable_1[CompositeCell]:
                return singleton(get_empty_cell_for_header(this.Headers[column_index], Unchecked_tryGetCellAt(column_index, 0, this._values)))

            return collect(_arrow779, range_big_int(0, 1, this.ColumnCount - 1))

        row: Array[CompositeCell] = list(to_array(delay(_arrow780)))
        def _arrow781(_arg: int) -> Array[CompositeCell]:
            return row

        rows: Array[Array[CompositeCell]] = ResizeArray_init(row_count, _arrow781)
        this.AddRows(rows, index)

    @staticmethod
    def add_rows_empty(row_count: int, index: int | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow782(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.AddRowsEmpty(row_count, index)
            return new_table

        return _arrow782

    def RemoveRow(self, index: int) -> None:
        this: ArcTable = self
        SanityChecks_validateRowIndex(index, this.RowCount, False)
        Unchecked_removeRowCells_withIndexChange(index, this._values)

    @staticmethod
    def remove_row(index: int) -> Callable[[ArcTable], ArcTable]:
        def _arrow783(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.RemoveRow(index)
            return new_table

        return _arrow783

    def RemoveRows(self, index_arr: Array[int]) -> None:
        this: ArcTable = self
        def _arrow784(index: int) -> None:
            SanityChecks_validateRowIndex(index, this.RowCount, False)

        iterate_2(_arrow784, index_arr)
        def _arrow785(index_1: int) -> None:
            this.RemoveRow(index_1)

        class ObjectExpr786:
            @property
            def Compare(self) -> Callable[[int, int], int]:
                return compare_primitives

        iterate_2(_arrow785, sort_descending(index_arr, ObjectExpr786()))

    @staticmethod
    def remove_rows(index_arr: Array[int]) -> Callable[[ArcTable], ArcTable]:
        def _arrow787(table: ArcTable) -> ArcTable:
            new_table: ArcTable = table.Copy()
            new_table.RemoveColumns(index_arr)
            return new_table

        return _arrow787

    def GetRow(self, row_index: int, SkipValidation: bool | None=None) -> Array[CompositeCell]:
        this: ArcTable = self
        if not equals(SkipValidation, True):
            SanityChecks_validateRowIndex(row_index, this.RowCount, False)

        def _arrow789(__unit: None=None) -> IEnumerable_1[CompositeCell]:
            def _arrow788(column_index: int) -> CompositeCell:
                return this.GetCellAt(column_index, row_index)

            return map(_arrow788, range_big_int(0, 1, this.ColumnCount - 1))

        return list(to_array(delay(_arrow789)))

    @staticmethod
    def get_row(index: int) -> Callable[[ArcTable], Array[CompositeCell]]:
        def _arrow790(table: ArcTable) -> Array[CompositeCell]:
            return table.GetRow(index)

        return _arrow790

    def Join(self, table: ArcTable, index: int | None=None, join_options: str | None=None, force_replace: bool | None=None) -> None:
        this: ArcTable = self
        join_options_1: str = default_arg(join_options, "headers")
        force_replace_1: bool = default_arg(force_replace, False)
        index_1: int = default_arg(index, this.ColumnCount) or 0
        index_1 = (this.ColumnCount if (index_1 == -1) else index_1) or 0
        SanityChecks_validateColumnIndex(index_1, this.ColumnCount, True)
        only_headers: bool = join_options_1 == "headers"
        columns: Array[CompositeColumn]
        pre: Array[CompositeColumn] = table.Columns
        def f_2(c_1: CompositeColumn) -> CompositeColumn:
            units_opt: Array[OntologyAnnotation] | None = c_1.TryGetColumnUnits()
            if units_opt is None:
                return CompositeColumn(c_1.Header, [])

            else: 
                def f_1(u: OntologyAnnotation, c_1: Any=c_1) -> CompositeCell:
                    return CompositeCell.create_unitized("", u)

                return CompositeColumn(c_1.Header, ResizeArray_map(f_1, units_opt))


        def f(c: CompositeColumn) -> CompositeColumn:
            return CompositeColumn(c.Header, [])

        columns = ResizeArray_map(f_2, pre) if (join_options_1 == "withUnit") else (pre if (join_options_1 == "withValues") else ResizeArray_map(f, pre))
        def mapping(x: CompositeColumn) -> CompositeHeader:
            return x.Header

        duplicates: FSharpList[dict[str, Any]] = try_find_duplicate_unique_in_array(map(mapping, columns))
        if not is_empty(duplicates):
            sb: Any = StringBuilder__ctor()
            ignore(StringBuilder__AppendLine_Z721C83C5(sb, "Found duplicate unique columns in `columns`."))
            def action(x_1: dict[str, Any]) -> None:
                ignore(StringBuilder__AppendLine_Z721C83C5(sb, ((((("Duplicate `" + str(x_1["HeaderType"])) + "` at index ") + str(x_1["Index1"])) + " and ") + str(x_1["Index2"])) + "."))

            iterate(action, duplicates)
            raise Exception(to_string(sb))

        def f_3(x_2: CompositeColumn) -> None:
            SanityChecks_validateColumn(x_2)

        ResizeArray_iter(f_3, columns)
        def f_4(col: CompositeColumn) -> None:
            nonlocal index_1
            prev_headers_count: int = len(this.Headers) or 0
            Unchecked_addColumn(col.Header, col.Cells, index_1, force_replace_1, only_headers, this.Headers, this._values)
            if len(this.Headers) > prev_headers_count:
                index_1 = (index_1 + 1) or 0


        ResizeArray_iter(f_4, columns)

    @staticmethod
    def join(table: ArcTable, index: int | None=None, join_options: str | None=None, force_replace: bool | None=None) -> Callable[[ArcTable], ArcTable]:
        def _arrow791(this: ArcTable) -> ArcTable:
            copy: ArcTable = this.Copy()
            copy.Join(table, index, join_options, force_replace)
            return copy

        return _arrow791

    def AddProtocolTypeColumn(self, types: Array[OntologyAnnotation] | None=None, index: int | None=None, force_replace: bool | None=None) -> None:
        this: ArcTable = self
        def mapping(a: Array[OntologyAnnotation]) -> Array[CompositeCell]:
            def f(Item: OntologyAnnotation, a: Any=a) -> CompositeCell:
                return CompositeCell(0, Item)

            return ResizeArray_map(f, a)

        cells: Array[CompositeCell] | None = map_1(mapping, types)
        this.AddColumn(CompositeHeader(4), cells, index, force_replace)

    def AddProtocolVersionColumn(self, versions: Array[str] | None=None, index: int | None=None, force_replace: bool | None=None) -> None:
        this: ArcTable = self
        def mapping(a: Array[str]) -> Array[CompositeCell]:
            def f(Item: str, a: Any=a) -> CompositeCell:
                return CompositeCell(1, Item)

            return ResizeArray_map(f, a)

        cells: Array[CompositeCell] | None = map_1(mapping, versions)
        this.AddColumn(CompositeHeader(7), cells, index, force_replace)

    def AddProtocolUriColumn(self, uris: Array[str] | None=None, index: int | None=None, force_replace: bool | None=None) -> None:
        this: ArcTable = self
        def mapping(a: Array[str]) -> Array[CompositeCell]:
            def f(Item: str, a: Any=a) -> CompositeCell:
                return CompositeCell(1, Item)

            return ResizeArray_map(f, a)

        cells: Array[CompositeCell] | None = map_1(mapping, uris)
        this.AddColumn(CompositeHeader(6), cells, index, force_replace)

    def AddProtocolDescriptionColumn(self, descriptions: Array[str] | None=None, index: int | None=None, force_replace: bool | None=None) -> None:
        this: ArcTable = self
        def mapping(a: Array[str]) -> Array[CompositeCell]:
            def f(Item: str, a: Any=a) -> CompositeCell:
                return CompositeCell(1, Item)

            return ResizeArray_map(f, a)

        cells: Array[CompositeCell] | None = map_1(mapping, descriptions)
        this.AddColumn(CompositeHeader(5), cells, index, force_replace)

    def AddProtocolNameColumn(self, names: Array[str] | None=None, index: int | None=None, force_replace: bool | None=None) -> None:
        this: ArcTable = self
        def mapping(a: Array[str]) -> Array[CompositeCell]:
            def f(Item: str, a: Any=a) -> CompositeCell:
                return CompositeCell(1, Item)

            return ResizeArray_map(f, a)

        cells: Array[CompositeCell] | None = map_1(mapping, names)
        this.AddColumn(CompositeHeader(8), cells, index, force_replace)

    def GetProtocolTypeColumn(self, __unit: None=None) -> CompositeColumn:
        this: ArcTable = self
        return this.GetColumnByHeader(CompositeHeader(4))

    def GetProtocolVersionColumn(self, __unit: None=None) -> CompositeColumn:
        this: ArcTable = self
        return this.GetColumnByHeader(CompositeHeader(7))

    def GetProtocolUriColumn(self, __unit: None=None) -> CompositeColumn:
        this: ArcTable = self
        return this.GetColumnByHeader(CompositeHeader(6))

    def GetProtocolDescriptionColumn(self, __unit: None=None) -> CompositeColumn:
        this: ArcTable = self
        return this.GetColumnByHeader(CompositeHeader(5))

    def GetProtocolNameColumn(self, __unit: None=None) -> CompositeColumn:
        this: ArcTable = self
        return this.GetColumnByHeader(CompositeHeader(8))

    def TryGetProtocolNameColumn(self, __unit: None=None) -> CompositeColumn | None:
        this: ArcTable = self
        return this.TryGetColumnByHeader(CompositeHeader(8))

    def GetComponentColumns(self, __unit: None=None) -> Array[CompositeColumn]:
        this: ArcTable = self
        def f(h: CompositeHeader) -> CompositeColumn | None:
            if h.is_component:
                return this.GetColumnByHeader(h)

            else: 
                return None


        return ResizeArray_choose(f, this.Headers)

    def RescanValueMap(self, __unit: None=None) -> None:
        this: ArcTable = self
        this._values.RescanValueMap()

    @staticmethod
    def SplitByColumnValues(column_index: int) -> Callable[[ArcTable], Array[ArcTable]]:
        def _arrow792(table: ArcTable) -> Array[ArcTable]:
            def f_4(i: int, index_group: Array[int]) -> ArcTable:
                headers: Array[CompositeHeader] = table.Headers
                def f_3(i_1: int, i: Any=i, index_group: Any=index_group) -> Array[CompositeCell]:
                    return table.GetRow(i_1, True)

                rows: Array[Array[CompositeCell]] = ResizeArray_map(f_3, index_group)
                return ArcTable.create_from_rows(table.Name, headers, rows)

            def f_2(tupled_arg: tuple[CompositeCell, Array[tuple[int, CompositeCell]]]) -> Array[int]:
                def f_1(tuple_1: tuple[int, CompositeCell], tupled_arg: Any=tupled_arg) -> int:
                    return tuple_1[0]

                return ResizeArray_map(f_1, tupled_arg[1])

            def f(tuple: tuple[int, CompositeCell]) -> CompositeCell:
                return tuple[1]

            return ResizeArray_mapi(f_4, ResizeArray_map(f_2, ResizeArray_groupBy(f, ResizeArray_indexed(table.GetColumn(column_index).Cells))))

        return _arrow792

    @staticmethod
    def SplitByColumnValuesByHeader(header: CompositeHeader) -> Callable[[ArcTable], Array[ArcTable]]:
        def _arrow793(table: ArcTable) -> Array[ArcTable]:
            def predicate(x: CompositeHeader) -> bool:
                return equals(x, header)

            index: int | None = try_find_index(predicate, table.Headers)
            if index is None:
                return ResizeArray_singleton(table.Copy())

            else: 
                i: int = index or 0
                return ArcTable.SplitByColumnValues(i)(table)


        return _arrow793

    @staticmethod
    def SplitByProtocolREF() -> Callable[[ArcTable], Array[ArcTable]]:
        def _arrow794(table: ArcTable) -> Array[ArcTable]:
            return ArcTable.SplitByColumnValuesByHeader(CompositeHeader(8))(table)

        return _arrow794

    @staticmethod
    def update_reference_by_annotation_table(ref_table: ArcTable, annotation_table: ArcTable) -> ArcTable:
        ref_table_1: ArcTable = ref_table.Copy()
        annotation_table_1: ArcTable = annotation_table.Copy()
        def chooser(tupled_arg: tuple[int, CompositeHeader]) -> int | None:
            if tupled_arg[1].is_protocol_column:
                return None

            else: 
                return tupled_arg[0]


        non_protocol_columns: Array[int] = to_array(choose(chooser, indexed(ref_table_1.Headers)))
        ref_table_1.RemoveColumns(non_protocol_columns)
        ref_table_1.RowCount = annotation_table_1.RowCount or 0
        enumerator: Any = get_enumerator(annotation_table_1.Columns)
        try: 
            while enumerator.System_Collections_IEnumerator_MoveNext():
                c: CompositeColumn = enumerator.System_Collections_Generic_IEnumerator_1_get_Current()
                ref_table_1.AddColumn(c.Header, c.Cells, None, True)

        finally: 
            dispose(enumerator)

        return ref_table_1

    @staticmethod
    def append(table1: ArcTable, table2: ArcTable) -> ArcTable:
        def get_list(t: ArcTable) -> FSharpList[FSharpList[tuple[CompositeHeader, CompositeCell]]]:
            def _arrow796(__unit: None=None, t: Any=t) -> IEnumerable_1[FSharpList[tuple[CompositeHeader, CompositeCell]]]:
                def _arrow795(row: int) -> FSharpList[tuple[CompositeHeader, CompositeCell]]:
                    def mapping(i: int, c: CompositeCell) -> tuple[CompositeHeader, CompositeCell]:
                        return (t.Headers[i], c)

                    return to_list(map_indexed(mapping, t.GetRow(row, True)))

                return map(_arrow795, range_big_int(0, 1, t.RowCount - 1))

            return to_list(delay(_arrow796))

        pattern_input: tuple[Array[CompositeHeader], ArcTableValues] = Unchecked_alignByHeaders(False, append(get_list(table1), get_list(table2)))
        return ArcTable.from_arc_table_values(table1.Name, pattern_input[0], pattern_input[1])

    def __str__(self, __unit: None=None) -> str:
        this: ArcTable = self
        row_count: int = this.RowCount or 0
        def _arrow805(__unit: None=None) -> IEnumerable_1[str]:
            def _arrow804(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow803(__unit: None=None) -> IEnumerable_1[str]:
                    def _arrow802(__unit: None=None) -> IEnumerable_1[str]:
                        def _arrow797(row_i: int) -> str:
                            return join("\t|\t", map(to_string, this.GetRow(row_i)))

                        def _arrow800(__unit: None=None) -> IEnumerable_1[str]:
                            def _arrow799(__unit: None=None) -> IEnumerable_1[str]:
                                def _arrow798(row_i_1: int) -> str:
                                    return join("\t|\t", map(to_string, this.GetRow(row_i_1)))

                                return map(_arrow798, range_big_int(row_count - 20, 1, row_count - 1))

                            return append_1(singleton("..."), delay(_arrow799))

                        def _arrow801(row_i_2: int) -> str:
                            return join("\t|\t", map(to_string, this.GetRow(row_i_2)))

                        return append_1(map(_arrow797, range_big_int(0, 1, 19)), delay(_arrow800)) if (row_count > 50) else (singleton("No rows") if (row_count == 0) else map(_arrow801, range_big_int(0, 1, row_count - 1)))

                    return append_1(singleton(join("\t|\t", map(to_string, this.Headers))), delay(_arrow802))

                return append_1(singleton("-------------"), delay(_arrow803))

            return append_1(singleton(("Table: " + this.Name) + ""), delay(_arrow804))

        return join("\n", to_list(delay(_arrow805)))

    def StructurallyEquals(self, other: ArcTable) -> bool:
        this: ArcTable = self
        return safe_hash(this) == safe_hash(other)

    def ReferenceEquals(self, other: ArcTable) -> bool:
        this: ArcTable = self
        return this is other

    def __eq__(self, other: Any=None) -> bool:
        this: ArcTable = self
        return this.StructurallyEquals(other) if isinstance(other, ArcTable) else False

    def __hash__(self, __unit: None=None) -> Any:
        this: ArcTable = self
        v_hash: int = safe_hash(this._values) or 0
        return box_hash_array([this.Name, box_hash_seq(this.Headers), v_hash])


ArcTable_reflection = _expr806

def ArcTable__ctor_2D310C9B(name: str, headers: Array[CompositeHeader] | None=None, columns: Array[Array[CompositeCell]] | None=None) -> ArcTable:
    return ArcTable(name, headers, columns)


__all__ = ["ArcTable_reflection"]

