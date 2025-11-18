from dataclasses import dataclass


@dataclass
class ScoreElement:
    pass


@dataclass
class NoteElement(ScoreElement):
    neume: str
    index: int
    gorgon: str | None = None
    quality: str | None = None
    time: str | None = None
    accidental: str | None = None
    fthora: str | None = None
    vareia: bool = False

    def to_dict(self):
        d = {
            "type": "note",
            "neume": self.neume,
            "accidental": self.accidental if self.accidental else None,
            "fthora": self.fthora if self.fthora else None,
            "gorgon": self.gorgon if self.gorgon else None,
            "time": self.time if self.time else None,
            "quality": (self.quality if self.quality else None),
        }

        if self.vareia:
            d["vareia"] = True

        return {k: v for k, v in d.items() if v is not None}


@dataclass
class MartyriaElement(ScoreElement):
    index: int
    fthora: str | None = None

    def to_dict(self):
        d = {"type": "martyria"}
        if self.fthora:
            d["fthora"] = self.fthora
        return d


@dataclass
class TempoElement(ScoreElement):
    index: int
    neume: str

    def to_dict(self):
        return {"type": "tempo", "neume": self.neume}


@dataclass
class EmptyElement(ScoreElement):

    pass
