from typing import ClassVar, Set, Callable

from orbiter_parsers.file_types import unimplemented_dump
from orbiter.file_types import FileType

from orbiter_parsers.parsers.jil import JilParser


class FileTypeJIL(FileType):
    """JIL File Type

    :param extension: JIL
    :type extension: Set[str]
    :param load_fn: custom JIL loading function
    :type load_fn: Callable[[str], dict]
    :param dump_fn: JIL dumping function not yet implemented, raises an error
    :type dump_fn: Callable[[dict], str]
    """

    extension: ClassVar[Set[str]] = {"TXT", "JIL"}
    load_fn: ClassVar[Callable[[str], dict]] = JilParser.loads
    dump_fn: ClassVar[Callable[[dict], str]] = unimplemented_dump
