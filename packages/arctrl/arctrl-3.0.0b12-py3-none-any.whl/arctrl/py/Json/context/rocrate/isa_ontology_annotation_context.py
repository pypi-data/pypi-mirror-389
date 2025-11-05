from __future__ import annotations
from dataclasses import dataclass
from typing import (Any, TypeVar)
from ....fable_modules.fable_library.reflection import (TypeInfo, string_type, record_type)
from ....fable_modules.fable_library.seq import map
from ....fable_modules.fable_library.types import Record
from ....fable_modules.fable_library.util import (to_enumerable, IEnumerable_1)
from ....fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1)

__A_ = TypeVar("__A_")

def _expr1767() -> TypeInfo:
    return record_type("ARCtrl.Json.ROCrateContext.OntologyAnnotation.IContext", [], IContext, lambda: [("sdo", string_type), ("arc", string_type), ("OntologyAnnotation", string_type), ("annotation_value", string_type), ("term_source", string_type), ("term_accession", string_type), ("comments", string_type)])


@dataclass(eq = False, repr = False, slots = True)
class IContext(Record):
    sdo: str
    arc: str
    OntologyAnnotation: str
    annotation_value: str
    term_source: str
    term_accession: str
    comments: str

IContext_reflection = _expr1767

def _arrow1775(__unit: None=None) -> IEncodable:
    class ObjectExpr1768(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string("http://schema.org/")

    class ObjectExpr1769(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
            return helpers_1.encode_string("sdo:DefinedTerm")

    class ObjectExpr1770(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
            return helpers_2.encode_string("sdo:name")

    class ObjectExpr1771(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
            return helpers_3.encode_string("sdo:inDefinedTermSet")

    class ObjectExpr1772(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
            return helpers_4.encode_string("sdo:termCode")

    class ObjectExpr1773(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
            return helpers_5.encode_string("sdo:disambiguatingDescription")

    values: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("sdo", ObjectExpr1768()), ("OntologyAnnotation", ObjectExpr1769()), ("annotationValue", ObjectExpr1770()), ("termSource", ObjectExpr1771()), ("termAccession", ObjectExpr1772()), ("comments", ObjectExpr1773())])
    class ObjectExpr1774(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any]) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_6))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_6.encode_object(arg)

    return ObjectExpr1774()


context_jsonvalue: IEncodable = _arrow1775()

__all__ = ["IContext_reflection", "context_jsonvalue"]

