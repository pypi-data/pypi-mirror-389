from __future__ import annotations
from collections.abc import Callable
from typing import Any
from ...fable_modules.fable_library.array_ import (skip, map, try_item)
from ...fable_modules.fable_library.list import (of_array, singleton as singleton_1, FSharpList, map as map_2)
from ...fable_modules.fable_library.map_util import (try_get_value, get_item_from_dict)
from ...fable_modules.fable_library.option import default_arg
from ...fable_modules.fable_library.range import range_big_int
from ...fable_modules.fable_library.seq import (to_array, delay, map as map_1, exists, to_list, append, singleton, reduce)
from ...fable_modules.fable_library.types import (Array, to_string)
from ...fable_modules.fable_library.util import (IEnumerable_1, string_hash)
from ...fable_modules.fs_spreadsheet.Cells.fs_cell import FsCell
from ...fable_modules.fs_spreadsheet.fs_column import FsColumn
from ...fable_modules.fs_spreadsheet.hash_codes import merge_hashes
from ...fable_modules.fable_library.types import FSharpRef
from ...Core.Table.arc_table_aux import (ColumnValueRefs, ensure_cell_hash_in_value_map)
from ...Core.Table.composite_cell import CompositeCell
from ...Core.Table.composite_column import CompositeColumn
from ...Core.Table.composite_header import (IOType, CompositeHeader)
from .composite_cell import to_string_cells as to_string_cells_1
from .composite_header import (from_string_cells, to_string_cells)

def fix_deprecated_ioheader(string_cell_col: Array[str]) -> Array[str]:
    if len(string_cell_col) == 0:
        raise Exception("Can\'t fix IOHeader Invalid column, neither header nor values given")

    values: Array[str] = skip(1, string_cell_col, None)
    match_value: IOType = IOType.of_string(string_cell_col[0])
    if match_value.tag == 4:
        return string_cell_col

    elif match_value.tag == 0:
        string_cell_col[0] = to_string(CompositeHeader(11, IOType(0)))
        return string_cell_col

    else: 
        string_cell_col[0] = to_string(CompositeHeader(12, match_value))
        return string_cell_col



def from_string_cell_columns(columns: Array[Array[str]]) -> CompositeColumn:
    def mapping(c: Array[str], columns: Any=columns) -> str:
        return c[0]

    pattern_input: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = from_string_cells(map(mapping, columns, None))
    l: int = len(columns[0]) or 0
    def _arrow1318(__unit: None=None, columns: Any=columns) -> IEnumerable_1[CompositeCell]:
        def _arrow1317(i: int) -> CompositeCell:
            def mapping_1(c_1: Array[str]) -> str:
                return c_1[i]

            return pattern_input[1](map(mapping_1, columns, None))

        return map_1(_arrow1317, range_big_int(1, 1, l - 1))

    cells: Array[CompositeCell] = list(to_array(delay(_arrow1318)))
    return CompositeColumn.create(pattern_input[0], cells)


def string_cell_columns_of_fs_columns(columns: Array[FsColumn]) -> Array[Array[str]]:
    def mapping_1(c: FsColumn, columns: Any=columns) -> Array[str]:
        c.ToDenseColumn()
        def mapping(cell: FsCell, c: Any=c) -> str:
            return cell.ValueAsString()

        return map(mapping, to_array(c.Cells), None)

    return map(mapping_1, columns, None)


def from_fs_columns(columns: Array[FsColumn]) -> CompositeColumn:
    def mapping_1(c: FsColumn, columns: Any=columns) -> Array[str]:
        c.ToDenseColumn()
        def mapping(c_1: FsCell, c: Any=c) -> str:
            return c_1.ValueAsString()

        return map(mapping, to_array(c.Cells), None)

    return from_string_cell_columns(map(mapping_1, columns, None))


def to_string_cell_columns(column: CompositeColumn) -> FSharpList[FSharpList[str]]:
    def predicate(c: CompositeCell, column: Any=column) -> bool:
        return c.is_unitized

    has_unit: bool = exists(predicate, column.Cells)
    is_term: bool = column.Header.IsTermColumn
    def predicate_1(c_1: CompositeCell, column: Any=column) -> bool:
        return c_1.is_data

    is_data: bool = exists(predicate_1, column.Cells) if column.Header.IsDataColumn else False
    header: Array[str] = to_string_cells(has_unit, column.Header)
    composite_cells: Array[CompositeCell] = to_array(column.Cells)
    def mapping(cell: CompositeCell, column: Any=column) -> Array[str]:
        return to_string_cells_1(is_term, has_unit, cell)

    cells: Array[Array[str]] = map(mapping, to_array(column.Cells), None)
    def get_cell_or_default(ri: int, ci: int, cells_1: Array[Array[str]], column: Any=column) -> str:
        return default_arg(try_item(ci, cells_1[ri]), "")

    if has_unit:
        def _arrow1324(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1323(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1322(i: int) -> str:
                    return get_cell_or_default(i, 0, cells)

                return map_1(_arrow1322, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[0]), delay(_arrow1323))

        def _arrow1327(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1326(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1325(i_1: int) -> str:
                    return get_cell_or_default(i_1, 1, cells)

                return map_1(_arrow1325, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[1]), delay(_arrow1326))

        def _arrow1330(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1329(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1328(i_2: int) -> str:
                    return get_cell_or_default(i_2, 2, cells)

                return map_1(_arrow1328, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[2]), delay(_arrow1329))

        def _arrow1333(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1332(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1331(i_3: int) -> str:
                    return get_cell_or_default(i_3, 3, cells)

                return map_1(_arrow1331, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[3]), delay(_arrow1332))

        return of_array([to_list(delay(_arrow1324)), to_list(delay(_arrow1327)), to_list(delay(_arrow1330)), to_list(delay(_arrow1333))])

    elif is_term:
        def _arrow1339(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1338(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1337(i_4: int) -> str:
                    return get_cell_or_default(i_4, 0, cells)

                return map_1(_arrow1337, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[0]), delay(_arrow1338))

        def _arrow1342(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1341(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1340(i_5: int) -> str:
                    return get_cell_or_default(i_5, 1, cells)

                return map_1(_arrow1340, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[1]), delay(_arrow1341))

        def _arrow1345(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1344(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1343(i_6: int) -> str:
                    return get_cell_or_default(i_6, 2, cells)

                return map_1(_arrow1343, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[2]), delay(_arrow1344))

        return of_array([to_list(delay(_arrow1339)), to_list(delay(_arrow1342)), to_list(delay(_arrow1345))])

    elif is_data:
        def _arrow1351(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1350(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1349(i_7: int) -> str:
                    return get_cell_or_default(i_7, 0, cells)

                return map_1(_arrow1349, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[0]), delay(_arrow1350))

        def _arrow1354(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1353(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1352(i_8: int) -> str:
                    return get_cell_or_default(i_8, 1, cells)

                return map_1(_arrow1352, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[1]), delay(_arrow1353))

        def _arrow1357(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1356(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1355(i_9: int) -> str:
                    return get_cell_or_default(i_9, 2, cells)

                return map_1(_arrow1355, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[2]), delay(_arrow1356))

        return of_array([to_list(delay(_arrow1351)), to_list(delay(_arrow1354)), to_list(delay(_arrow1357))])

    else: 
        def _arrow1360(__unit: None=None, column: Any=column) -> IEnumerable_1[str]:
            def _arrow1359(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1358(i_10: int) -> str:
                    return cells[i_10][0]

                return map_1(_arrow1358, range_big_int(0, 1, len(composite_cells) - 1))

            return append(singleton(header[0]), delay(_arrow1359))

        return singleton_1(to_list(delay(_arrow1360)))



def to_fs_columns(column: CompositeColumn) -> FSharpList[FSharpList[FsCell]]:
    def mapping_1(c: FSharpList[str], column: Any=column) -> FSharpList[FsCell]:
        def mapping(s: str, c: Any=c) -> FsCell:
            return FsCell(s)

        return map_2(mapping, c)

    return map_2(mapping_1, to_string_cell_columns(column))


def ColumnValueRefs_fromStringCellColumns(value_map: Any, columns: Array[Array[str]]) -> tuple[CompositeHeader, ColumnValueRefs]:
    hash_map: Any = dict([])
    cells: Any = dict([])
    constant: bool = True
    def mapping(c: Array[str], value_map: Any=value_map, columns: Any=columns) -> str:
        return c[0]

    pattern_input: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = from_string_cells(map(mapping, columns, None))
    header: CompositeHeader = pattern_input[0]
    cell_parser: Callable[[Array[str]], CompositeCell] = pattern_input[1]
    l: int = len(columns[0]) or 0
    if l == 1:
        return (header, ColumnValueRefs(1, cells))

    else: 
        for i in range(1, (l - 1) + 1, 1):
            def mapping_1(c_1: Array[str], value_map: Any=value_map, columns: Any=columns) -> str:
                return c_1[i]

            strings: Array[str] = map(mapping_1, columns, None)
            def _arrow1361(hash_1: int, hash_2: int, value_map: Any=value_map, columns: Any=columns) -> int:
                return merge_hashes(hash_1, hash_2)

            def mapping_2(s: str, value_map: Any=value_map, columns: Any=columns) -> int:
                return string_hash(s)

            hash_3: int = reduce(_arrow1361, map_1(mapping_2, strings)) or 0
            match_value: int | None
            pattern_input_1: tuple[bool, int]
            out_arg: int = None or 0
            def _arrow1362(__unit: None=None, value_map: Any=value_map, columns: Any=columns) -> int:
                return out_arg

            def _arrow1363(v: int, value_map: Any=value_map, columns: Any=columns) -> None:
                nonlocal out_arg
                out_arg = v or 0

            pattern_input_1 = (try_get_value(hash_map, hash_3, FSharpRef(_arrow1362, _arrow1363)), out_arg)
            match_value = pattern_input_1[1] if pattern_input_1[0] else None
            if match_value is None:
                if i == 1:
                    cell_hash_3: int = ensure_cell_hash_in_value_map(cell_parser(strings), value_map) or 0
                    hash_map[hash_3] = cell_hash_3
                    cells[i - 1] = cell_hash_3

                else: 
                    if constant:
                        constant = False
                        for j in range(0, (i - 1) + 1, 1):
                            cell_hash_4: int = get_item_from_dict(cells, 0) or 0
                            cells[j] = cell_hash_4

                    cell_hash_5: int = ensure_cell_hash_in_value_map(cell_parser(strings), value_map) or 0
                    hash_map[hash_3] = cell_hash_5
                    cells[i - 1] = cell_hash_5


            else: 
                def _arrow1364(__unit: None=None, value_map: Any=value_map, columns: Any=columns) -> bool:
                    cell_hash: int = match_value or 0
                    return constant

                if _arrow1364():
                    cell_hash_1: int = match_value or 0

                else: 
                    cell_hash_2: int = match_value or 0
                    cells[i - 1] = cell_hash_2


        if constant:
            return (header, ColumnValueRefs(0, get_item_from_dict(cells, 0)))

        else: 
            return (header, ColumnValueRefs(1, cells))




__all__ = ["fix_deprecated_ioheader", "from_string_cell_columns", "string_cell_columns_of_fs_columns", "from_fs_columns", "to_string_cell_columns", "to_fs_columns", "ColumnValueRefs_fromStringCellColumns"]

