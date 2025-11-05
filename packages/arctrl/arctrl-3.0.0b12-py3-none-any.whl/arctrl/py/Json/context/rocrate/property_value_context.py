from __future__ import annotations
from typing import (Any, TypeVar)
from ....fable_modules.fable_library.seq import map
from ....fable_modules.fable_library.util import (to_enumerable, IEnumerable_1)
from ....fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1)

__A_ = TypeVar("__A_")

def _arrow1654(__unit: None=None) -> IEncodable:
    class ObjectExpr1640(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string("http://schema.org/")

    class ObjectExpr1641(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
            return helpers_1.encode_string("sdo:additionalType")

    class ObjectExpr1643(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
            return helpers_2.encode_string("sdo:alternateName")

    class ObjectExpr1644(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
            return helpers_3.encode_string("sdo:measurementMethod")

    class ObjectExpr1645(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
            return helpers_4.encode_string("sdo:description")

    class ObjectExpr1646(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
            return helpers_5.encode_string("sdo:name")

    class ObjectExpr1647(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any]) -> Any:
            return helpers_6.encode_string("sdo:propertyID")

    class ObjectExpr1648(IEncodable):
        def Encode(self, helpers_7: IEncoderHelpers_1[Any]) -> Any:
            return helpers_7.encode_string("sdo:value")

    class ObjectExpr1649(IEncodable):
        def Encode(self, helpers_8: IEncoderHelpers_1[Any]) -> Any:
            return helpers_8.encode_string("sdo:valueReference")

    class ObjectExpr1650(IEncodable):
        def Encode(self, helpers_9: IEncoderHelpers_1[Any]) -> Any:
            return helpers_9.encode_string("sdo:unitText")

    class ObjectExpr1651(IEncodable):
        def Encode(self, helpers_10: IEncoderHelpers_1[Any]) -> Any:
            return helpers_10.encode_string("sdo:unitCode")

    class ObjectExpr1652(IEncodable):
        def Encode(self, helpers_11: IEncoderHelpers_1[Any]) -> Any:
            return helpers_11.encode_string("sdo:disambiguatingDescription")

    values: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("sdo", ObjectExpr1640()), ("additionalType", ObjectExpr1641()), ("alternateName", ObjectExpr1643()), ("measurementMethod", ObjectExpr1644()), ("description", ObjectExpr1645()), ("category", ObjectExpr1646()), ("categoryCode", ObjectExpr1647()), ("value", ObjectExpr1648()), ("valueCode", ObjectExpr1649()), ("unit", ObjectExpr1650()), ("unitCode", ObjectExpr1651()), ("comments", ObjectExpr1652())])
    class ObjectExpr1653(IEncodable):
        def Encode(self, helpers_12: IEncoderHelpers_1[Any]) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_12))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_12.encode_object(arg)

    return ObjectExpr1653()


context_jsonvalue: IEncodable = _arrow1654()

__all__ = ["context_jsonvalue"]

