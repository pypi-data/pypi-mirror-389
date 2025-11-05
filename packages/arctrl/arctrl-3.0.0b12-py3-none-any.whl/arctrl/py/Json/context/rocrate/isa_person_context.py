from __future__ import annotations
from dataclasses import dataclass
from typing import (Any, TypeVar)
from ....fable_modules.fable_library.reflection import (TypeInfo, string_type, record_type)
from ....fable_modules.fable_library.seq import map
from ....fable_modules.fable_library.types import Record
from ....fable_modules.fable_library.util import (to_enumerable, IEnumerable_1)
from ....fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1)

__A_ = TypeVar("__A_")

def _expr1792() -> TypeInfo:
    return record_type("ARCtrl.Json.ROCrateContext.Person.IContext", [], IContext, lambda: [("sdo", string_type), ("arc", string_type), ("Person", string_type), ("first_name", string_type), ("last_name", string_type), ("mid_initials", string_type), ("email", string_type), ("address", string_type), ("phone", string_type), ("fax", string_type), ("comments", string_type), ("roles", string_type), ("affiliation", string_type)])


@dataclass(eq = False, repr = False, slots = True)
class IContext(Record):
    sdo: str
    arc: str
    Person: str
    first_name: str
    last_name: str
    mid_initials: str
    email: str
    address: str
    phone: str
    fax: str
    comments: str
    roles: str
    affiliation: str

IContext_reflection = _expr1792

def _arrow1807(__unit: None=None) -> IEncodable:
    class ObjectExpr1793(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string("http://schema.org/")

    class ObjectExpr1794(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
            return helpers_1.encode_string("sdo:Person")

    class ObjectExpr1795(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
            return helpers_2.encode_string("sdo:identifier")

    class ObjectExpr1796(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
            return helpers_3.encode_string("sdo:givenName")

    class ObjectExpr1797(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
            return helpers_4.encode_string("sdo:familyName")

    class ObjectExpr1798(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
            return helpers_5.encode_string("sdo:additionalName")

    class ObjectExpr1799(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any]) -> Any:
            return helpers_6.encode_string("sdo:email")

    class ObjectExpr1800(IEncodable):
        def Encode(self, helpers_7: IEncoderHelpers_1[Any]) -> Any:
            return helpers_7.encode_string("sdo:address")

    class ObjectExpr1801(IEncodable):
        def Encode(self, helpers_8: IEncoderHelpers_1[Any]) -> Any:
            return helpers_8.encode_string("sdo:telephone")

    class ObjectExpr1802(IEncodable):
        def Encode(self, helpers_9: IEncoderHelpers_1[Any]) -> Any:
            return helpers_9.encode_string("sdo:faxNumber")

    class ObjectExpr1803(IEncodable):
        def Encode(self, helpers_10: IEncoderHelpers_1[Any]) -> Any:
            return helpers_10.encode_string("sdo:disambiguatingDescription")

    class ObjectExpr1804(IEncodable):
        def Encode(self, helpers_11: IEncoderHelpers_1[Any]) -> Any:
            return helpers_11.encode_string("sdo:jobTitle")

    class ObjectExpr1805(IEncodable):
        def Encode(self, helpers_12: IEncoderHelpers_1[Any]) -> Any:
            return helpers_12.encode_string("sdo:affiliation")

    values: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("sdo", ObjectExpr1793()), ("Person", ObjectExpr1794()), ("orcid", ObjectExpr1795()), ("firstName", ObjectExpr1796()), ("lastName", ObjectExpr1797()), ("midInitials", ObjectExpr1798()), ("email", ObjectExpr1799()), ("address", ObjectExpr1800()), ("phone", ObjectExpr1801()), ("fax", ObjectExpr1802()), ("comments", ObjectExpr1803()), ("roles", ObjectExpr1804()), ("affiliation", ObjectExpr1805())])
    class ObjectExpr1806(IEncodable):
        def Encode(self, helpers_13: IEncoderHelpers_1[Any]) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_13))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_13.encode_object(arg)

    return ObjectExpr1806()


context_jsonvalue: IEncodable = _arrow1807()

def _arrow1812(__unit: None=None) -> IEncodable:
    class ObjectExpr1808(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string("http://schema.org/")

    class ObjectExpr1809(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
            return helpers_1.encode_string("sdo:Person")

    class ObjectExpr1810(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
            return helpers_2.encode_string("sdo:name")

    values: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("sdo", ObjectExpr1808()), ("Person", ObjectExpr1809()), ("name", ObjectExpr1810())])
    class ObjectExpr1811(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_3))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_3.encode_object(arg)

    return ObjectExpr1811()


context_minimal_json_value: IEncodable = _arrow1812()

context_str: str = "\r\n{\r\n  \"@context\": {\r\n    \"sdo\": \"http://schema.org/\",\r\n    \"arc\": \"http://purl.org/nfdi4plants/ontology/\",\r\n\r\n    \"Person\": \"sdo:Person\",\r\n    \"firstName\": \"sdo:givenName\",\r\n    \"lastName\": \"sdo:familyName\",\r\n    \"midInitials\": \"sdo:additionalName\",\r\n    \"email\": \"sdo:email\",\r\n    \"address\": \"sdo:address\",\r\n    \"phone\": \"sdo:telephone\",\r\n    \"fax\": \"sdo:faxNumber\",\r\n    \"comments\": \"sdo:disambiguatingDescription\",\r\n    \"roles\": \"sdo:jobTitle\",\r\n    \"affiliation\": \"sdo:affiliation\"\r\n  }\r\n}\r\n    "

__all__ = ["IContext_reflection", "context_jsonvalue", "context_minimal_json_value", "context_str"]

