from __future__ import annotations
from collections.abc import Callable
from typing import (Any, TypeVar)
from ...fable_modules.fable_library.array_ import map as map_1
from ...fable_modules.fable_library.date import to_string as to_string_1
from ...fable_modules.fable_library.seq import map
from ...fable_modules.fable_library.types import (to_string, Array)
from ...fable_modules.fable_library.util import (to_enumerable, IEnumerable_1)
from ...fable_modules.thoth_json_core.decode import (and_then, succeed, string, object, IRequiredGetter, guid, resize_array, IOptionalGetter, IGetters, datetime_local, array as array_2)
from ...fable_modules.thoth_json_core.encode import seq
from ...fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ...Core.ontology_annotation import OntologyAnnotation
from ...Core.person import Person
from ...Core.Table.arc_table import ArcTable
from ...Core.Table.composite_cell import CompositeCell
from ...Core.template import (Organisation, Template)
from ..decode import Decode_datetime
from ..encode import date_time
from ..ontology_annotation import (OntologyAnnotation_encoder, OntologyAnnotation_decoder)
from ..person import (encoder as encoder_1, decoder as decoder_2)
from .arc_table import (encoder, decoder as decoder_1, encoder_compressed, decoder_compressed)

__A_ = TypeVar("__A_")

def _arrow2869(arg: Organisation) -> IEncodable:
    value: str = to_string(arg)
    class ObjectExpr2868(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string(value)

    return ObjectExpr2868()


Template_Organisation_encoder: Callable[[Organisation], IEncodable] = _arrow2869

def cb(text_value: str) -> Decoder_1[Organisation]:
    return succeed(Organisation.of_string(text_value))


Template_Organisation_decoder: Decoder_1[Organisation] = and_then(cb, string)

def Template_encoder(template: Template) -> IEncodable:
    def _arrow2875(__unit: None=None, template: Any=template) -> IEncodable:
        value_1: str
        copy_of_struct: str = template.Id
        value_1 = str(copy_of_struct)
        class ObjectExpr2874(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value_1)

        return ObjectExpr2874()

    def _arrow2880(__unit: None=None, template: Any=template) -> IEncodable:
        value_3: str = template.Name
        class ObjectExpr2879(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_3)

        return ObjectExpr2879()

    def _arrow2882(__unit: None=None, template: Any=template) -> IEncodable:
        value_4: str = template.Description
        class ObjectExpr2881(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_4)

        return ObjectExpr2881()

    def _arrow2885(__unit: None=None, template: Any=template) -> IEncodable:
        value_5: str = template.Version
        class ObjectExpr2884(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr2884()

    def mapping(person: Person, template: Any=template) -> IEncodable:
        return encoder_1(person)

    def mapping_1(oa: OntologyAnnotation, template: Any=template) -> IEncodable:
        return OntologyAnnotation_encoder(oa)

    def mapping_2(oa_1: OntologyAnnotation, template: Any=template) -> IEncodable:
        return OntologyAnnotation_encoder(oa_1)

    values_3: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("id", _arrow2875()), ("table", encoder(template.Table)), ("name", _arrow2880()), ("description", _arrow2882()), ("organisation", Template_Organisation_encoder(template.Organisation)), ("version", _arrow2885()), ("authors", seq(map(mapping, template.Authors))), ("endpoint_repositories", seq(map(mapping_1, template.EndpointRepositories))), ("tags", seq(map(mapping_2, template.Tags))), ("last_updated", date_time(template.LastUpdated))])
    class ObjectExpr2894(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any], template: Any=template) -> Any:
            def mapping_3(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping_3, values_3)
            return helpers_4.encode_object(arg)

    return ObjectExpr2894()


def _arrow2913(get: IGetters) -> Template:
    def _arrow2899(__unit: None=None) -> str:
        object_arg: IRequiredGetter = get.Required
        return object_arg.Field("id", guid)

    def _arrow2900(__unit: None=None) -> ArcTable:
        object_arg_1: IRequiredGetter = get.Required
        return object_arg_1.Field("table", decoder_1)

    def _arrow2901(__unit: None=None) -> str:
        object_arg_2: IRequiredGetter = get.Required
        return object_arg_2.Field("name", string)

    def _arrow2902(__unit: None=None) -> str:
        object_arg_3: IRequiredGetter = get.Required
        return object_arg_3.Field("description", string)

    def _arrow2904(__unit: None=None) -> Organisation:
        object_arg_4: IRequiredGetter = get.Required
        return object_arg_4.Field("organisation", Template_Organisation_decoder)

    def _arrow2905(__unit: None=None) -> str:
        object_arg_5: IRequiredGetter = get.Required
        return object_arg_5.Field("version", string)

    def _arrow2906(__unit: None=None) -> Array[Person] | None:
        arg_13: Decoder_1[Array[Person]] = resize_array(decoder_2)
        object_arg_6: IOptionalGetter = get.Optional
        return object_arg_6.Field("authors", arg_13)

    def _arrow2909(__unit: None=None) -> Array[OntologyAnnotation] | None:
        arg_15: Decoder_1[Array[OntologyAnnotation]] = resize_array(OntologyAnnotation_decoder)
        object_arg_7: IOptionalGetter = get.Optional
        return object_arg_7.Field("endpoint_repositories", arg_15)

    def _arrow2910(__unit: None=None) -> Array[OntologyAnnotation] | None:
        arg_17: Decoder_1[Array[OntologyAnnotation]] = resize_array(OntologyAnnotation_decoder)
        object_arg_8: IOptionalGetter = get.Optional
        return object_arg_8.Field("tags", arg_17)

    def _arrow2911(__unit: None=None) -> Any:
        object_arg_9: IRequiredGetter = get.Required
        return object_arg_9.Field("last_updated", Decode_datetime)

    return Template.create(_arrow2899(), _arrow2900(), _arrow2901(), _arrow2902(), _arrow2904(), _arrow2905(), _arrow2906(), _arrow2909(), _arrow2910(), _arrow2911())


Template_decoder: Decoder_1[Template] = object(_arrow2913)

def Template_encoderCompressed(string_table: Any, oa_table: Any, cell_table: Any, template: Template) -> IEncodable:
    def _arrow2916(__unit: None=None, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, template: Any=template) -> IEncodable:
        value_1: str
        copy_of_struct: str = template.Id
        value_1 = str(copy_of_struct)
        class ObjectExpr2915(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value_1)

        return ObjectExpr2915()

    def _arrow2919(__unit: None=None, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, template: Any=template) -> IEncodable:
        value_3: str = template.Name
        class ObjectExpr2918(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_3)

        return ObjectExpr2918()

    def _arrow2921(__unit: None=None, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, template: Any=template) -> IEncodable:
        value_4: str = template.Description
        class ObjectExpr2920(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_4)

        return ObjectExpr2920()

    def _arrow2923(__unit: None=None, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, template: Any=template) -> IEncodable:
        value_5: str = template.Version
        class ObjectExpr2922(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr2922()

    def mapping(person: Person, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, template: Any=template) -> IEncodable:
        return encoder_1(person)

    def mapping_1(oa: OntologyAnnotation, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, template: Any=template) -> IEncodable:
        return OntologyAnnotation_encoder(oa)

    def mapping_2(oa_1: OntologyAnnotation, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, template: Any=template) -> IEncodable:
        return OntologyAnnotation_encoder(oa_1)

    def _arrow2925(__unit: None=None, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, template: Any=template) -> IEncodable:
        value_1_1: str = to_string_1(template.LastUpdated, "O", {})
        class ObjectExpr2924(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_1_1)

        return ObjectExpr2924()

    values_3: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("id", _arrow2916()), ("table", encoder_compressed(string_table, oa_table, cell_table, template.Table)), ("name", _arrow2919()), ("description", _arrow2921()), ("organisation", Template_Organisation_encoder(template.Organisation)), ("version", _arrow2923()), ("authors", seq(map(mapping, template.Authors))), ("endpoint_repositories", seq(map(mapping_1, template.EndpointRepositories))), ("tags", seq(map(mapping_2, template.Tags))), ("last_updated", _arrow2925())])
    class ObjectExpr2926(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any], string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, template: Any=template) -> Any:
            def mapping_3(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_5))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping_3, values_3)
            return helpers_5.encode_object(arg)

    return ObjectExpr2926()


def Template_decoderCompressed(string_table: Array[str], oa_table: Array[OntologyAnnotation], cell_table: Array[CompositeCell]) -> Decoder_1[Template]:
    def _arrow2937(get: IGetters, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> Template:
        def _arrow2927(__unit: None=None) -> str:
            object_arg: IRequiredGetter = get.Required
            return object_arg.Field("id", guid)

        def _arrow2928(__unit: None=None) -> ArcTable:
            arg_3: Decoder_1[ArcTable] = decoder_compressed(string_table, oa_table, cell_table)
            object_arg_1: IRequiredGetter = get.Required
            return object_arg_1.Field("table", arg_3)

        def _arrow2929(__unit: None=None) -> str:
            object_arg_2: IRequiredGetter = get.Required
            return object_arg_2.Field("name", string)

        def _arrow2930(__unit: None=None) -> str:
            object_arg_3: IRequiredGetter = get.Required
            return object_arg_3.Field("description", string)

        def _arrow2931(__unit: None=None) -> Organisation:
            object_arg_4: IRequiredGetter = get.Required
            return object_arg_4.Field("organisation", Template_Organisation_decoder)

        def _arrow2932(__unit: None=None) -> str:
            object_arg_5: IRequiredGetter = get.Required
            return object_arg_5.Field("version", string)

        def _arrow2933(__unit: None=None) -> Array[Person] | None:
            arg_13: Decoder_1[Array[Person]] = resize_array(decoder_2)
            object_arg_6: IOptionalGetter = get.Optional
            return object_arg_6.Field("authors", arg_13)

        def _arrow2934(__unit: None=None) -> Array[OntologyAnnotation] | None:
            arg_15: Decoder_1[Array[OntologyAnnotation]] = resize_array(OntologyAnnotation_decoder)
            object_arg_7: IOptionalGetter = get.Optional
            return object_arg_7.Field("endpoint_repositories", arg_15)

        def _arrow2935(__unit: None=None) -> Array[OntologyAnnotation] | None:
            arg_17: Decoder_1[Array[OntologyAnnotation]] = resize_array(OntologyAnnotation_decoder)
            object_arg_8: IOptionalGetter = get.Optional
            return object_arg_8.Field("tags", arg_17)

        def _arrow2936(__unit: None=None) -> Any:
            object_arg_9: IRequiredGetter = get.Required
            return object_arg_9.Field("last_updated", datetime_local)

        return Template.create(_arrow2927(), _arrow2928(), _arrow2929(), _arrow2930(), _arrow2931(), _arrow2932(), _arrow2933(), _arrow2934(), _arrow2935(), _arrow2936())

    return object(_arrow2937)


def Templates_encoder(templates: Array[Template]) -> IEncodable:
    def mapping(template: Template, templates: Any=templates) -> IEncodable:
        return Template_encoder(template)

    values: Array[IEncodable] = map_1(mapping, templates, None)
    class ObjectExpr2938(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any], templates: Any=templates) -> Any:
            def mapping_1(v: IEncodable) -> __A_:
                return v.Encode(helpers)

            arg: Array[__A_] = map_1(mapping_1, values, None)
            return helpers.encode_array(arg)

    return ObjectExpr2938()


Templates_decoder: Decoder_1[Array[Template]] = array_2(Template_decoder)

__all__ = ["Template_Organisation_encoder", "Template_Organisation_decoder", "Template_encoder", "Template_decoder", "Template_encoderCompressed", "Template_decoderCompressed", "Templates_encoder", "Templates_decoder"]

