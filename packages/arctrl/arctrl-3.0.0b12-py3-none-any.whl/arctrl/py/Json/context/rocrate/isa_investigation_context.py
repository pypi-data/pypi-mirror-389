from __future__ import annotations
from dataclasses import dataclass
from typing import (Any, TypeVar)
from ....fable_modules.fable_library.reflection import (TypeInfo, string_type, record_type)
from ....fable_modules.fable_library.seq import map
from ....fable_modules.fable_library.types import Record
from ....fable_modules.fable_library.util import (to_enumerable, IEnumerable_1)
from ....fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1)

__A_ = TypeVar("__A_")

def _expr1721() -> TypeInfo:
    return record_type("ARCtrl.Json.ROCrateContext.Investigation.IContext", [], IContext, lambda: [("sdo", string_type), ("arc", string_type), ("Investigation", string_type), ("identifier", string_type), ("title", string_type), ("description", string_type), ("submission_date", string_type), ("public_release_date", string_type), ("publications", string_type), ("people", string_type), ("studies", string_type), ("ontology_source_references", string_type), ("comments", string_type), ("publications_003F", string_type), ("filename", string_type)])


@dataclass(eq = False, repr = False, slots = True)
class IContext(Record):
    sdo: str
    arc: str
    Investigation: str
    identifier: str
    title: str
    description: str
    submission_date: str
    public_release_date: str
    publications: str
    people: str
    studies: str
    ontology_source_references: str
    comments: str
    publications_003F: str
    filename: str

IContext_reflection = _expr1721

def _arrow1737(__unit: None=None) -> IEncodable:
    class ObjectExpr1722(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string("http://schema.org/")

    class ObjectExpr1723(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
            return helpers_1.encode_string("sdo:Dataset")

    class ObjectExpr1724(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
            return helpers_2.encode_string("sdo:identifier")

    class ObjectExpr1725(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
            return helpers_3.encode_string("sdo:name")

    class ObjectExpr1726(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
            return helpers_4.encode_string("sdo:additionalType")

    class ObjectExpr1727(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
            return helpers_5.encode_string("sdo:description")

    class ObjectExpr1728(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any]) -> Any:
            return helpers_6.encode_string("sdo:dateCreated")

    class ObjectExpr1729(IEncodable):
        def Encode(self, helpers_7: IEncoderHelpers_1[Any]) -> Any:
            return helpers_7.encode_string("sdo:datePublished")

    class ObjectExpr1730(IEncodable):
        def Encode(self, helpers_8: IEncoderHelpers_1[Any]) -> Any:
            return helpers_8.encode_string("sdo:citation")

    class ObjectExpr1731(IEncodable):
        def Encode(self, helpers_9: IEncoderHelpers_1[Any]) -> Any:
            return helpers_9.encode_string("sdo:creator")

    class ObjectExpr1732(IEncodable):
        def Encode(self, helpers_10: IEncoderHelpers_1[Any]) -> Any:
            return helpers_10.encode_string("sdo:hasPart")

    class ObjectExpr1733(IEncodable):
        def Encode(self, helpers_11: IEncoderHelpers_1[Any]) -> Any:
            return helpers_11.encode_string("sdo:mentions")

    class ObjectExpr1734(IEncodable):
        def Encode(self, helpers_12: IEncoderHelpers_1[Any]) -> Any:
            return helpers_12.encode_string("sdo:comment")

    class ObjectExpr1735(IEncodable):
        def Encode(self, helpers_13: IEncoderHelpers_1[Any]) -> Any:
            return helpers_13.encode_string("sdo:alternateName")

    values: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("sdo", ObjectExpr1722()), ("Investigation", ObjectExpr1723()), ("identifier", ObjectExpr1724()), ("title", ObjectExpr1725()), ("additionalType", ObjectExpr1726()), ("description", ObjectExpr1727()), ("submissionDate", ObjectExpr1728()), ("publicReleaseDate", ObjectExpr1729()), ("publications", ObjectExpr1730()), ("people", ObjectExpr1731()), ("studies", ObjectExpr1732()), ("ontologySourceReferences", ObjectExpr1733()), ("comments", ObjectExpr1734()), ("filename", ObjectExpr1735())])
    class ObjectExpr1736(IEncodable):
        def Encode(self, helpers_14: IEncoderHelpers_1[Any]) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_14))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_14.encode_object(arg)

    return ObjectExpr1736()


context_jsonvalue: IEncodable = _arrow1737()

context_str: str = "\r\n{\r\n  \"@context\": {\r\n    \"sdo\": \"http://schema.org/\",\r\n    \"arc\": \"http://purl.org/nfdi4plants/ontology/\",\r\n\r\n    \"Investigation\": \"sdo:Dataset\",\r\n\r\n    \"identifier\" : \"sdo:identifier\",\r\n    \"title\": \"sdo:name\",\r\n    \"description\": \"sdo:description\",\r\n    \"submissionDate\": \"sdo:dateCreated\",\r\n    \"publicReleaseDate\": \"sdo:datePublished\",\r\n    \"publications\": \"sdo:citation\",\r\n    \"people\": \"sdo:creator\",\r\n    \"studies\": \"sdo:hasPart\",\r\n    \"ontologySourceReferences\": \"sdo:mentions\",\r\n    \"comments\": \"sdo:disambiguatingDescription\",\r\n\r\n    \"publications?\": \"sdo:SubjectOf?\",\r\n    \"filename\": \"sdo:alternateName\"\r\n  }\r\n}\r\n    "

__all__ = ["IContext_reflection", "context_jsonvalue", "context_str"]

