from collections.abc import Callable
from typing import Any
from ...fable_modules.fable_library.util import to_enumerable
from .collections_ import (Dictionary_ofSeq, Dictionary_tryFind)

def OntobeeParser(tsr: str, local_tan: str) -> str:
    return ((((("" + "http://purl.obolibrary.org/obo/") + "") + tsr) + "_") + local_tan) + ""


def BioregistryParser(tsr: str, local_tan: str) -> str:
    return ((((("" + "https://bioregistry.io/") + "") + tsr) + ":") + local_tan) + ""


def OntobeeDPBOParser(tsr: str, local_tan: str) -> str:
    return ((((("" + "http://purl.org/nfdi4plants/ontology/dpbo/") + "") + tsr) + "_") + local_tan) + ""


def MSParser(tsr: str, local_tan: str) -> str:
    return ((((("" + "https://www.ebi.ac.uk/ols4/ontologies/ms/classes/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F") + "") + tsr) + "_") + local_tan) + ""


def POParser(tsr: str, local_tan: str) -> str:
    return ((((("" + "https://www.ebi.ac.uk/ols4/ontologies/po/classes/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F") + "") + tsr) + "_") + local_tan) + ""


def ROParser(tsr: str, local_tan: str) -> str:
    return ((((("" + "https://www.ebi.ac.uk/ols4/ontologies/ro/classes/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F") + "") + tsr) + "_") + local_tan) + ""


def _arrow488(tsr: str) -> Callable[[str], str]:
    def _arrow487(local_tan: str) -> str:
        return OntobeeDPBOParser(tsr, local_tan)

    return _arrow487


def _arrow490(tsr_1: str) -> Callable[[str], str]:
    def _arrow489(local_tan_1: str) -> str:
        return MSParser(tsr_1, local_tan_1)

    return _arrow489


def _arrow492(tsr_2: str) -> Callable[[str], str]:
    def _arrow491(local_tan_2: str) -> str:
        return POParser(tsr_2, local_tan_2)

    return _arrow491


def _arrow494(tsr_3: str) -> Callable[[str], str]:
    def _arrow493(local_tan_3: str) -> str:
        return ROParser(tsr_3, local_tan_3)

    return _arrow493


def _arrow496(tsr_4: str) -> Callable[[str], str]:
    def _arrow495(local_tan_4: str) -> str:
        return BioregistryParser(tsr_4, local_tan_4)

    return _arrow495


def _arrow498(tsr_5: str) -> Callable[[str], str]:
    def _arrow497(local_tan_5: str) -> str:
        return BioregistryParser(tsr_5, local_tan_5)

    return _arrow497


def _arrow500(tsr_6: str) -> Callable[[str], str]:
    def _arrow499(local_tan_6: str) -> str:
        return BioregistryParser(tsr_6, local_tan_6)

    return _arrow499


def _arrow502(tsr_7: str) -> Callable[[str], str]:
    def _arrow501(local_tan_7: str) -> str:
        return BioregistryParser(tsr_7, local_tan_7)

    return _arrow501


def _arrow504(tsr_8: str) -> Callable[[str], str]:
    def _arrow503(local_tan_8: str) -> str:
        return BioregistryParser(tsr_8, local_tan_8)

    return _arrow503


def _arrow506(tsr_9: str) -> Callable[[str], str]:
    def _arrow505(local_tan_9: str) -> str:
        return BioregistryParser(tsr_9, local_tan_9)

    return _arrow505


def _arrow508(tsr_10: str) -> Callable[[str], str]:
    def _arrow507(local_tan_10: str) -> str:
        return BioregistryParser(tsr_10, local_tan_10)

    return _arrow507


def _arrow510(tsr_11: str) -> Callable[[str], str]:
    def _arrow509(local_tan_11: str) -> str:
        return BioregistryParser(tsr_11, local_tan_11)

    return _arrow509


def _arrow512(tsr_12: str) -> Callable[[str], str]:
    def _arrow511(local_tan_12: str) -> str:
        return BioregistryParser(tsr_12, local_tan_12)

    return _arrow511


def _arrow514(tsr_13: str) -> Callable[[str], str]:
    def _arrow513(local_tan_13: str) -> str:
        return BioregistryParser(tsr_13, local_tan_13)

    return _arrow513


def _arrow516(tsr_14: str) -> Callable[[str], str]:
    def _arrow515(local_tan_14: str) -> str:
        return BioregistryParser(tsr_14, local_tan_14)

    return _arrow515


uri_parser_collection: Any = Dictionary_ofSeq(to_enumerable([("DPBO", _arrow488), ("MS", _arrow490), ("PO", _arrow492), ("RO", _arrow494), ("ENVO", _arrow496), ("CHEBI", _arrow498), ("GO", _arrow500), ("OBI", _arrow502), ("PATO", _arrow504), ("PECO", _arrow506), ("TO", _arrow508), ("UO", _arrow510), ("EFO", _arrow512), ("NCIT", _arrow514), ("OMP", _arrow516)]))

def create_oauri(tsr: str, local_tan: str) -> str:
    match_value: Callable[[str, str], str] | None = Dictionary_tryFind(tsr, uri_parser_collection)
    if match_value is None:
        return OntobeeParser(tsr, local_tan)

    else: 
        return match_value(tsr)(local_tan)



__all__ = ["OntobeeParser", "BioregistryParser", "OntobeeDPBOParser", "MSParser", "POParser", "ROParser", "uri_parser_collection", "create_oauri"]

