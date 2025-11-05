from __future__ import annotations
from collections.abc import Callable
from typing import (Any, TypeVar)
from ..fable_modules.fable_library.list import (choose, of_array, FSharpList)
from ..fable_modules.fable_library.option import (map, value as value_6)
from ..fable_modules.fable_library.seq import map as map_1
from ..fable_modules.fable_library.string_ import replace
from ..fable_modules.fable_library.types import to_string
from ..fable_modules.fable_library.util import IEnumerable_1
from ..fable_modules.thoth_json_core.decode import (object, IOptionalGetter, string, IGetters, map as map_2)
from ..fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ..Core.comment import Comment
from .context.rocrate.isa_comment_context import context_jsonvalue
from .encode import try_include
from .idtable import encode

__A_ = TypeVar("__A_")

def encoder(comment: Comment) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], comment: Any=comment) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2027(value: str, comment: Any=comment) -> IEncodable:
        class ObjectExpr2026(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2026()

    def _arrow2029(value_2: str, comment: Any=comment) -> IEncodable:
        class ObjectExpr2028(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_2)

        return ObjectExpr2028()

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("name", _arrow2027, comment.Name), try_include("value", _arrow2029, comment.Value)]))
    class ObjectExpr2030(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any], comment: Any=comment) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_2))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_2.encode_object(arg)

    return ObjectExpr2030()


def _arrow2033(get: IGetters) -> Comment:
    def _arrow2031(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("name", string)

    def _arrow2032(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("value", string)

    return Comment(_arrow2031(), _arrow2032())


decoder: Decoder_1[Comment] = object(_arrow2033)

def ROCrate_genID(c: Comment) -> str:
    match_value: str | None = c.Name
    if match_value is None:
        return "#EmptyComment"

    else: 
        n: str = match_value
        v: str = ("_" + replace(value_6(c.Value), " ", "_")) if (c.Value is not None) else ""
        return ("#Comment_" + replace(n, " ", "_")) + v



def ROCrate_encoder(comment: Comment) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], comment: Any=comment) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2037(__unit: None=None, comment: Any=comment) -> IEncodable:
        value: str = ROCrate_genID(comment)
        class ObjectExpr2036(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2036()

    class ObjectExpr2038(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any], comment: Any=comment) -> Any:
            return helpers_1.encode_string("Comment")

    def _arrow2040(value_2: str, comment: Any=comment) -> IEncodable:
        class ObjectExpr2039(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_2)

        return ObjectExpr2039()

    def _arrow2042(value_4: str, comment: Any=comment) -> IEncodable:
        class ObjectExpr2041(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_4)

        return ObjectExpr2041()

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("@id", _arrow2037()), ("@type", ObjectExpr2038()), try_include("name", _arrow2040, comment.Name), try_include("value", _arrow2042, comment.Value), ("@context", context_jsonvalue)]))
    class ObjectExpr2043(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any], comment: Any=comment) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_4.encode_object(arg)

    return ObjectExpr2043()


def _arrow2046(get: IGetters) -> Comment:
    def _arrow2044(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("name", string)

    def _arrow2045(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("value", string)

    return Comment(_arrow2044(), _arrow2045())


ROCrate_decoder: Decoder_1[Comment] = object(_arrow2046)

def ROCrate_encoderDisambiguatingDescription(comment: Comment) -> IEncodable:
    value: str = to_string(comment)
    class ObjectExpr2047(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any], comment: Any=comment) -> Any:
            return helpers.encode_string(value)

    return ObjectExpr2047()


def ctor(s: str) -> Comment:
    return Comment.from_string(s)


ROCrate_decoderDisambiguatingDescription: Decoder_1[Comment] = map_2(ctor, string)

def ISAJson_encoder(id_map: Any | None, comment: Comment) -> IEncodable:
    def f(comment_1: Comment, id_map: Any=id_map, comment: Any=comment) -> IEncodable:
        def chooser(tupled_arg: tuple[str, IEncodable | None], comment_1: Any=comment_1) -> tuple[str, IEncodable] | None:
            def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
                return (tupled_arg[0], v_1)

            return map(mapping, tupled_arg[1])

        def _arrow2051(value: str, comment_1: Any=comment_1) -> IEncodable:
            class ObjectExpr2050(IEncodable):
                def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                    return helpers.encode_string(value)

            return ObjectExpr2050()

        def _arrow2053(value_2: str, comment_1: Any=comment_1) -> IEncodable:
            class ObjectExpr2052(IEncodable):
                def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_1.encode_string(value_2)

            return ObjectExpr2052()

        def _arrow2055(value_4: str, comment_1: Any=comment_1) -> IEncodable:
            class ObjectExpr2054(IEncodable):
                def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_2.encode_string(value_4)

            return ObjectExpr2054()

        values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("@id", _arrow2051, ROCrate_genID(comment_1)), try_include("name", _arrow2053, comment_1.Name), try_include("value", _arrow2055, comment_1.Value)]))
        class ObjectExpr2056(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any], comment_1: Any=comment_1) -> Any:
                def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                    return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_3))

                arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
                return helpers_3.encode_object(arg)

        return ObjectExpr2056()

    if id_map is None:
        return f(comment)

    else: 
        def _arrow2057(c: Comment, id_map: Any=id_map, comment: Any=comment) -> str:
            return ROCrate_genID(c)

        return encode(_arrow2057, f, comment, id_map)



ISAJson_decoder: Decoder_1[Comment] = decoder

__all__ = ["encoder", "decoder", "ROCrate_genID", "ROCrate_encoder", "ROCrate_decoder", "ROCrate_encoderDisambiguatingDescription", "ROCrate_decoderDisambiguatingDescription", "ISAJson_encoder", "ISAJson_decoder"]

