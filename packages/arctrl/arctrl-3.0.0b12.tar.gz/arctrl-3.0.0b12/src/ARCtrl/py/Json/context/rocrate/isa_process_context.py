from __future__ import annotations
from dataclasses import dataclass
from typing import (Any, TypeVar)
from ....fable_modules.fable_library.reflection import (TypeInfo, string_type, record_type)
from ....fable_modules.fable_library.seq import map
from ....fable_modules.fable_library.types import Record
from ....fable_modules.fable_library.util import (to_enumerable, IEnumerable_1)
from ....fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1)

__A_ = TypeVar("__A_")

def _expr1813() -> TypeInfo:
    return record_type("ARCtrl.Json.ROCrateContext.Process.IContext", [], IContext, lambda: [("sdo", string_type), ("arc", string_type), ("Process", string_type), ("ArcProcess", string_type), ("name", string_type), ("executes_protocol", string_type), ("performer", string_type), ("date", string_type), ("previous_process", string_type), ("next_process", string_type), ("input", string_type), ("output", string_type), ("comments", string_type)])


@dataclass(eq = False, repr = False, slots = True)
class IContext(Record):
    sdo: str
    arc: str
    Process: str
    ArcProcess: str
    name: str
    executes_protocol: str
    performer: str
    date: str
    previous_process: str
    next_process: str
    input: str
    output: str
    comments: str

IContext_reflection = _expr1813

def _arrow1826(__unit: None=None) -> IEncodable:
    class ObjectExpr1814(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string("http://schema.org/")

    class ObjectExpr1815(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
            return helpers_1.encode_string("https://bioschemas.org/")

    class ObjectExpr1816(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
            return helpers_2.encode_string("bio:LabProcess")

    class ObjectExpr1817(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
            return helpers_3.encode_string("sdo:name")

    class ObjectExpr1818(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
            return helpers_4.encode_string("bio:executesLabProtocol")

    class ObjectExpr1819(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
            return helpers_5.encode_string("bio:parameterValue")

    class ObjectExpr1820(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any]) -> Any:
            return helpers_6.encode_string("sdo:agent")

    class ObjectExpr1821(IEncodable):
        def Encode(self, helpers_7: IEncoderHelpers_1[Any]) -> Any:
            return helpers_7.encode_string("sdo:endTime")

    class ObjectExpr1822(IEncodable):
        def Encode(self, helpers_8: IEncoderHelpers_1[Any]) -> Any:
            return helpers_8.encode_string("sdo:object")

    class ObjectExpr1823(IEncodable):
        def Encode(self, helpers_9: IEncoderHelpers_1[Any]) -> Any:
            return helpers_9.encode_string("sdo:result")

    class ObjectExpr1824(IEncodable):
        def Encode(self, helpers_10: IEncoderHelpers_1[Any]) -> Any:
            return helpers_10.encode_string("sdo:disambiguatingDescription")

    values: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("sdo", ObjectExpr1814()), ("bio", ObjectExpr1815()), ("Process", ObjectExpr1816()), ("name", ObjectExpr1817()), ("executesProtocol", ObjectExpr1818()), ("parameterValues", ObjectExpr1819()), ("performer", ObjectExpr1820()), ("date", ObjectExpr1821()), ("inputs", ObjectExpr1822()), ("outputs", ObjectExpr1823()), ("comments", ObjectExpr1824())])
    class ObjectExpr1825(IEncodable):
        def Encode(self, helpers_11: IEncoderHelpers_1[Any]) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_11))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_11.encode_object(arg)

    return ObjectExpr1825()


context_jsonvalue: IEncodable = _arrow1826()

__all__ = ["IContext_reflection", "context_jsonvalue"]

