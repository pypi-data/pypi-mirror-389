from __future__ import annotations
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import (Any, TypeVar)
from ...fable_modules.fable_library.array_ import fold
from ...fable_modules.fable_library.list import (FSharpList, is_empty, length, head, of_array)
from ...fable_modules.fable_library.option import value as value_12
from ...fable_modules.fable_library.result import FSharpResult_2
from ...fable_modules.fable_library.seq import (to_list, delay, map, enumerate_from_functions, append, singleton, empty, collect)
from ...fable_modules.fable_library.string_ import starts_with_exact
from ...fable_modules.fable_library.types import Array
from ...fable_modules.fable_library.util import (equals, is_iterable, get_enumerator, IEnumerator, IEnumerable_1, int32_to_string)
from ...fable_modules.thoth_json_core.decode import (Getters_2__ctor_Z4BE6C149, Getters_2, IGetters, string, IRequiredGetter, IOptionalGetter, Getters_2__get_Errors, map as map_1, one_of, int_1, decimal)
from ...fable_modules.thoth_json_core.encode import list_1
from ...fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1, ErrorReason_1, IDecoderHelpers_1)
from ...ROCrate.ldcontext import LDContext
from ...ROCrate.ldobject import (LDValue, LDRef, LDNode)
from ..decode import (Decode_resizeArrayOrSingleton, Helpers_prependPath)
from ..encode import (date_time, resize_array_or_singleton)
from .ldcontext import (encoder as encoder_3, decoder as decoder_1)
from .ldref import (encoder as encoder_2, decoder as decoder_3)
from .ldvalue import (encoder as encoder_1, decoder as decoder_2)

__A_ = TypeVar("__A_")

def generic_encoder(obj: Any=None) -> IEncodable:
    if str(type(obj)) == "<class \'str\'>":
        class ObjectExpr1966(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any], obj: Any=obj) -> Any:
                return helpers.encode_string(obj)

        return ObjectExpr1966()

    elif str(type(obj)) == "<class \'int\'>":
        class ObjectExpr1967(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any], obj: Any=obj) -> Any:
                return helpers_1.encode_signed_integral_number(obj)

        return ObjectExpr1967()

    elif str(type(obj)) == "<class \'bool\'>":
        class ObjectExpr1968(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any], obj: Any=obj) -> Any:
                return helpers_2.encode_bool(obj)

        return ObjectExpr1968()

    elif str(type(obj)) == "<class \'float\'>":
        class ObjectExpr1969(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any], obj: Any=obj) -> Any:
                return helpers_3.encode_decimal_number(obj)

        return ObjectExpr1969()

    elif isinstance(obj, datetime):
        return date_time(obj)

    elif isinstance(obj, LDValue):
        return encoder_1(obj)

    elif isinstance(obj, LDRef):
        return encoder_2(obj)

    elif isinstance(obj, LDNode):
        return encoder(obj)

    elif equals(obj, None):
        class ObjectExpr1970(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any], obj: Any=obj) -> Any:
                return helpers_4.encode_null()

        return ObjectExpr1970()

    elif is_iterable(obj):
        def _arrow1974(__unit: None=None, obj: Any=obj) -> IEnumerable_1[IEncodable]:
            def _arrow1971(__unit: None=None) -> IEnumerator[Any]:
                return get_enumerator(obj)

            def _arrow1972(enumerator: IEnumerator[Any]) -> bool:
                return enumerator.System_Collections_IEnumerator_MoveNext()

            def _arrow1973(enumerator_1: IEnumerator[Any]) -> Any:
                return enumerator_1.System_Collections_IEnumerator_get_Current()

            return map(generic_encoder, enumerate_from_functions(_arrow1971, _arrow1972, _arrow1973))

        return list_1(to_list(delay(_arrow1974)))

    else: 
        raise Exception("Unknown type")



def encoder(obj: LDNode) -> IEncodable:
    def _arrow1987(__unit: None=None, obj: Any=obj) -> IEnumerable_1[tuple[str, IEncodable]]:
        def _arrow1976(__unit: None=None) -> IEncodable:
            value: str = obj.Id
            class ObjectExpr1975(IEncodable):
                def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                    return helpers.encode_string(value)

            return ObjectExpr1975()

        def _arrow1986(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
            def _arrow1978(value_1: str) -> IEncodable:
                class ObjectExpr1977(IEncodable):
                    def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                        return helpers_1.encode_string(value_1)

                return ObjectExpr1977()

            def _arrow1985(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
                def _arrow1980(value_3: str) -> IEncodable:
                    class ObjectExpr1979(IEncodable):
                        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                            return helpers_2.encode_string(value_3)

                    return ObjectExpr1979()

                def _arrow1984(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
                    def _arrow1981(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
                        match_value: LDContext | None = obj.TryGetContext()
                        if match_value is not None:
                            return singleton(("@context", encoder_3(match_value)))

                        else: 
                            return empty()


                    def _arrow1983(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
                        def _arrow1982(kv: Any) -> IEnumerable_1[tuple[str, IEncodable]]:
                            l: str = kv[0].lower()
                            return singleton((kv[0], generic_encoder(kv[1]))) if ((not starts_with_exact(l, "init_")) if ((not starts_with_exact(l, "init@")) if ((l != "@context") if ((l != "additionaltype") if ((l != "schematype") if (l != "id") else False) else False) else False) else False) else False) else empty()

                        return collect(_arrow1982, obj.GetProperties(True))

                    return append(_arrow1981(), delay(_arrow1983))

                return append(singleton(("additionalType", resize_array_or_singleton(_arrow1980, obj.AdditionalType))) if (len(obj.AdditionalType) != 0) else empty(), delay(_arrow1984))

            return append(singleton(("@type", resize_array_or_singleton(_arrow1978, obj.SchemaType))), delay(_arrow1985))

        return append(singleton(("@id", _arrow1976())), delay(_arrow1986))

    values: FSharpList[tuple[str, IEncodable]] = to_list(delay(_arrow1987))
    class ObjectExpr1988(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any], obj: Any=obj) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_3))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_3.encode_object(arg)

    return ObjectExpr1988()


def get_decoder(expect_object: bool) -> Decoder_1[Any]:
    def decode(expect_object_1: bool, expect_object: Any=expect_object) -> Decoder_1[Any]:
        class ObjectExpr1993(Decoder_1[LDNode]):
            def Decode(self, helpers: IDecoderHelpers_1[Any], value: Any, expect_object_1: Any=expect_object_1) -> FSharpResult_2[LDNode, tuple[str, ErrorReason_1[__A_]]]:
                if helpers.is_object(value):
                    getters: Getters_2[__A_, Any] = Getters_2__ctor_Z4BE6C149(helpers, value)
                    properties: IEnumerable_1[str] = helpers.get_properties(value)
                    result: LDNode
                    get: IGetters = getters
                    t: Array[str]
                    arg_1: Decoder_1[Array[str]] = Decode_resizeArrayOrSingleton(string)
                    object_arg: IRequiredGetter = get.Required
                    t = object_arg.Field("@type", arg_1)
                    id: str
                    object_arg_1: IRequiredGetter = get.Required
                    id = object_arg_1.Field("@id", string)
                    context: LDContext | None
                    object_arg_2: IOptionalGetter = get.Optional
                    context = object_arg_2.Field("@context", decoder_1)
                    def _arrow1990(__unit: None=None) -> Array[str] | None:
                        arg_7: Decoder_1[Array[str]] = Decode_resizeArrayOrSingleton(string)
                        object_arg_3: IOptionalGetter = get.Optional
                        return object_arg_3.Field("additionalType", arg_7)

                    o: LDNode = LDNode(id, t, _arrow1990())
                    with get_enumerator(properties) as enumerator:
                        while enumerator.System_Collections_IEnumerator_MoveNext():
                            property: str = enumerator.System_Collections_Generic_IEnumerator_1_get_Current()
                            if (property != "@context") if ((property != "@type") if (property != "@id") else False) else False:
                                def _arrow1992(__unit: None=None) -> Any:
                                    arg_9: Decoder_1[Any] = decode(False)
                                    object_arg_4: IRequiredGetter = get.Required
                                    return object_arg_4.Field(property, arg_9)

                                o.SetProperty(property, _arrow1992())

                    if context is not None:
                        o.SetContext(value_12(context))

                    result = o
                    match_value: FSharpList[tuple[str, ErrorReason_1[__A_]]] = Getters_2__get_Errors(getters)
                    if not is_empty(match_value):
                        errors: FSharpList[tuple[str, ErrorReason_1[__A_]]] = match_value
                        return FSharpResult_2(1, ("", ErrorReason_1(7, errors))) if (length(errors) > 1) else FSharpResult_2(1, head(match_value))

                    else: 
                        return FSharpResult_2(0, result)


                else: 
                    return FSharpResult_2(1, ("", ErrorReason_1(0, "an object", value)))


        decode_object: Decoder_1[LDNode] = ObjectExpr1993()
        class ObjectExpr1995(Decoder_1[Array[Any]]):
            def Decode(self, helpers_1: IDecoderHelpers_1[Any], value_1: Any, expect_object_1: Any=expect_object_1) -> FSharpResult_2[Array[Any], tuple[str, ErrorReason_1[__A_]]]:
                if helpers_1.is_array(value_1):
                    i: int = -1
                    def folder(acc: FSharpResult_2[Array[Any], tuple[str, ErrorReason_1[__A_]]], value_2: __A_) -> FSharpResult_2[Array[Any], tuple[str, ErrorReason_1[__A_]]]:
                        nonlocal i
                        i = (i + 1) or 0
                        if acc.tag == 0:
                            acc_1: Array[Any] = acc.fields[0]
                            match_value_1: FSharpResult_2[Any, tuple[str, ErrorReason_1[__A_]]]
                            copy_of_struct: Decoder_1[Any] = decode(False)
                            match_value_1 = copy_of_struct.Decode(helpers_1, value_2)
                            if match_value_1.tag == 0:
                                (acc_1.append(match_value_1.fields[0]))
                                return FSharpResult_2(0, acc_1)

                            else: 
                                def _arrow1994(__unit: None=None, acc: Any=acc, value_2: Any=value_2) -> tuple[str, ErrorReason_1[__A_]]:
                                    tupled_arg: tuple[str, ErrorReason_1[__A_]] = match_value_1.fields[0]
                                    return Helpers_prependPath((".[" + int32_to_string(i)) + "]", tupled_arg[0], tupled_arg[1])

                                return FSharpResult_2(1, _arrow1994())


                        else: 
                            return acc


                    return fold(folder, FSharpResult_2(0, []), helpers_1.as_array(value_1))

                else: 
                    return FSharpResult_2(1, ("", ErrorReason_1(0, "an array", value_1)))


        resize_array: Decoder_1[Array[Any]] = ObjectExpr1995()
        if expect_object_1:
            def _arrow1996(value_4: LDNode, expect_object_1: Any=expect_object_1) -> Any:
                return value_4

            return map_1(_arrow1996, decode_object)

        else: 
            def _arrow1998(value_5: LDValue, expect_object_1: Any=expect_object_1) -> Any:
                return value_5

            def _arrow1999(value_6: LDNode, expect_object_1: Any=expect_object_1) -> Any:
                return value_6

            def _arrow2000(value_7: LDRef, expect_object_1: Any=expect_object_1) -> Any:
                return value_7

            def _arrow2001(value_8: Array[Any], expect_object_1: Any=expect_object_1) -> Any:
                return value_8

            def _arrow2002(value_9: str, expect_object_1: Any=expect_object_1) -> Any:
                return value_9

            def _arrow2003(value_10: int, expect_object_1: Any=expect_object_1) -> Any:
                return value_10

            def _arrow2004(value_11: Decimal, expect_object_1: Any=expect_object_1) -> Any:
                return value_11

            return one_of(of_array([map_1(_arrow1998, decoder_2), map_1(_arrow1999, decode_object), map_1(_arrow2000, decoder_3), map_1(_arrow2001, resize_array), map_1(_arrow2002, string), map_1(_arrow2003, int_1), map_1(_arrow2004, decimal)]))


    return decode(expect_object)


def _arrow2005(value: Any=None) -> LDNode:
    return value


decoder: Decoder_1[LDNode] = map_1(_arrow2005, get_decoder(True))

generic_decoder: Decoder_1[Any] = get_decoder(False)

__all__ = ["generic_encoder", "encoder", "get_decoder", "decoder", "generic_decoder"]

