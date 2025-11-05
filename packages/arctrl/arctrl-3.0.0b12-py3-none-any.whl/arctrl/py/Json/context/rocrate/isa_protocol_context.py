from __future__ import annotations
from dataclasses import dataclass
from typing import (Any, TypeVar)
from ....fable_modules.fable_library.reflection import (TypeInfo, string_type, record_type)
from ....fable_modules.fable_library.seq import map
from ....fable_modules.fable_library.types import Record
from ....fable_modules.fable_library.util import (to_enumerable, IEnumerable_1)
from ....fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1)

__A_ = TypeVar("__A_")

def _expr1839() -> TypeInfo:
    return record_type("ARCtrl.Json.ROCrateContext.Protocol.IContext", [], IContext, lambda: [("sdo", string_type), ("arc", string_type), ("Protocol", string_type), ("ArcProtocol", string_type), ("name", string_type), ("protocol_type", string_type), ("description", string_type), ("version", string_type), ("components", string_type), ("parameters", string_type), ("uri", string_type), ("comments", string_type)])


@dataclass(eq = False, repr = False, slots = True)
class IContext(Record):
    sdo: str
    arc: str
    Protocol: str
    ArcProtocol: str
    name: str
    protocol_type: str
    description: str
    version: str
    components: str
    parameters: str
    uri: str
    comments: str

IContext_reflection = _expr1839

def _arrow1853(__unit: None=None) -> IEncodable:
    class ObjectExpr1840(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string("http://schema.org/")

    class ObjectExpr1841(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
            return helpers_1.encode_string("https://bioschemas.org/")

    class ObjectExpr1842(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
            return helpers_2.encode_string("bio:LabProtocol")

    class ObjectExpr1843(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
            return helpers_3.encode_string("sdo:name")

    class ObjectExpr1844(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
            return helpers_4.encode_string("bio:intendedUse")

    class ObjectExpr1845(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
            return helpers_5.encode_string("sdo:description")

    class ObjectExpr1846(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any]) -> Any:
            return helpers_6.encode_string("sdo:version")

    class ObjectExpr1847(IEncodable):
        def Encode(self, helpers_7: IEncoderHelpers_1[Any]) -> Any:
            return helpers_7.encode_string("bio:labEquipment")

    class ObjectExpr1848(IEncodable):
        def Encode(self, helpers_8: IEncoderHelpers_1[Any]) -> Any:
            return helpers_8.encode_string("bio:reagent")

    class ObjectExpr1849(IEncodable):
        def Encode(self, helpers_9: IEncoderHelpers_1[Any]) -> Any:
            return helpers_9.encode_string("bio:computationalTool")

    class ObjectExpr1850(IEncodable):
        def Encode(self, helpers_10: IEncoderHelpers_1[Any]) -> Any:
            return helpers_10.encode_string("sdo:url")

    class ObjectExpr1851(IEncodable):
        def Encode(self, helpers_11: IEncoderHelpers_1[Any]) -> Any:
            return helpers_11.encode_string("sdo:comment")

    values: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("sdo", ObjectExpr1840()), ("bio", ObjectExpr1841()), ("Protocol", ObjectExpr1842()), ("name", ObjectExpr1843()), ("protocolType", ObjectExpr1844()), ("description", ObjectExpr1845()), ("version", ObjectExpr1846()), ("components", ObjectExpr1847()), ("reagents", ObjectExpr1848()), ("computationalTools", ObjectExpr1849()), ("uri", ObjectExpr1850()), ("comments", ObjectExpr1851())])
    class ObjectExpr1852(IEncodable):
        def Encode(self, helpers_12: IEncoderHelpers_1[Any]) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_12))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_12.encode_object(arg)

    return ObjectExpr1852()


context_jsonvalue: IEncodable = _arrow1853()

__all__ = ["IContext_reflection", "context_jsonvalue"]

