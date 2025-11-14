from enum import Enum


class QuantitativeNeume(Enum):
    Ison = "ison"

    Oligon = "oligon"
    OligonPlusKentimaBelow = "oligonKentimaBelow"
    OligonPlusKentimaAbove = "oligonKentimaAbove"
    OligonPlusHypsiliRight = "oligonYpsiliRight"
    OligonPlusHypsiliLeft = "oligonYpsiliLeft"
    OligonPlusHypsiliPlusKentimaHorizontal = "oligonKentimaYpsiliRight"
    OligonPlusHypsiliPlusKentimaVertical = "oligonKentimaYpsiliMiddle"
    OligonPlusDoubleHypsili = "oligonDoubleYpsili"
    OligonKentimataDoubleYpsili = "oligonKentimataDoubleYpsili"
    OligonKentimaDoubleYpsiliRight = "oligonKentimaDoubleYpsiliRight"
    OligonKentimaDoubleYpsiliLeft = "oligonKentimaDoubleYpsiliLeft"
    OligonTripleYpsili = "oligonTripleYpsili"
    OligonKentimataTripleYpsili = "oligonKentimataTripleYpsili"
    OligonKentimaTripleYpsili = "oligonKentimaTripleYpsili"

    PetastiWithIson = "petastiIson"
    Petasti = "petasti"
    PetastiPlusOligon = "petastiOligon"
    PetastiPlusKentimaAbove = "petastiKentima"
    PetastiPlusHypsiliRight = "petastiYpsiliRight"
    PetastiPlusHypsiliLeft = "petastiYpsiliLeft"
    PetastiPlusHypsiliPlusKentimaHorizontal = "petastiKentimaYpsiliRight"
    PetastiPlusHypsiliPlusKentimaVertical = "petastiKentimaYpsiliMiddle"
    PetastiPlusDoubleHypsili = "petastiDoubleYpsili"
    PetastiKentimataDoubleYpsili = "petastiKentimataDoubleYpsili"
    PetastiKentimaDoubleYpsiliRight = "petastiKentimaDoubleYpsiliRight"
    PetastiKentimaDoubleYpsiliLeft = "petastiKentimaDoubleYpsiliLeft"
    PetastiTripleYpsili = "petastiTripleYpsili"
    PetastiKentimataTripleYpsili = "petastiKentimataTripleYpsili"
    PetastiKentimaTripleYpsili = "petastiKentimaTripleYpsili"

    Apostrophos = "apostrofos"
    Elaphron = "elafron"
    ElaphronPlusApostrophos = "elafronApostrofos"
    Hamili = "chamili"
    HamiliPlusApostrophos = "chamiliApostrofos"
    HamiliPlusElaphron = "chamiliElafron"
    HamiliPlusElaphronPlusApostrophos = "chamiliElafronApostrofos"
    DoubleHamili = "doubleChamili"
    DoubleHamiliApostrofos = "doubleChamiliApostrofos"
    DoubleHamiliElafron = "doubleChamiliElafron"
    DoubleHamiliElafronApostrofos = "doubleChamiliElafronApostrofos"
    TripleHamili = "tripleChamili"

    PetastiPlusApostrophos = "petastiApostrofos"
    PetastiPlusElaphron = "petastiElafron"
    PetastiPlusElaphronPlusApostrophos = "petastiElafronApostrofos"
    PetastiHamili = "petastiChamili"
    PetastiHamiliApostrofos = "petastiChamiliApostrofos"
    PetastiHamiliElafron = "petastiChamiliElafron"
    PetastiHamiliElafronApostrofos = "petastiChamiliElafronApostrofos"
    PetastiDoubleHamili = "petastiDoubleChamili"
    PetastiDoubleHamiliApostrofos = "petastiDoubleChamiliApostrofos"

    OligonPlusKentemata = "oligonKentimataAbove"
    KentemataPlusOligon = "oligonKentimataBelow"
    OligonPlusIsonPlusKentemata = "oligonIsonKentimata"
    OligonPlusApostrophosPlusKentemata = "oligonApostrofosKentimata"
    OligonPlusHyporoePlusKentemata = "oligonYporroiKentimata"
    OligonPlusElaphronPlusKentemata = "oligonElafronKentimata"
    OligonPlusElaphronPlusApostrophosPlusKentemata = "oligonElafronApostrofosKentimata"
    OligonPlusHamiliPlusKentemata = "oligonChamiliKentimata"

    RunningElaphron = "runningElafron"
    Hyporoe = "yporroi"
    PetastiPlusRunningElaphron = "petastiRunningElafron"
    PetastiPlusHyporoe = "petastiYporroi"

    OligonPlusIson = "oligonIson"
    OligonPlusApostrophos = "oligonApostrofos"
    OligonPlusElaphron = "oligonElafron"
    OligonPlusHyporoe = "oligonYporroi"
    OligonPlusElaphronPlusApostrophos = "oligonElafronApostrofos"
    OligonPlusHamili = "oligonChamili"

    Kentima = "kentima"
    OligonPlusKentima = "oligonKentimaMiddle"
    Kentemata = "kentimata"

    DoubleApostrophos = "apostrofosSyndesmos"
    OligonPlusRunningElaphronPlusKentemata = "oligonRunningElafronKentimata"
    IsonPlusApostrophos = "isonApostrofos"
    OligonKentimaMiddleKentimata = "oligonKentimaMiddleKentimata"
    OligonPlusKentemataPlusHypsiliLeft = "oligonYpsiliLeftKentimata"
    OligonPlusKentemataPlusHypsiliRight = "oligonYpsiliRightKentimata"

    VareiaDotted = "leimma1"
    VareiaDotted2 = "leimma2"
    VareiaDotted3 = "leimma3"
    VareiaDotted4 = "leimma4"
    Cross = "stavros"
    Breath = "breath"


class TimeNeume(Enum):
    Klasma_Top = "klasmaAbove"
    Klasma_Bottom = "klasmaBelow"

    Hapli = "apli"
    Dipli = "dipli"
    Tripli = "tripli"
    Tetrapli = "tetrapli"

    Koronis = "koronis"


class GorgonNeume(Enum):
    Gorgon_Top = "gorgonAbove"
    Gorgon_Bottom = "gorgonBelow"
    Digorgon = "digorgon"
    Trigorgon = "trigorgon"

    GorgonDottedLeft = "gorgonDottedLeft"
    GorgonDottedRight = "gorgonDottedRight"

    DigorgonDottedLeft1 = "digorgonDottedLeftBelow"
    DigorgonDottedLeft2 = "digorgonDottedLeftAbove"
    DigorgonDottedRight = "digorgonDottedRight"

    TrigorgonDottedLeft1 = "trigorgonDottedLeftBelow"
    TrigorgonDottedLeft2 = "trigorgonDottedLeftAbove"
    TrigorgonDottedRight = "trigorgonDottedRight"

    Argon = "argon"
    Hemiolion = "diargon"
    Diargon = "triargon"


class VocalExpressionNeume(Enum):
    Vareia = "vareia"
    HomalonConnecting = "omalonConnecting"
    Homalon = "omalon"
    Antikenoma = "antikenoma"
    Psifiston = "psifiston"
    Heteron = "heteron"
    HeteronConnecting = "heteronConnecting"
    Endofonon = "endofonon"
    Cross_Top = "stavrosAbove"


class TempoSign(Enum):
    VerySlow = "agogiPoliArgi"
    Slower = "agogiArgoteri"
    Slow = "agogiArgi"
    Medium = "agogiMetria"
    Moderate = "agogiMesi"
    Quick = "agogiGorgi"
    Quicker = "agogiGorgoteri"
    VeryQuick = "agogiPoliGorgi"


class Fthora(Enum):
    DiatonicNiLow_Top = "fthoraDiatonicNiLowAbove"
    DiatonicPa_Top = "fthoraDiatonicPaAbove"
    DiatonicVou_Top = "fthoraDiatonicVouAbove"
    DiatonicGa_Top = "fthoraDiatonicGaAbove"
    DiatonicThi_Top = "fthoraDiatonicDiAbove"
    DiatonicKe_Top = "fthoraDiatonicKeAbove"
    DiatonicZo_Top = "fthoraDiatonicZoAbove"
    DiatonicNiHigh_Top = "fthoraDiatonicNiHighAbove"
    HardChromaticPa_Top = "fthoraHardChromaticPaAbove"
    HardChromaticThi_Top = "fthoraHardChromaticDiAbove"
    SoftChromaticPa_Top = "fthoraSoftChromaticKeAbove"
    SoftChromaticThi_Top = "fthoraSoftChromaticDiAbove"
    Enharmonic_Top = "fthoraEnharmonicAbove"
    Zygos_Top = "chroaZygosAbove"
    Kliton_Top = "chroaKlitonAbove"
    Spathi_Top = "chroaSpathiAbove"

    DiatonicNiLow_Bottom = "fthoraDiatonicNiLowBelow"
    DiatonicPa_Bottom = "fthoraDiatonicPaBelow"
    DiatonicVou_Bottom = "fthoraDiatonicVouBelow"
    DiatonicGa_Bottom = "fthoraDiatonicGaBelow"
    DiatonicThi_Bottom = "fthoraDiatonicDiBelow"
    DiatonicKe_Bottom = "fthoraDiatonicKeBelow"
    DiatonicZo_Bottom = "fthoraDiatonicZoBelow"
    DiatonicNiHigh_Bottom = "fthoraDiatonicNiHighBelow"
    HardChromaticPa_Bottom = "fthoraHardChromaticPaBelow"
    HardChromaticThi_Bottom = "fthoraHardChromaticDiBelow"
    SoftChromaticPa_Bottom = "fthoraSoftChromaticKeBelow"
    SoftChromaticThi_Bottom = "fthoraSoftChromaticDiBelow"
    Enharmonic_Bottom = "fthoraEnharmonicBelow"
    Zygos_Bottom = "chroaZygosBelow"
    Kliton_Bottom = "chroaKlitonBelow"
    Spathi_Bottom = "chroaSpathiBelow"

    GeneralSharp_Top = "diesisGenikiAbove"
    GeneralSharp_Bottom = "diesisGenikiBelow"

    GeneralFlat_Top = "yfesisGenikiAbove"
    GeneralFlat_Bottom = "yfesisGenikiBelow"


class Accidental(Enum):
    Sharp_2_Left = "diesis2"
    Sharp_4_Left = "diesis4"
    Sharp_6_Left = "diesis6"
    Sharp_8_Left = "diesis8"

    Flat_2_Right = "yfesis2"
    Flat_4_Right = "yfesis4"
    Flat_6_Right = "yfesis6"
    Flat_8_Right = "yfesis8"
