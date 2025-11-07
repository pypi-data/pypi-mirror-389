"""
Wrappers for LLVM MC classes
"""
from __future__ import annotations
import typing

__all__ = [
    "AssemblerFlag",
    "BinaryExpr",
    "ConstantExpr",
    "DataRegionType",
    "Diagnostic",
    "DwarfFrameInfo",
    "Expr",
    "Fixup",
    "FixupKindInfo",
    "Instruction",
    "InstructionDesc",
    "MipsExprKind",
    "Register",
    "Section",
    "SectionCOFF",
    "SectionELF",
    "SectionMachO",
    "SourceLocation",
    "Symbol",
    "SymbolAttr",
    "SymbolRefExpr",
    "TargetExpr",
    "TargetExprAArch64",
    "TargetExprMips",
    "VersionMinType",
]

class AssemblerFlag:
    """
    Members:

      SyntaxUnified

      SubsectionsViaSymbols

      Code16

      Code32

      Code64
    """

    Code16: typing.ClassVar[AssemblerFlag]  # value = <AssemblerFlag.Code16: 2>
    Code32: typing.ClassVar[AssemblerFlag]  # value = <AssemblerFlag.Code32: 3>
    Code64: typing.ClassVar[AssemblerFlag]  # value = <AssemblerFlag.Code64: 4>
    SubsectionsViaSymbols: typing.ClassVar[
        AssemblerFlag
    ]  # value = <AssemblerFlag.SubsectionsViaSymbols: 1>
    SyntaxUnified: typing.ClassVar[
        AssemblerFlag
    ]  # value = <AssemblerFlag.SyntaxUnified: 0>
    __members__: typing.ClassVar[
        dict[str, AssemblerFlag]
    ]  # value = {'SyntaxUnified': <AssemblerFlag.SyntaxUnified: 0>, 'SubsectionsViaSymbols': <AssemblerFlag.SubsectionsViaSymbols: 1>, 'Code16': <AssemblerFlag.Code16: 2>, 'Code32': <AssemblerFlag.Code32: 3>, 'Code64': <AssemblerFlag.Code64: 4>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    def __eq__(self, other: typing.Any) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: typing.Any) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    def __str__(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class BinaryExpr(Expr):
    class Opcode:
        """
        Members:

          Add

          And

          Div

          EQ

          GT

          GTE

          LAnd

          LOr

          LT

          LTE

          Mod

          Mul

          NE

          Or

          OrNot

          Shl

          AShr

          LShr

          Sub

          Xor
        """

        AShr: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.AShr: 16>
        Add: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.Add: 0>
        And: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.And: 1>
        Div: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.Div: 2>
        EQ: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.EQ: 3>
        GT: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.GT: 4>
        GTE: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.GTE: 5>
        LAnd: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.LAnd: 6>
        LOr: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.LOr: 7>
        LShr: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.LShr: 17>
        LT: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.LT: 8>
        LTE: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.LTE: 9>
        Mod: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.Mod: 10>
        Mul: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.Mul: 11>
        NE: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.NE: 12>
        Or: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.Or: 13>
        OrNot: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.OrNot: 14>
        Shl: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.Shl: 15>
        Sub: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.Sub: 18>
        Xor: typing.ClassVar[BinaryExpr.Opcode]  # value = <Opcode.Xor: 19>
        __members__: typing.ClassVar[
            dict[str, BinaryExpr.Opcode]
        ]  # value = {'Add': <Opcode.Add: 0>, 'And': <Opcode.And: 1>, 'Div': <Opcode.Div: 2>, 'EQ': <Opcode.EQ: 3>, 'GT': <Opcode.GT: 4>, 'GTE': <Opcode.GTE: 5>, 'LAnd': <Opcode.LAnd: 6>, 'LOr': <Opcode.LOr: 7>, 'LT': <Opcode.LT: 8>, 'LTE': <Opcode.LTE: 9>, 'Mod': <Opcode.Mod: 10>, 'Mul': <Opcode.Mul: 11>, 'NE': <Opcode.NE: 12>, 'Or': <Opcode.Or: 13>, 'OrNot': <Opcode.OrNot: 14>, 'Shl': <Opcode.Shl: 15>, 'AShr': <Opcode.AShr: 16>, 'LShr': <Opcode.LShr: 17>, 'Sub': <Opcode.Sub: 18>, 'Xor': <Opcode.Xor: 19>}
        @staticmethod
        def _pybind11_conduit_v1_(*args, **kwargs): ...
        def __eq__(self, other: typing.Any) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: typing.Any) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        def __str__(self) -> str: ...
        @property
        def name(self) -> str: ...
        @property
        def value(self) -> int: ...

    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def lhs(self) -> Expr: ...
    @property
    def opcode(self) -> BinaryExpr.Opcode: ...
    @property
    def rhs(self) -> Expr: ...

class ConstantExpr(Expr):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def size_in_bytes(self) -> int: ...
    @property
    def value(self) -> int: ...

class DataRegionType:
    """
    Members:

      DataRegion

      DataRegionJT8

      DataRegionJT16

      DataRegionJT32

      DataRegionEnd
    """

    DataRegion: typing.ClassVar[
        DataRegionType
    ]  # value = <DataRegionType.DataRegion: 0>
    DataRegionEnd: typing.ClassVar[
        DataRegionType
    ]  # value = <DataRegionType.DataRegionEnd: 4>
    DataRegionJT16: typing.ClassVar[
        DataRegionType
    ]  # value = <DataRegionType.DataRegionJT16: 2>
    DataRegionJT32: typing.ClassVar[
        DataRegionType
    ]  # value = <DataRegionType.DataRegionJT32: 3>
    DataRegionJT8: typing.ClassVar[
        DataRegionType
    ]  # value = <DataRegionType.DataRegionJT8: 1>
    __members__: typing.ClassVar[
        dict[str, DataRegionType]
    ]  # value = {'DataRegion': <DataRegionType.DataRegion: 0>, 'DataRegionJT8': <DataRegionType.DataRegionJT8: 1>, 'DataRegionJT16': <DataRegionType.DataRegionJT16: 2>, 'DataRegionJT32': <DataRegionType.DataRegionJT32: 3>, 'DataRegionEnd': <DataRegionType.DataRegionEnd: 4>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    def __eq__(self, other: typing.Any) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: typing.Any) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    def __str__(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class Diagnostic:
    class Kind:
        """
        Members:

          Error

          Warning

          Remark

          Note
        """

        Error: typing.ClassVar[Diagnostic.Kind]  # value = <Kind.Error: 0>
        Note: typing.ClassVar[Diagnostic.Kind]  # value = <Kind.Note: 3>
        Remark: typing.ClassVar[Diagnostic.Kind]  # value = <Kind.Remark: 2>
        Warning: typing.ClassVar[Diagnostic.Kind]  # value = <Kind.Warning: 1>
        __members__: typing.ClassVar[
            dict[str, Diagnostic.Kind]
        ]  # value = {'Error': <Kind.Error: 0>, 'Warning': <Kind.Warning: 1>, 'Remark': <Kind.Remark: 2>, 'Note': <Kind.Note: 3>}
        @staticmethod
        def _pybind11_conduit_v1_(*args, **kwargs): ...
        def __eq__(self, other: typing.Any) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: typing.Any) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        def __str__(self) -> str: ...
        @property
        def name(self) -> str: ...
        @property
        def value(self) -> int: ...

    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def kind(self) -> Diagnostic.Kind: ...
    @property
    def lineno(self) -> int: ...
    @property
    def message(self) -> str: ...
    @property
    def offset(self) -> int: ...
    @property
    def text(self) -> str: ...

class DwarfFrameInfo:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...

class Expr:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def location(self) -> SourceLocation: ...

class Fixup:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def kind_info(self) -> FixupKindInfo: ...
    @property
    def offset(self) -> int: ...
    @property
    def value(self) -> Expr: ...

class FixupKindInfo:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def bit_offset(self) -> int: ...
    @property
    def bit_size(self) -> int: ...
    @property
    def is_aligned_down_to_32_bits(self) -> int: ...
    @property
    def is_constant(self) -> int: ...
    @property
    def is_pc_rel(self) -> int: ...
    @property
    def is_target_dependent(self) -> int: ...
    @property
    def name(self) -> str: ...

class Instruction:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def desc(self) -> InstructionDesc: ...
    @property
    def name(self) -> str: ...
    @property
    def opcode(self) -> int: ...
    @property
    def operands(self) -> list[typing.Any]: ...

class InstructionDesc:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def can_fold_as_load(self) -> bool: ...
    @property
    def has_delay_slot(self) -> bool: ...
    @property
    def has_optional_def(self) -> bool: ...
    @property
    def has_unmodeled_side_effects(self) -> bool: ...
    @property
    def implicit_defs(self) -> list[Register]: ...
    @property
    def implicit_uses(self) -> list[Register]: ...
    @property
    def is_add(self) -> bool: ...
    @property
    def is_authenticated(self) -> bool: ...
    @property
    def is_barrier(self) -> bool: ...
    @property
    def is_bitcast(self) -> bool: ...
    @property
    def is_branch(self) -> bool: ...
    @property
    def is_call(self) -> bool: ...
    @property
    def is_compare(self) -> bool: ...
    @property
    def is_conditional_branch(self) -> bool: ...
    @property
    def is_convergent(self) -> bool: ...
    @property
    def is_extract_subreg_like(self) -> bool: ...
    @property
    def is_indirect_branch(self) -> bool: ...
    @property
    def is_insert_subreg_like(self) -> bool: ...
    @property
    def is_move_immediate(self) -> bool: ...
    @property
    def is_move_reg(self) -> bool: ...
    @property
    def is_not_duplicable(self) -> bool: ...
    @property
    def is_predicable(self) -> bool: ...
    @property
    def is_pseudo(self) -> bool: ...
    @property
    def is_reg_sequence_like(self) -> bool: ...
    @property
    def is_return(self) -> bool: ...
    @property
    def is_select(self) -> bool: ...
    @property
    def is_terminator(self) -> bool: ...
    @property
    def is_trap(self) -> bool: ...
    @property
    def is_unconditional_branch(self) -> bool: ...
    @property
    def is_variadic(self) -> bool: ...
    @property
    def may_load(self) -> bool: ...
    @property
    def may_raise_fp_exception(self) -> bool: ...
    @property
    def may_store(self) -> bool: ...
    @property
    def variadic_ops_are_defs(self) -> bool: ...

class MipsExprKind:
    """
    Members:

      None_

      CALL_HI16

      CALL_LO16

      DTPREL

      DTPREL_HI

      DTPREL_LO

      GOT

      GOTTPREL

      GOT_CALL

      GOT_DISP

      GOT_HI16

      GOT_LO16

      GOT_OFST

      GOT_PAGE

      GPREL

      HI

      HIGHER

      HIGHEST

      LO

      NEG

      PCREL_HI16

      PCREL_LO16

      TLSGD

      TLSLDM

      TPREL_HI

      TPREL_LO

      Special
    """

    CALL_HI16: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.CALL_HI16: 1>
    CALL_LO16: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.CALL_LO16: 2>
    DTPREL: typing.ClassVar[MipsExprKind]  # value = <MipsExprKind.DTPREL: 3>
    DTPREL_HI: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.DTPREL_HI: 4>
    DTPREL_LO: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.DTPREL_LO: 5>
    GOT: typing.ClassVar[MipsExprKind]  # value = <MipsExprKind.GOT: 6>
    GOTTPREL: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.GOTTPREL: 7>
    GOT_CALL: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.GOT_CALL: 8>
    GOT_DISP: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.GOT_DISP: 9>
    GOT_HI16: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.GOT_HI16: 10>
    GOT_LO16: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.GOT_LO16: 11>
    GOT_OFST: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.GOT_OFST: 12>
    GOT_PAGE: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.GOT_PAGE: 13>
    GPREL: typing.ClassVar[MipsExprKind]  # value = <MipsExprKind.GPREL: 14>
    HI: typing.ClassVar[MipsExprKind]  # value = <MipsExprKind.HI: 15>
    HIGHER: typing.ClassVar[MipsExprKind]  # value = <MipsExprKind.HIGHER: 16>
    HIGHEST: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.HIGHEST: 17>
    LO: typing.ClassVar[MipsExprKind]  # value = <MipsExprKind.LO: 18>
    NEG: typing.ClassVar[MipsExprKind]  # value = <MipsExprKind.NEG: 19>
    None_: typing.ClassVar[MipsExprKind]  # value = <MipsExprKind.None_: 0>
    PCREL_HI16: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.PCREL_HI16: 20>
    PCREL_LO16: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.PCREL_LO16: 21>
    Special: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.Special: 26>
    TLSGD: typing.ClassVar[MipsExprKind]  # value = <MipsExprKind.TLSGD: 22>
    TLSLDM: typing.ClassVar[MipsExprKind]  # value = <MipsExprKind.TLSLDM: 23>
    TPREL_HI: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.TPREL_HI: 24>
    TPREL_LO: typing.ClassVar[
        MipsExprKind
    ]  # value = <MipsExprKind.TPREL_LO: 25>
    __members__: typing.ClassVar[
        dict[str, MipsExprKind]
    ]  # value = {'None_': <MipsExprKind.None_: 0>, 'CALL_HI16': <MipsExprKind.CALL_HI16: 1>, 'CALL_LO16': <MipsExprKind.CALL_LO16: 2>, 'DTPREL': <MipsExprKind.DTPREL: 3>, 'DTPREL_HI': <MipsExprKind.DTPREL_HI: 4>, 'DTPREL_LO': <MipsExprKind.DTPREL_LO: 5>, 'GOT': <MipsExprKind.GOT: 6>, 'GOTTPREL': <MipsExprKind.GOTTPREL: 7>, 'GOT_CALL': <MipsExprKind.GOT_CALL: 8>, 'GOT_DISP': <MipsExprKind.GOT_DISP: 9>, 'GOT_HI16': <MipsExprKind.GOT_HI16: 10>, 'GOT_LO16': <MipsExprKind.GOT_LO16: 11>, 'GOT_OFST': <MipsExprKind.GOT_OFST: 12>, 'GOT_PAGE': <MipsExprKind.GOT_PAGE: 13>, 'GPREL': <MipsExprKind.GPREL: 14>, 'HI': <MipsExprKind.HI: 15>, 'HIGHER': <MipsExprKind.HIGHER: 16>, 'HIGHEST': <MipsExprKind.HIGHEST: 17>, 'LO': <MipsExprKind.LO: 18>, 'NEG': <MipsExprKind.NEG: 19>, 'PCREL_HI16': <MipsExprKind.PCREL_HI16: 20>, 'PCREL_LO16': <MipsExprKind.PCREL_LO16: 21>, 'TLSGD': <MipsExprKind.TLSGD: 22>, 'TLSLDM': <MipsExprKind.TLSLDM: 23>, 'TPREL_HI': <MipsExprKind.TPREL_HI: 24>, 'TPREL_LO': <MipsExprKind.TPREL_LO: 25>, 'Special': <MipsExprKind.Special: 26>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    def __eq__(self, other: typing.Any) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: typing.Any) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    def __str__(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class Register:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def id(self) -> int: ...
    @property
    def is_physical_register(self) -> bool: ...
    @property
    def is_stack_slot(self) -> bool: ...
    @property
    def name(self) -> str: ...

class Section:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def name(self) -> str: ...

class SectionCOFF(Section):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def characteristics(self) -> int: ...

class SectionELF(Section):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def flags(self) -> int: ...
    @property
    def type(self) -> int: ...

class SectionMachO(Section):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def segment_name(self) -> str: ...

class SourceLocation:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    def __iter__(self) -> typing.Iterator: ...
    def __str__(self) -> str: ...
    @property
    def lineno(self) -> int: ...
    @property
    def offset(self) -> int: ...

class Symbol:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def is_temporary(self) -> bool: ...
    @property
    def name(self) -> str: ...

class SymbolAttr:
    """
    Members:

      Cold

      ELF_TypeFunction

      ELF_TypeIndFunction

      ELF_TypeObject

      ELF_TypeTLS

      ELF_TypeCommon

      ELF_TypeNoType

      ELF_TypeGnuUniqueObject

      Global

      LGlobal

      Hidden

      IndirectSymbol

      Internal

      LazyReference

      Local

      NoDeadStrip

      SymbolResolver

      AltEntry

      PrivateExtern

      Protected

      Reference

      Weak

      WeakDefinition

      WeakReference

      WeakDefAutoPrivate
    """

    AltEntry: typing.ClassVar[SymbolAttr]  # value = <SymbolAttr.AltEntry: 19>
    Cold: typing.ClassVar[SymbolAttr]  # value = <SymbolAttr.Cold: 1>
    ELF_TypeCommon: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.ELF_TypeCommon: 6>
    ELF_TypeFunction: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.ELF_TypeFunction: 2>
    ELF_TypeGnuUniqueObject: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.ELF_TypeGnuUniqueObject: 8>
    ELF_TypeIndFunction: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.ELF_TypeIndFunction: 3>
    ELF_TypeNoType: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.ELF_TypeNoType: 7>
    ELF_TypeObject: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.ELF_TypeObject: 4>
    ELF_TypeTLS: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.ELF_TypeTLS: 5>
    Global: typing.ClassVar[SymbolAttr]  # value = <SymbolAttr.Global: 9>
    Hidden: typing.ClassVar[SymbolAttr]  # value = <SymbolAttr.Hidden: 12>
    IndirectSymbol: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.IndirectSymbol: 13>
    Internal: typing.ClassVar[SymbolAttr]  # value = <SymbolAttr.Internal: 14>
    LGlobal: typing.ClassVar[SymbolAttr]  # value = <SymbolAttr.LGlobal: 10>
    LazyReference: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.LazyReference: 15>
    Local: typing.ClassVar[SymbolAttr]  # value = <SymbolAttr.Local: 16>
    NoDeadStrip: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.NoDeadStrip: 17>
    PrivateExtern: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.PrivateExtern: 20>
    Protected: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.Protected: 21>
    Reference: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.Reference: 22>
    SymbolResolver: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.SymbolResolver: 18>
    Weak: typing.ClassVar[SymbolAttr]  # value = <SymbolAttr.Weak: 23>
    WeakDefAutoPrivate: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.WeakDefAutoPrivate: 26>
    WeakDefinition: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.WeakDefinition: 24>
    WeakReference: typing.ClassVar[
        SymbolAttr
    ]  # value = <SymbolAttr.WeakReference: 25>
    __members__: typing.ClassVar[
        dict[str, SymbolAttr]
    ]  # value = {'Cold': <SymbolAttr.Cold: 1>, 'ELF_TypeFunction': <SymbolAttr.ELF_TypeFunction: 2>, 'ELF_TypeIndFunction': <SymbolAttr.ELF_TypeIndFunction: 3>, 'ELF_TypeObject': <SymbolAttr.ELF_TypeObject: 4>, 'ELF_TypeTLS': <SymbolAttr.ELF_TypeTLS: 5>, 'ELF_TypeCommon': <SymbolAttr.ELF_TypeCommon: 6>, 'ELF_TypeNoType': <SymbolAttr.ELF_TypeNoType: 7>, 'ELF_TypeGnuUniqueObject': <SymbolAttr.ELF_TypeGnuUniqueObject: 8>, 'Global': <SymbolAttr.Global: 9>, 'LGlobal': <SymbolAttr.LGlobal: 10>, 'Hidden': <SymbolAttr.Hidden: 12>, 'IndirectSymbol': <SymbolAttr.IndirectSymbol: 13>, 'Internal': <SymbolAttr.Internal: 14>, 'LazyReference': <SymbolAttr.LazyReference: 15>, 'Local': <SymbolAttr.Local: 16>, 'NoDeadStrip': <SymbolAttr.NoDeadStrip: 17>, 'SymbolResolver': <SymbolAttr.SymbolResolver: 18>, 'AltEntry': <SymbolAttr.AltEntry: 19>, 'PrivateExtern': <SymbolAttr.PrivateExtern: 20>, 'Protected': <SymbolAttr.Protected: 21>, 'Reference': <SymbolAttr.Reference: 22>, 'Weak': <SymbolAttr.Weak: 23>, 'WeakDefinition': <SymbolAttr.WeakDefinition: 24>, 'WeakReference': <SymbolAttr.WeakReference: 25>, 'WeakDefAutoPrivate': <SymbolAttr.WeakDefAutoPrivate: 26>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    def __eq__(self, other: typing.Any) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: typing.Any) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    def __str__(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class SymbolRefExpr(Expr):
    class VariantKind:
        """
        Members:

          None_

          Invalid

          GOT

          GOTOFF

          GOTREL

          PCREL

          GOTPCREL

          GOTTPOFF

          INDNTPOFF

          NTPOFF

          GOTNTPOFF

          PLT

          TLSGD

          TLSLD

          TLSLDM

          TPOFF

          DTPOFF

          TLSCALL

          TLSDESC

          TLVP

          TLVPPAGE

          TLVPPAGEOFF

          PAGE

          PAGEOFF

          GOTPAGE

          GOTPAGEOFF

          SECREL

          SIZE

          WEAKREF

          X86_ABS8

          X86_PLTOFF

          ARM_NONE

          ARM_GOT_PREL

          ARM_TARGET1

          ARM_TARGET2

          ARM_PREL31

          ARM_SBREL

          ARM_TLSLDO

          ARM_TLSDESCSEQ

          AVR_NONE

          AVR_LO8

          AVR_HI8

          AVR_HLO8

          AVR_DIFF8

          AVR_DIFF16

          AVR_DIFF32

          AVR_PM

          PPC_LO

          PPC_HI

          PPC_HA

          PPC_HIGH

          PPC_HIGHA

          PPC_HIGHER

          PPC_HIGHERA

          PPC_HIGHEST

          PPC_HIGHESTA

          PPC_GOT_LO

          PPC_GOT_HI

          PPC_GOT_HA

          PPC_TOCBASE

          PPC_TOC

          PPC_TOC_LO

          PPC_TOC_HI

          PPC_TOC_HA

          PPC_U

          PPC_L

          PPC_DTPMOD

          PPC_TPREL_LO

          PPC_TPREL_HI

          PPC_TPREL_HA

          PPC_TPREL_HIGH

          PPC_TPREL_HIGHA

          PPC_TPREL_HIGHER

          PPC_TPREL_HIGHERA

          PPC_TPREL_HIGHEST

          PPC_TPREL_HIGHESTA

          PPC_DTPREL_LO

          PPC_DTPREL_HI

          PPC_DTPREL_HA

          PPC_DTPREL_HIGH

          PPC_DTPREL_HIGHA

          PPC_DTPREL_HIGHER

          PPC_DTPREL_HIGHERA

          PPC_DTPREL_HIGHEST

          PPC_DTPREL_HIGHESTA

          PPC_GOT_TPREL

          PPC_GOT_TPREL_LO

          PPC_GOT_TPREL_HI

          PPC_GOT_TPREL_HA

          PPC_GOT_DTPREL

          PPC_GOT_DTPREL_LO

          PPC_GOT_DTPREL_HI

          PPC_GOT_DTPREL_HA

          PPC_TLS

          PPC_GOT_TLSGD

          PPC_GOT_TLSGD_LO

          PPC_GOT_TLSGD_HI

          PPC_GOT_TLSGD_HA

          PPC_TLSGD

          PPC_AIX_TLSGD

          PPC_AIX_TLSGDM

          PPC_GOT_TLSLD

          PPC_GOT_TLSLD_LO

          PPC_GOT_TLSLD_HI

          PPC_GOT_TLSLD_HA

          PPC_GOT_PCREL

          PPC_GOT_TLSGD_PCREL

          PPC_GOT_TLSLD_PCREL

          PPC_GOT_TPREL_PCREL

          PPC_TLS_PCREL

          PPC_TLSLD

          PPC_LOCAL

          PPC_NOTOC

          PPC_PCREL_OPT

          COFF_IMGREL32

          Hexagon_LO16

          Hexagon_HI16

          Hexagon_GPREL

          Hexagon_GD_GOT

          Hexagon_LD_GOT

          Hexagon_GD_PLT

          Hexagon_LD_PLT

          Hexagon_IE

          Hexagon_IE_GOT

          WASM_TYPEINDEX

          WASM_TLSREL

          WASM_MBREL

          WASM_TBREL

          AMDGPU_GOTPCREL32_LO

          AMDGPU_GOTPCREL32_HI

          AMDGPU_REL32_LO

          AMDGPU_REL32_HI

          AMDGPU_REL64

          AMDGPU_ABS32_LO

          AMDGPU_ABS32_HI

          VE_HI32

          VE_LO32

          VE_PC_HI32

          VE_PC_LO32

          VE_GOT_HI32

          VE_GOT_LO32

          VE_GOTOFF_HI32

          VE_GOTOFF_LO32

          VE_PLT_HI32

          VE_PLT_LO32

          VE_TLS_GD_HI32

          VE_TLS_GD_LO32

          VE_TPOFF_HI32

          VE_TPOFF_LO32

          TPREL

          DTPREL
        """

        AMDGPU_ABS32_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AMDGPU_ABS32_HI: 136>
        AMDGPU_ABS32_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AMDGPU_ABS32_LO: 135>
        AMDGPU_GOTPCREL32_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AMDGPU_GOTPCREL32_HI: 131>
        AMDGPU_GOTPCREL32_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AMDGPU_GOTPCREL32_LO: 130>
        AMDGPU_REL32_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AMDGPU_REL32_HI: 133>
        AMDGPU_REL32_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AMDGPU_REL32_LO: 132>
        AMDGPU_REL64: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AMDGPU_REL64: 134>
        ARM_GOT_PREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.ARM_GOT_PREL: 33>
        ARM_NONE: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.ARM_NONE: 32>
        ARM_PREL31: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.ARM_PREL31: 36>
        ARM_SBREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.ARM_SBREL: 37>
        ARM_TARGET1: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.ARM_TARGET1: 34>
        ARM_TARGET2: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.ARM_TARGET2: 35>
        ARM_TLSDESCSEQ: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.ARM_TLSDESCSEQ: 39>
        ARM_TLSLDO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.ARM_TLSLDO: 38>
        AVR_DIFF16: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AVR_DIFF16: 45>
        AVR_DIFF32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AVR_DIFF32: 46>
        AVR_DIFF8: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AVR_DIFF8: 44>
        AVR_HI8: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AVR_HI8: 42>
        AVR_HLO8: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AVR_HLO8: 43>
        AVR_LO8: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AVR_LO8: 41>
        AVR_NONE: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AVR_NONE: 40>
        AVR_PM: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.AVR_PM: 47>
        COFF_IMGREL32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.COFF_IMGREL32: 115>
        DTPOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.DTPOFF: 17>
        DTPREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.DTPREL: 152>
        GOT: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.GOT: 2>
        GOTNTPOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.GOTNTPOFF: 11>
        GOTOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.GOTOFF: 3>
        GOTPAGE: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.GOTPAGE: 25>
        GOTPAGEOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.GOTPAGEOFF: 26>
        GOTPCREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.GOTPCREL: 6>
        GOTREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.GOTREL: 4>
        GOTTPOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.GOTTPOFF: 8>
        Hexagon_GD_GOT: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.Hexagon_GD_GOT: 119>
        Hexagon_GD_PLT: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.Hexagon_GD_PLT: 121>
        Hexagon_GPREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.Hexagon_GPREL: 118>
        Hexagon_HI16: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.Hexagon_HI16: 117>
        Hexagon_IE: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.Hexagon_IE: 123>
        Hexagon_IE_GOT: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.Hexagon_IE_GOT: 124>
        Hexagon_LD_GOT: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.Hexagon_LD_GOT: 120>
        Hexagon_LD_PLT: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.Hexagon_LD_PLT: 122>
        Hexagon_LO16: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.Hexagon_LO16: 116>
        INDNTPOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.INDNTPOFF: 9>
        Invalid: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.Invalid: 1>
        NTPOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.NTPOFF: 10>
        None_: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.None_: 0>
        PAGE: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PAGE: 23>
        PAGEOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PAGEOFF: 24>
        PCREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PCREL: 5>
        PLT: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PLT: 12>
        PPC_AIX_TLSGD: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_AIX_TLSGD: 100>
        PPC_AIX_TLSGDM: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_AIX_TLSGDM: 101>
        PPC_DTPMOD: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_DTPMOD: 67>
        PPC_DTPREL_HA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_DTPREL_HA: 79>
        PPC_DTPREL_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_DTPREL_HI: 78>
        PPC_DTPREL_HIGH: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_DTPREL_HIGH: 80>
        PPC_DTPREL_HIGHA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_DTPREL_HIGHA: 81>
        PPC_DTPREL_HIGHER: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_DTPREL_HIGHER: 82>
        PPC_DTPREL_HIGHERA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_DTPREL_HIGHERA: 83>
        PPC_DTPREL_HIGHEST: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_DTPREL_HIGHEST: 84>
        PPC_DTPREL_HIGHESTA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_DTPREL_HIGHESTA: 85>
        PPC_DTPREL_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_DTPREL_LO: 77>
        PPC_GOT_DTPREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_DTPREL: 90>
        PPC_GOT_DTPREL_HA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_DTPREL_HA: 93>
        PPC_GOT_DTPREL_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_DTPREL_HI: 92>
        PPC_GOT_DTPREL_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_DTPREL_LO: 91>
        PPC_GOT_HA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_HA: 59>
        PPC_GOT_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_HI: 58>
        PPC_GOT_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_LO: 57>
        PPC_GOT_PCREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_PCREL: 106>
        PPC_GOT_TLSGD: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TLSGD: 95>
        PPC_GOT_TLSGD_HA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TLSGD_HA: 98>
        PPC_GOT_TLSGD_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TLSGD_HI: 97>
        PPC_GOT_TLSGD_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TLSGD_LO: 96>
        PPC_GOT_TLSGD_PCREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TLSGD_PCREL: 107>
        PPC_GOT_TLSLD: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TLSLD: 102>
        PPC_GOT_TLSLD_HA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TLSLD_HA: 105>
        PPC_GOT_TLSLD_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TLSLD_HI: 104>
        PPC_GOT_TLSLD_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TLSLD_LO: 103>
        PPC_GOT_TLSLD_PCREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TLSLD_PCREL: 108>
        PPC_GOT_TPREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TPREL: 86>
        PPC_GOT_TPREL_HA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TPREL_HA: 89>
        PPC_GOT_TPREL_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TPREL_HI: 88>
        PPC_GOT_TPREL_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TPREL_LO: 87>
        PPC_GOT_TPREL_PCREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_GOT_TPREL_PCREL: 109>
        PPC_HA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_HA: 50>
        PPC_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_HI: 49>
        PPC_HIGH: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_HIGH: 51>
        PPC_HIGHA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_HIGHA: 52>
        PPC_HIGHER: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_HIGHER: 53>
        PPC_HIGHERA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_HIGHERA: 54>
        PPC_HIGHEST: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_HIGHEST: 55>
        PPC_HIGHESTA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_HIGHESTA: 56>
        PPC_L: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_L: 66>
        PPC_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_LO: 48>
        PPC_LOCAL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_LOCAL: 112>
        PPC_NOTOC: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_NOTOC: 113>
        PPC_PCREL_OPT: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_PCREL_OPT: 114>
        PPC_TLS: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TLS: 94>
        PPC_TLSGD: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TLSGD: 99>
        PPC_TLSLD: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TLSLD: 111>
        PPC_TLS_PCREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TLS_PCREL: 110>
        PPC_TOC: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TOC: 61>
        PPC_TOCBASE: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TOCBASE: 60>
        PPC_TOC_HA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TOC_HA: 64>
        PPC_TOC_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TOC_HI: 63>
        PPC_TOC_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TOC_LO: 62>
        PPC_TPREL_HA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TPREL_HA: 70>
        PPC_TPREL_HI: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TPREL_HI: 69>
        PPC_TPREL_HIGH: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TPREL_HIGH: 71>
        PPC_TPREL_HIGHA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TPREL_HIGHA: 72>
        PPC_TPREL_HIGHER: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TPREL_HIGHER: 73>
        PPC_TPREL_HIGHERA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TPREL_HIGHERA: 74>
        PPC_TPREL_HIGHEST: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TPREL_HIGHEST: 75>
        PPC_TPREL_HIGHESTA: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TPREL_HIGHESTA: 76>
        PPC_TPREL_LO: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_TPREL_LO: 68>
        PPC_U: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.PPC_U: 65>
        SECREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.SECREL: 27>
        SIZE: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.SIZE: 28>
        TLSCALL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.TLSCALL: 18>
        TLSDESC: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.TLSDESC: 19>
        TLSGD: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.TLSGD: 13>
        TLSLD: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.TLSLD: 14>
        TLSLDM: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.TLSLDM: 15>
        TLVP: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.TLVP: 20>
        TLVPPAGE: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.TLVPPAGE: 21>
        TLVPPAGEOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.TLVPPAGEOFF: 22>
        TPOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.TPOFF: 16>
        TPREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.TPREL: 151>
        VE_GOTOFF_HI32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_GOTOFF_HI32: 143>
        VE_GOTOFF_LO32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_GOTOFF_LO32: 144>
        VE_GOT_HI32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_GOT_HI32: 141>
        VE_GOT_LO32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_GOT_LO32: 142>
        VE_HI32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_HI32: 137>
        VE_LO32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_LO32: 138>
        VE_PC_HI32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_PC_HI32: 139>
        VE_PC_LO32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_PC_LO32: 140>
        VE_PLT_HI32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_PLT_HI32: 145>
        VE_PLT_LO32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_PLT_LO32: 146>
        VE_TLS_GD_HI32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_TLS_GD_HI32: 147>
        VE_TLS_GD_LO32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_TLS_GD_LO32: 148>
        VE_TPOFF_HI32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_TPOFF_HI32: 149>
        VE_TPOFF_LO32: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.VE_TPOFF_LO32: 150>
        WASM_MBREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.WASM_MBREL: 127>
        WASM_TBREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.WASM_TBREL: 128>
        WASM_TLSREL: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.WASM_TLSREL: 126>
        WASM_TYPEINDEX: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.WASM_TYPEINDEX: 125>
        WEAKREF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.WEAKREF: 29>
        X86_ABS8: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.X86_ABS8: 30>
        X86_PLTOFF: typing.ClassVar[
            SymbolRefExpr.VariantKind
        ]  # value = <VariantKind.X86_PLTOFF: 31>
        __members__: typing.ClassVar[
            dict[str, SymbolRefExpr.VariantKind]
        ]  # value = {'None_': <VariantKind.None_: 0>, 'Invalid': <VariantKind.Invalid: 1>, 'GOT': <VariantKind.GOT: 2>, 'GOTOFF': <VariantKind.GOTOFF: 3>, 'GOTREL': <VariantKind.GOTREL: 4>, 'PCREL': <VariantKind.PCREL: 5>, 'GOTPCREL': <VariantKind.GOTPCREL: 6>, 'GOTTPOFF': <VariantKind.GOTTPOFF: 8>, 'INDNTPOFF': <VariantKind.INDNTPOFF: 9>, 'NTPOFF': <VariantKind.NTPOFF: 10>, 'GOTNTPOFF': <VariantKind.GOTNTPOFF: 11>, 'PLT': <VariantKind.PLT: 12>, 'TLSGD': <VariantKind.TLSGD: 13>, 'TLSLD': <VariantKind.TLSLD: 14>, 'TLSLDM': <VariantKind.TLSLDM: 15>, 'TPOFF': <VariantKind.TPOFF: 16>, 'DTPOFF': <VariantKind.DTPOFF: 17>, 'TLSCALL': <VariantKind.TLSCALL: 18>, 'TLSDESC': <VariantKind.TLSDESC: 19>, 'TLVP': <VariantKind.TLVP: 20>, 'TLVPPAGE': <VariantKind.TLVPPAGE: 21>, 'TLVPPAGEOFF': <VariantKind.TLVPPAGEOFF: 22>, 'PAGE': <VariantKind.PAGE: 23>, 'PAGEOFF': <VariantKind.PAGEOFF: 24>, 'GOTPAGE': <VariantKind.GOTPAGE: 25>, 'GOTPAGEOFF': <VariantKind.GOTPAGEOFF: 26>, 'SECREL': <VariantKind.SECREL: 27>, 'SIZE': <VariantKind.SIZE: 28>, 'WEAKREF': <VariantKind.WEAKREF: 29>, 'X86_ABS8': <VariantKind.X86_ABS8: 30>, 'X86_PLTOFF': <VariantKind.X86_PLTOFF: 31>, 'ARM_NONE': <VariantKind.ARM_NONE: 32>, 'ARM_GOT_PREL': <VariantKind.ARM_GOT_PREL: 33>, 'ARM_TARGET1': <VariantKind.ARM_TARGET1: 34>, 'ARM_TARGET2': <VariantKind.ARM_TARGET2: 35>, 'ARM_PREL31': <VariantKind.ARM_PREL31: 36>, 'ARM_SBREL': <VariantKind.ARM_SBREL: 37>, 'ARM_TLSLDO': <VariantKind.ARM_TLSLDO: 38>, 'ARM_TLSDESCSEQ': <VariantKind.ARM_TLSDESCSEQ: 39>, 'AVR_NONE': <VariantKind.AVR_NONE: 40>, 'AVR_LO8': <VariantKind.AVR_LO8: 41>, 'AVR_HI8': <VariantKind.AVR_HI8: 42>, 'AVR_HLO8': <VariantKind.AVR_HLO8: 43>, 'AVR_DIFF8': <VariantKind.AVR_DIFF8: 44>, 'AVR_DIFF16': <VariantKind.AVR_DIFF16: 45>, 'AVR_DIFF32': <VariantKind.AVR_DIFF32: 46>, 'AVR_PM': <VariantKind.AVR_PM: 47>, 'PPC_LO': <VariantKind.PPC_LO: 48>, 'PPC_HI': <VariantKind.PPC_HI: 49>, 'PPC_HA': <VariantKind.PPC_HA: 50>, 'PPC_HIGH': <VariantKind.PPC_HIGH: 51>, 'PPC_HIGHA': <VariantKind.PPC_HIGHA: 52>, 'PPC_HIGHER': <VariantKind.PPC_HIGHER: 53>, 'PPC_HIGHERA': <VariantKind.PPC_HIGHERA: 54>, 'PPC_HIGHEST': <VariantKind.PPC_HIGHEST: 55>, 'PPC_HIGHESTA': <VariantKind.PPC_HIGHESTA: 56>, 'PPC_GOT_LO': <VariantKind.PPC_GOT_LO: 57>, 'PPC_GOT_HI': <VariantKind.PPC_GOT_HI: 58>, 'PPC_GOT_HA': <VariantKind.PPC_GOT_HA: 59>, 'PPC_TOCBASE': <VariantKind.PPC_TOCBASE: 60>, 'PPC_TOC': <VariantKind.PPC_TOC: 61>, 'PPC_TOC_LO': <VariantKind.PPC_TOC_LO: 62>, 'PPC_TOC_HI': <VariantKind.PPC_TOC_HI: 63>, 'PPC_TOC_HA': <VariantKind.PPC_TOC_HA: 64>, 'PPC_U': <VariantKind.PPC_U: 65>, 'PPC_L': <VariantKind.PPC_L: 66>, 'PPC_DTPMOD': <VariantKind.PPC_DTPMOD: 67>, 'PPC_TPREL_LO': <VariantKind.PPC_TPREL_LO: 68>, 'PPC_TPREL_HI': <VariantKind.PPC_TPREL_HI: 69>, 'PPC_TPREL_HA': <VariantKind.PPC_TPREL_HA: 70>, 'PPC_TPREL_HIGH': <VariantKind.PPC_TPREL_HIGH: 71>, 'PPC_TPREL_HIGHA': <VariantKind.PPC_TPREL_HIGHA: 72>, 'PPC_TPREL_HIGHER': <VariantKind.PPC_TPREL_HIGHER: 73>, 'PPC_TPREL_HIGHERA': <VariantKind.PPC_TPREL_HIGHERA: 74>, 'PPC_TPREL_HIGHEST': <VariantKind.PPC_TPREL_HIGHEST: 75>, 'PPC_TPREL_HIGHESTA': <VariantKind.PPC_TPREL_HIGHESTA: 76>, 'PPC_DTPREL_LO': <VariantKind.PPC_DTPREL_LO: 77>, 'PPC_DTPREL_HI': <VariantKind.PPC_DTPREL_HI: 78>, 'PPC_DTPREL_HA': <VariantKind.PPC_DTPREL_HA: 79>, 'PPC_DTPREL_HIGH': <VariantKind.PPC_DTPREL_HIGH: 80>, 'PPC_DTPREL_HIGHA': <VariantKind.PPC_DTPREL_HIGHA: 81>, 'PPC_DTPREL_HIGHER': <VariantKind.PPC_DTPREL_HIGHER: 82>, 'PPC_DTPREL_HIGHERA': <VariantKind.PPC_DTPREL_HIGHERA: 83>, 'PPC_DTPREL_HIGHEST': <VariantKind.PPC_DTPREL_HIGHEST: 84>, 'PPC_DTPREL_HIGHESTA': <VariantKind.PPC_DTPREL_HIGHESTA: 85>, 'PPC_GOT_TPREL': <VariantKind.PPC_GOT_TPREL: 86>, 'PPC_GOT_TPREL_LO': <VariantKind.PPC_GOT_TPREL_LO: 87>, 'PPC_GOT_TPREL_HI': <VariantKind.PPC_GOT_TPREL_HI: 88>, 'PPC_GOT_TPREL_HA': <VariantKind.PPC_GOT_TPREL_HA: 89>, 'PPC_GOT_DTPREL': <VariantKind.PPC_GOT_DTPREL: 90>, 'PPC_GOT_DTPREL_LO': <VariantKind.PPC_GOT_DTPREL_LO: 91>, 'PPC_GOT_DTPREL_HI': <VariantKind.PPC_GOT_DTPREL_HI: 92>, 'PPC_GOT_DTPREL_HA': <VariantKind.PPC_GOT_DTPREL_HA: 93>, 'PPC_TLS': <VariantKind.PPC_TLS: 94>, 'PPC_GOT_TLSGD': <VariantKind.PPC_GOT_TLSGD: 95>, 'PPC_GOT_TLSGD_LO': <VariantKind.PPC_GOT_TLSGD_LO: 96>, 'PPC_GOT_TLSGD_HI': <VariantKind.PPC_GOT_TLSGD_HI: 97>, 'PPC_GOT_TLSGD_HA': <VariantKind.PPC_GOT_TLSGD_HA: 98>, 'PPC_TLSGD': <VariantKind.PPC_TLSGD: 99>, 'PPC_AIX_TLSGD': <VariantKind.PPC_AIX_TLSGD: 100>, 'PPC_AIX_TLSGDM': <VariantKind.PPC_AIX_TLSGDM: 101>, 'PPC_GOT_TLSLD': <VariantKind.PPC_GOT_TLSLD: 102>, 'PPC_GOT_TLSLD_LO': <VariantKind.PPC_GOT_TLSLD_LO: 103>, 'PPC_GOT_TLSLD_HI': <VariantKind.PPC_GOT_TLSLD_HI: 104>, 'PPC_GOT_TLSLD_HA': <VariantKind.PPC_GOT_TLSLD_HA: 105>, 'PPC_GOT_PCREL': <VariantKind.PPC_GOT_PCREL: 106>, 'PPC_GOT_TLSGD_PCREL': <VariantKind.PPC_GOT_TLSGD_PCREL: 107>, 'PPC_GOT_TLSLD_PCREL': <VariantKind.PPC_GOT_TLSLD_PCREL: 108>, 'PPC_GOT_TPREL_PCREL': <VariantKind.PPC_GOT_TPREL_PCREL: 109>, 'PPC_TLS_PCREL': <VariantKind.PPC_TLS_PCREL: 110>, 'PPC_TLSLD': <VariantKind.PPC_TLSLD: 111>, 'PPC_LOCAL': <VariantKind.PPC_LOCAL: 112>, 'PPC_NOTOC': <VariantKind.PPC_NOTOC: 113>, 'PPC_PCREL_OPT': <VariantKind.PPC_PCREL_OPT: 114>, 'COFF_IMGREL32': <VariantKind.COFF_IMGREL32: 115>, 'Hexagon_LO16': <VariantKind.Hexagon_LO16: 116>, 'Hexagon_HI16': <VariantKind.Hexagon_HI16: 117>, 'Hexagon_GPREL': <VariantKind.Hexagon_GPREL: 118>, 'Hexagon_GD_GOT': <VariantKind.Hexagon_GD_GOT: 119>, 'Hexagon_LD_GOT': <VariantKind.Hexagon_LD_GOT: 120>, 'Hexagon_GD_PLT': <VariantKind.Hexagon_GD_PLT: 121>, 'Hexagon_LD_PLT': <VariantKind.Hexagon_LD_PLT: 122>, 'Hexagon_IE': <VariantKind.Hexagon_IE: 123>, 'Hexagon_IE_GOT': <VariantKind.Hexagon_IE_GOT: 124>, 'WASM_TYPEINDEX': <VariantKind.WASM_TYPEINDEX: 125>, 'WASM_TLSREL': <VariantKind.WASM_TLSREL: 126>, 'WASM_MBREL': <VariantKind.WASM_MBREL: 127>, 'WASM_TBREL': <VariantKind.WASM_TBREL: 128>, 'AMDGPU_GOTPCREL32_LO': <VariantKind.AMDGPU_GOTPCREL32_LO: 130>, 'AMDGPU_GOTPCREL32_HI': <VariantKind.AMDGPU_GOTPCREL32_HI: 131>, 'AMDGPU_REL32_LO': <VariantKind.AMDGPU_REL32_LO: 132>, 'AMDGPU_REL32_HI': <VariantKind.AMDGPU_REL32_HI: 133>, 'AMDGPU_REL64': <VariantKind.AMDGPU_REL64: 134>, 'AMDGPU_ABS32_LO': <VariantKind.AMDGPU_ABS32_LO: 135>, 'AMDGPU_ABS32_HI': <VariantKind.AMDGPU_ABS32_HI: 136>, 'VE_HI32': <VariantKind.VE_HI32: 137>, 'VE_LO32': <VariantKind.VE_LO32: 138>, 'VE_PC_HI32': <VariantKind.VE_PC_HI32: 139>, 'VE_PC_LO32': <VariantKind.VE_PC_LO32: 140>, 'VE_GOT_HI32': <VariantKind.VE_GOT_HI32: 141>, 'VE_GOT_LO32': <VariantKind.VE_GOT_LO32: 142>, 'VE_GOTOFF_HI32': <VariantKind.VE_GOTOFF_HI32: 143>, 'VE_GOTOFF_LO32': <VariantKind.VE_GOTOFF_LO32: 144>, 'VE_PLT_HI32': <VariantKind.VE_PLT_HI32: 145>, 'VE_PLT_LO32': <VariantKind.VE_PLT_LO32: 146>, 'VE_TLS_GD_HI32': <VariantKind.VE_TLS_GD_HI32: 147>, 'VE_TLS_GD_LO32': <VariantKind.VE_TLS_GD_LO32: 148>, 'VE_TPOFF_HI32': <VariantKind.VE_TPOFF_HI32: 149>, 'VE_TPOFF_LO32': <VariantKind.VE_TPOFF_LO32: 150>, 'TPREL': <VariantKind.TPREL: 151>, 'DTPREL': <VariantKind.DTPREL: 152>}
        @staticmethod
        def _pybind11_conduit_v1_(*args, **kwargs): ...
        def __eq__(self, other: typing.Any) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: typing.Any) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        def __str__(self) -> str: ...
        @property
        def name(self) -> str: ...
        @property
        def value(self) -> int: ...

    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def symbol(self) -> Symbol: ...
    @property
    def variant_kind(self) -> SymbolRefExpr.VariantKind: ...

class TargetExpr(Expr):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...

class TargetExprAArch64(TargetExpr):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def sub_expr(self) -> Expr: ...
    @property
    def variant_kind_name(self) -> str: ...

class TargetExprMips(TargetExpr):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    @property
    def sub_expr(self) -> Expr: ...
    @property
    def variant_kind(self) -> int: ...

class VersionMinType:
    """
    Members:

      IOSVersionMin

      OSXVersionMin

      TvOSVersionMin

      WatchOSVersionMin
    """

    IOSVersionMin: typing.ClassVar[
        VersionMinType
    ]  # value = <VersionMinType.IOSVersionMin: 0>
    OSXVersionMin: typing.ClassVar[
        VersionMinType
    ]  # value = <VersionMinType.OSXVersionMin: 1>
    TvOSVersionMin: typing.ClassVar[
        VersionMinType
    ]  # value = <VersionMinType.TvOSVersionMin: 2>
    WatchOSVersionMin: typing.ClassVar[
        VersionMinType
    ]  # value = <VersionMinType.WatchOSVersionMin: 3>
    __members__: typing.ClassVar[
        dict[str, VersionMinType]
    ]  # value = {'IOSVersionMin': <VersionMinType.IOSVersionMin: 0>, 'OSXVersionMin': <VersionMinType.OSXVersionMin: 1>, 'TvOSVersionMin': <VersionMinType.TvOSVersionMin: 2>, 'WatchOSVersionMin': <VersionMinType.WatchOSVersionMin: 3>}
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs): ...
    def __eq__(self, other: typing.Any) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: typing.Any) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    def __str__(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...
