from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from rich_click import ParamType, BadParameter
import os, json


def json_write(d, f_out):
    with open(f_out, "w") as fp:
        json.dump(d, fp)


class FileWithExtension(ParamType):
    def __init__(self, ext: str):
        self.ext = ext.lower()
        self.name = "PATH"

    def convert(self, value, param, ctx):
        path = Path(value)
        if path.suffix.lower() != self.ext:
            self.fail(f"File must have extension {self.ext}", param, ctx)
        if path.exists() and not path.is_file():
            self.fail("Path exists and is not a file", param, ctx)
        parent = path.parent if path.parent != Path("") else Path(".")
        if not parent.exists():
            raise BadParameter(f"Directory {parent} does not exist.")
        if not os.access(parent, os.W_OK):
            raise BadParameter(f"Cannot write to directory {parent}.")
        return value


FileJSON = FileWithExtension(".json")

JinxMoleculeType = str


@dataclass
class JinxDef:
    resname: str
    name_string: str
    x: list[float]
    y: list[float]
    z: list[float]
    moltype: str

    @property
    def as_plain(self):
        outlist = []
        x_string = ", ".join(f"{num:.1f}" for num in self.x)
        y_string = ", ".join(f"{num:.1f}" for num in self.y)
        z_string = ", ".join(f"{num:.1f}" for num in self.z)
        outlist.append(f'moltype = "{self.moltype}"\n')
        outlist.append(f"lipidsx[moltype] = ({x_string})\n")
        outlist.append(f"lipidsy[moltype] = ({y_string})\n")
        outlist.append(f"lipidsz[moltype] = ({z_string})\n")
        outlist.append("lipidsa.update({ \n")
        outlist.append(f'    "{self.resname}": (moltype, "{self.name_string}"),\n')
        outlist.append("})\n")
        return "".join(outlist)

    @property
    def as_dict(self):
        return {
            self.moltype: {
                "x": self.x,
                "y": self.y,
                "z": self.z,
                "a": {self.resname: self.name_string},
            }
        }

        """
        "INOSITOLLIPIDS" : {
        "x" : [   0.5,  0.5,   0,  0.25,   0,   0, 0.5,  1,  0,   0.5,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,   1,   1],
        "y" : [    0,     0,   0,     0,   0,   0,   0,  0,  0,     0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
        "z" : [    8,     9,   9,   8.5,   7,  10,  10, 10,  6,     6,   5,   4,   3,   2,   1,   0,   5,   4,   3,   2,   1,   0],
        "a" : {
           "POPI": " C1   C2   C3   C4   PO4   -   -   -  GL1  GL2  C1A  D2A  C3A  C4A   -     -   C1B  C2B  C3B  C4B   -    -",
           "POP4": " C1   C2   C3   C4   PO4   -  P4   -  GL1  GL2  C1A  D2A  C3A  C4A   -     -   C1B  C2B  C3B  C4B   -    -",
           "POP5": " C1   C2   C3   C4   PO4   -   -  P5  GL1  GL2  C1A  D2A  C3A  C4A   -     -   C1B  C2B  C3B  C4B   -    -"
        }
        }
        }
        """


@dataclass
class AtomInfo:
    atom_name: str
    resname: str
    resid: int


def parse_file(filename) -> list[AtomInfo]:
    atoms_info = []
    in_atoms_section = False
    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if line == "[atoms]" or line == "[ atoms ]":
                in_atoms_section = True
                continue
            if in_atoms_section:
                if line.startswith("["):
                    break
                if not line.startswith(";") and line:
                    parts = line.split()
                    atoms_info.append(AtomInfo(parts[4], parts[3], int(parts[2])))
    return atoms_info


def file_to_bytesIO(f_in: str):
    print("Reading " + f_in)
    return BytesIO(Path(f_in).read_bytes())
