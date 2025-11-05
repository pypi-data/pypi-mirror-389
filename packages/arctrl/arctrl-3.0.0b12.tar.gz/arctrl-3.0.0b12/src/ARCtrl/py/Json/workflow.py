from __future__ import annotations
from typing import (Any, TypeVar)
from ..fable_modules.fable_library.list import (choose, of_array, FSharpList)
from ..fable_modules.fable_library.option import map
from ..fable_modules.fable_library.seq import map as map_1
from ..fable_modules.fable_library.types import Array
from ..fable_modules.fable_library.util import IEnumerable_1
from ..fable_modules.thoth_json_core.decode import (object, IRequiredGetter, string, IOptionalGetter, resize_array, IGetters)
from ..fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ..Core.arc_types import ArcWorkflow
from ..Core.comment import Comment
from ..Core.data_map import DataMap
from ..Core.ontology_annotation import OntologyAnnotation
from ..Core.person import Person
from ..Core.Process.component import Component
from ..Core.Process.protocol_parameter import ProtocolParameter
from ..Core.Table.composite_cell import CompositeCell
from .comment import (encoder as encoder_5, decoder as decoder_5)
from .DataMap.data_map import (encoder as encoder_1, decoder as decoder_3, encoder_compressed as encoder_compressed_1, decoder_compressed as decoder_compressed_1)
from .encode import (try_include, try_include_seq)
from .ontology_annotation import (OntologyAnnotation_encoder, OntologyAnnotation_decoder)
from .person import (encoder as encoder_4, decoder as decoder_4)
from .Process.component import (encoder as encoder_3, decoder as decoder_2)
from .Process.protocol_parameter import (encoder as encoder_2, decoder as decoder_1)

__A_ = TypeVar("__A_")

def encoder(workflow: ArcWorkflow) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], workflow: Any=workflow) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3051(__unit: None=None, workflow: Any=workflow) -> IEncodable:
        value: str = workflow.Identifier
        class ObjectExpr3050(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3050()

    def _arrow3052(oa: OntologyAnnotation, workflow: Any=workflow) -> IEncodable:
        return OntologyAnnotation_encoder(oa)

    def _arrow3054(value_1: str, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3053(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_1)

        return ObjectExpr3053()

    def _arrow3056(value_3: str, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3055(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_3)

        return ObjectExpr3055()

    def _arrow3058(value_5: str, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3057(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr3057()

    def _arrow3060(value_7: str, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3059(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_7)

        return ObjectExpr3059()

    def _arrow3061(dm: DataMap, workflow: Any=workflow) -> IEncodable:
        return encoder_1(dm)

    def _arrow3063(value_9: str, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3062(IEncodable):
            def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
                return helpers_5.encode_string(value_9)

        return ObjectExpr3062()

    def _arrow3064(value_11: ProtocolParameter, workflow: Any=workflow) -> IEncodable:
        return encoder_2(value_11)

    def _arrow3065(value_12: Component, workflow: Any=workflow) -> IEncodable:
        return encoder_3(value_12)

    def _arrow3066(person: Person, workflow: Any=workflow) -> IEncodable:
        return encoder_4(person)

    def _arrow3067(comment: Comment, workflow: Any=workflow) -> IEncodable:
        return encoder_5(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("Identifier", _arrow3051()), try_include("WorkflowType", _arrow3052, workflow.WorkflowType), try_include("Title", _arrow3054, workflow.Title), try_include("URI", _arrow3056, workflow.URI), try_include("Description", _arrow3058, workflow.Description), try_include("Version", _arrow3060, workflow.Version), try_include("DataMap", _arrow3061, workflow.DataMap), try_include_seq("SubWorkflowIdentifiers", _arrow3063, workflow.SubWorkflowIdentifiers), try_include_seq("Parameters", _arrow3064, workflow.Parameters), try_include_seq("Components", _arrow3065, workflow.Components), try_include_seq("Contacts", _arrow3066, workflow.Contacts), try_include_seq("Comments", _arrow3067, workflow.Comments)]))
    class ObjectExpr3068(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any], workflow: Any=workflow) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_6))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_6.encode_object(arg)

    return ObjectExpr3068()


def _arrow3081(get: IGetters) -> ArcWorkflow:
    def _arrow3069(__unit: None=None) -> str:
        object_arg: IRequiredGetter = get.Required
        return object_arg.Field("Identifier", string)

    def _arrow3070(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("Title", string)

    def _arrow3071(__unit: None=None) -> str | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("Description", string)

    def _arrow3072(__unit: None=None) -> OntologyAnnotation | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("WorkflowType", OntologyAnnotation_decoder)

    def _arrow3073(__unit: None=None) -> str | None:
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("URI", string)

    def _arrow3074(__unit: None=None) -> str | None:
        object_arg_5: IOptionalGetter = get.Optional
        return object_arg_5.Field("Version", string)

    def _arrow3075(__unit: None=None) -> Array[str] | None:
        arg_13: Decoder_1[Array[str]] = resize_array(string)
        object_arg_6: IOptionalGetter = get.Optional
        return object_arg_6.Field("SubWorkflowIdentifiers", arg_13)

    def _arrow3076(__unit: None=None) -> Array[ProtocolParameter] | None:
        arg_15: Decoder_1[Array[ProtocolParameter]] = resize_array(decoder_1)
        object_arg_7: IOptionalGetter = get.Optional
        return object_arg_7.Field("Parameters", arg_15)

    def _arrow3077(__unit: None=None) -> Array[Component] | None:
        arg_17: Decoder_1[Array[Component]] = resize_array(decoder_2)
        object_arg_8: IOptionalGetter = get.Optional
        return object_arg_8.Field("Components", arg_17)

    def _arrow3078(__unit: None=None) -> DataMap | None:
        object_arg_9: IOptionalGetter = get.Optional
        return object_arg_9.Field("DataMap", decoder_3)

    def _arrow3079(__unit: None=None) -> Array[Person] | None:
        arg_21: Decoder_1[Array[Person]] = resize_array(decoder_4)
        object_arg_10: IOptionalGetter = get.Optional
        return object_arg_10.Field("Contacts", arg_21)

    def _arrow3080(__unit: None=None) -> Array[Comment] | None:
        arg_23: Decoder_1[Array[Comment]] = resize_array(decoder_5)
        object_arg_11: IOptionalGetter = get.Optional
        return object_arg_11.Field("Comments", arg_23)

    return ArcWorkflow.create(_arrow3069(), _arrow3070(), _arrow3071(), _arrow3072(), _arrow3073(), _arrow3074(), _arrow3075(), _arrow3076(), _arrow3077(), _arrow3078(), _arrow3079(), _arrow3080())


decoder: Decoder_1[ArcWorkflow] = object(_arrow3081)

def encoder_compressed(string_table: Any, oa_table: Any, cell_table: Any, workflow: ArcWorkflow) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3085(__unit: None=None, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        value: str = workflow.Identifier
        class ObjectExpr3084(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3084()

    def _arrow3086(oa: OntologyAnnotation, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return OntologyAnnotation_encoder(oa)

    def _arrow3088(value_1: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3087(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_1)

        return ObjectExpr3087()

    def _arrow3090(value_3: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3089(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_3)

        return ObjectExpr3089()

    def _arrow3092(value_5: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3091(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr3091()

    def _arrow3094(value_7: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3093(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_7)

        return ObjectExpr3093()

    def _arrow3095(dm: DataMap, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return encoder_compressed_1(string_table, oa_table, cell_table, dm)

    def _arrow3097(value_9: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3096(IEncodable):
            def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
                return helpers_5.encode_string(value_9)

        return ObjectExpr3096()

    def _arrow3098(value_11: ProtocolParameter, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return encoder_2(value_11)

    def _arrow3099(value_12: Component, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return encoder_3(value_12)

    def _arrow3100(person: Person, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return encoder_4(person)

    def _arrow3101(comment: Comment, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return encoder_5(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("Identifier", _arrow3085()), try_include("WorkflowType", _arrow3086, workflow.WorkflowType), try_include("Title", _arrow3088, workflow.Title), try_include("URI", _arrow3090, workflow.URI), try_include("Description", _arrow3092, workflow.Description), try_include("Version", _arrow3094, workflow.Version), try_include("DataMap", _arrow3095, workflow.DataMap), try_include_seq("SubWorkflowIdentifiers", _arrow3097, workflow.SubWorkflowIdentifiers), try_include_seq("Parameters", _arrow3098, workflow.Parameters), try_include_seq("Components", _arrow3099, workflow.Components), try_include_seq("Contacts", _arrow3100, workflow.Contacts), try_include_seq("Comments", _arrow3101, workflow.Comments)]))
    class ObjectExpr3102(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any], string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_6))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_6.encode_object(arg)

    return ObjectExpr3102()


def decoder_compressed(string_table: Array[str], oa_table: Array[OntologyAnnotation], cell_table: Array[CompositeCell]) -> Decoder_1[ArcWorkflow]:
    def _arrow3115(get: IGetters, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> ArcWorkflow:
        def _arrow3103(__unit: None=None) -> str:
            object_arg: IRequiredGetter = get.Required
            return object_arg.Field("Identifier", string)

        def _arrow3104(__unit: None=None) -> str | None:
            object_arg_1: IOptionalGetter = get.Optional
            return object_arg_1.Field("Title", string)

        def _arrow3105(__unit: None=None) -> str | None:
            object_arg_2: IOptionalGetter = get.Optional
            return object_arg_2.Field("Description", string)

        def _arrow3106(__unit: None=None) -> OntologyAnnotation | None:
            object_arg_3: IOptionalGetter = get.Optional
            return object_arg_3.Field("WorkflowType", OntologyAnnotation_decoder)

        def _arrow3107(__unit: None=None) -> str | None:
            object_arg_4: IOptionalGetter = get.Optional
            return object_arg_4.Field("URI", string)

        def _arrow3108(__unit: None=None) -> str | None:
            object_arg_5: IOptionalGetter = get.Optional
            return object_arg_5.Field("Version", string)

        def _arrow3109(__unit: None=None) -> Array[str] | None:
            arg_13: Decoder_1[Array[str]] = resize_array(string)
            object_arg_6: IOptionalGetter = get.Optional
            return object_arg_6.Field("SubWorkflowIdentifiers", arg_13)

        def _arrow3110(__unit: None=None) -> Array[ProtocolParameter] | None:
            arg_15: Decoder_1[Array[ProtocolParameter]] = resize_array(decoder_1)
            object_arg_7: IOptionalGetter = get.Optional
            return object_arg_7.Field("Parameters", arg_15)

        def _arrow3111(__unit: None=None) -> Array[Component] | None:
            arg_17: Decoder_1[Array[Component]] = resize_array(decoder_2)
            object_arg_8: IOptionalGetter = get.Optional
            return object_arg_8.Field("Components", arg_17)

        def _arrow3112(__unit: None=None) -> DataMap | None:
            arg_19: Decoder_1[DataMap] = decoder_compressed_1(string_table, oa_table, cell_table)
            object_arg_9: IOptionalGetter = get.Optional
            return object_arg_9.Field("DataMap", arg_19)

        def _arrow3113(__unit: None=None) -> Array[Person] | None:
            arg_21: Decoder_1[Array[Person]] = resize_array(decoder_4)
            object_arg_10: IOptionalGetter = get.Optional
            return object_arg_10.Field("Contacts", arg_21)

        def _arrow3114(__unit: None=None) -> Array[Comment] | None:
            arg_23: Decoder_1[Array[Comment]] = resize_array(decoder_5)
            object_arg_11: IOptionalGetter = get.Optional
            return object_arg_11.Field("Comments", arg_23)

        return ArcWorkflow.create(_arrow3103(), _arrow3104(), _arrow3105(), _arrow3106(), _arrow3107(), _arrow3108(), _arrow3109(), _arrow3110(), _arrow3111(), _arrow3112(), _arrow3113(), _arrow3114())

    return object(_arrow3115)


__all__ = ["encoder", "decoder", "encoder_compressed", "decoder_compressed"]

