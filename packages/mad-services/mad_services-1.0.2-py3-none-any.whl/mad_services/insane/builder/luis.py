####
#### Insane builder functions
####
from io import BytesIO
import MDAnalysis as mda
import numpy as np
import subprocess
from pathlib import Path
from .utils import JinxDef, parse_file
from uuid import uuid4
from collections import Counter
import os

## NEED TO CHECK GMX INSTALLATION !!!


class InsaneBuilderError(Exception):
    pass


class InsaneBuilder:
    required_ff_files: list[str] = [
        "martini_v3.0.0.itp",
        "martini_v3.0.0_ffbonded_v2_openbeta.itp",
        "martini_v3.0.0_solvents_v1.itp",
    ]
    base_ff_dir = None
    temp_dir: Path = Path("/tmp")
    required_gmx_files: list[str] = ["water.gro", "rel-igen.mdp", "min-igen.mdp"]

    ff_files_abs_path: list[Path] = []
    gmx_files_abs_path: dict[str, Path] = {}
    itp_input_file: Path | None = None

    with_nlt = False

    @classmethod
    def write(cls, input: BytesIO | None, ext: str, prefix=None) -> Path:
        """
        Returns a path to a uuid file in the temp folder
        if input is defined, writes its content
        if input is not defined, doesnot create the file just return the path
        """

        f_out_path = Path(
            f"{cls.temp_dir}/{uuid4() if prefix is None else prefix}.{ext}"
        )
        if input is None:
            return f_out_path

        with open(f_out_path, "wb") as f:
            f.write(input.getbuffer())
        return f_out_path

    @classmethod
    def setup(cls, base_ff_dir, base_gmx_dir, tmp_dir: str | None = None, nlt=True):
        cls.with_nlt = nlt
        for i, ifile in enumerate(cls.required_ff_files):
            _ = Path(f"{base_ff_dir}/{ifile}")
            if not _.exists():
                raise InsaneBuilderError(f"{base_ff_dir}/{ifile} not found")
            if i == 1 and not cls.with_nlt:
                continue
            cls.ff_files_abs_path.append(_.resolve())

        for ifile in cls.required_gmx_files:
            _ = Path(f"{base_gmx_dir}/{ifile}")
            if not _.exists():
                raise InsaneBuilderError(f"{base_gmx_dir}/{ifile} not found")
            cls.gmx_files_abs_path[ifile] = _.resolve()

        cls.base_gmx_dir = base_gmx_dir
        cls.base_ff_dir = base_ff_dir
        cls.temp_dir = Path.cwd()

        if tmp_dir is not None:
            _ = Path(tmp_dir)
            cls.temp_dir = _ if _.is_absolute() else Path.cwd() / _
        assert cls.temp_dir.is_dir() and os.access(cls.temp_dir, os.W_OK), (
            f"{cls.temp_dir} is not a writable directory"
        )

        try:
            _ = subprocess.run(
                ["gmx", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            raise InsaneBuilderError("gmx is NOT installed.")
        except subprocess.CalledProcessError:
            raise InsaneBuilderError("gmx exists but returned an error.")

    @classmethod
    def create_random_structure_from_itp(cls, itp_file) -> BytesIO:
        tmp_file = cls.write(None, "gro")
        atoms_info = parse_file(itp_file)
        cls.itp_input_file = Path(itp_file).resolve()

        sol = mda.Universe.empty(
            len(atoms_info),
            n_residues=1,
            atom_resindex=[0] * len(atoms_info),
            residue_segindex=[0],
            trajectory=True,
        )
        sol.add_TopologyAttr("name", [info.atom_name for info in atoms_info] * 1)
        sol.add_TopologyAttr("resname", [atoms_info[0].resname] * 1)
        sol.add_TopologyAttr("resid", [atoms_info[0].resid] * 1)
        poslis = []
        for i in range(len(sol.atoms)):
            poslis.append(
                [np.random.rand() * 10, np.random.rand() * 10, np.random.rand() * 10]
            )

        positions = np.array(poslis)
        sol.atoms.positions = positions

        sol.atoms.write(tmp_file)

        file_bytes = None
        with open(tmp_file, "rb") as f:  # open in binary mode
            file_bytes = f.read()
        _ = BytesIO(file_bytes)
        tmp_file.unlink()

        return _

    @classmethod
    def generateHeader(cls, struct_file) -> list[str]:
        return [
            f'#include "{rel_ff_file}"\n' for rel_ff_file in cls.ff_files_abs_path
        ] + [
            f'#include "{cls.itp_input_file}"\n',
            f'#include "{cls.temp_dir}/posres.itp"\n',
            "[system]\n",
            f"Get starting structure: {struct_file}\n",
            "\n",
            "[ molecules ]\n",
        ]

    @classmethod
    def get_starting_structure(cls, rdm_struct: BytesIO) -> BytesIO:
        """
        Starting from a completely random configuration of beads,
        this func controls their minimization and relaxation within
        a cylinder, so as to obtain the most lipid/membrane-like
        configuration possible.
        filename: input CG .itp file.
        """
        input_rdm_gro = cls.write(rdm_struct, "gro")
        counts = Counter(mda.Universe(input_rdm_gro).atoms.residues.resnames)
        num_atom = len(mda.Universe(input_rdm_gro).atoms)

        header = cls.generateHeader(input_rdm_gro)
        for item, count in counts.items():
            header.append(f"{item}    {count}\n")

        top_file = cls.write(None, "top", prefix="topol")
        with open(top_file, "w+") as topout:
            for line in header:
                topout.write(line)

        ## Write a restraint file.
        header = BytesIO()
        header.write(
            b"; Position restraint file for GROMACS\n; Restrain atoms within a cylinder of radius 0.3 nm and height parallel to the z-axis\n[ position_restraints ]\n;     atom     type     g    r(nm)    k\n"
        )

        for idx in np.arange(num_atom):
            header.write(f"  {idx + 1}  2      8    .3      250\n".encode("utf-8"))

        cls.write(header, "itp", prefix="posres")

        box_gro = cls.write(None, "gro", prefix="box")
        proc = subprocess.run(
            f"gmx editconf -f {input_rdm_gro} -o {box_gro} -box 11 11 11 -bt dodecahedron",
            shell=True,
            cwd=cls.temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        InsaneBuilder.assert_non_empty_file(
            box_gro, stage="get_starting_structure:create_box"
        )

        restraints_gro = cls.write(None, "gro", prefix="restraints")
        u = mda.Universe(box_gro)
        pos = u.atoms.positions.copy()
        pos[:, 0] = 40.0
        pos[:, 1] = 40
        u.atoms.positions = pos
        u.atoms.write(restraints_gro)

        tmp_outs = [
            cls.write(None, "gro", prefix="watered"),
            cls.write(None, "tpr", prefix="min-igen"),
            cls.write(None, "gro", prefix="min-igen"),
            cls.write(None, "tpr", prefix="rel-igen"),
            cls.write(None, "gro", prefix="rel-igen"),
        ]

        cmds = [
            f"gmx solvate -cp {box_gro} -cs {cls.gmx_files_abs_path['water.gro']} -p {top_file} -o {tmp_outs[0]} ",
            f"gmx grompp -f {cls.gmx_files_abs_path['min-igen.mdp']} -c {tmp_outs[0]} -p {top_file} -maxwarn 5 -r {restraints_gro} -o {tmp_outs[1]}",
            f"gmx mdrun -deffnm min-igen -v -nt 5 -pin on -pinoffset 0 -s {tmp_outs[1]}",
            f"gmx grompp -f {cls.gmx_files_abs_path['rel-igen.mdp']} -c {tmp_outs[2]} -p topol.top -o {tmp_outs[3]} -maxwarn 5 -r {restraints_gro}",
            f"gmx mdrun -deffnm rel-igen -v -nt 5 -pin on -pinoffset 0",
        ]

        for cmd, out in zip(cmds, tmp_outs):
            proc = subprocess.run(
                cmd,
                cwd=cls.temp_dir,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                InsaneBuilder.assert_non_empty_file(out, stage=cmd)
            except Exception as e:
                print(">Breaking process stderr::")
                curr_step_stderr = proc.stderr.decode("utf-8")
                print(curr_step_stderr)
                print(">Breaking process stdout::")
                curr_step_stdout = proc.stdout.decode("utf-8")
                print(curr_step_stdout)
                raise e
            # curr_step_stdout = proc.stdout.decode("utf-8")
            #
            # Checkpoint here
            #

        cleanagg_file = cls.write(None, "ndx", prefix="index")
        u = mda.Universe(tmp_outs[-1])
        cleanagg = u.select_atoms("not resname W NA CL ION BENZ")
        cleanagg.write(cleanagg_file, mode="w", name="Clean")

        structure_pdb_out = cls.write(None, "pdb")
        cmd = f"gmx trjconv -f {tmp_outs[-1]} -s {tmp_outs[-2]} -pbc whole -o {structure_pdb_out} -conect -n {cleanagg_file}"

        p = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cls.temp_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        #  curr_step_stdout = proc.stdout.decode("utf-8")
        #  curr_step_stderr = proc.stderr.decode("utf-8")
        p.communicate("Clean\n")
        p.wait()
        # Checkpoint here

        InsaneBuilder.assert_non_empty_file(structure_pdb_out, stage=cmd)

        # print("###" + str(structure_pdb_out.read_text()))
        # remove ENDMDL lines from file
        _ = structure_pdb_out.write_text(
            "".join(
                line
                for line in structure_pdb_out.read_text().splitlines(True)
                if "ENDMDL" not in line
            )
        )

        return BytesIO(structure_pdb_out.read_bytes())

    @classmethod
    def jinxanize(
        cls,
        structure: BytesIO,
    ) -> JinxDef:
        """
        This func takes in a lipid structure file, and writes out its insane entry.
        structure: any input structure file (gro, pdb, whatever as long as MDAnalyisis reads it.) Returns a list containing the insane entry.
        """
        input = cls.write(structure, "pdb")
        u = mda.Universe(input)
        moltype = "lipid"
        resname: str = u.atoms.residues.resnames[0]
        names = u.atoms.names
        pos_zero = (
            u.atoms.positions - u.atoms.center_of_geometry()
        )  ## center on the origin
        x = pos_zero[:, 0]
        y = pos_zero[:, 1]
        z = np.abs(
            pos_zero[:, 2] - pos_zero[:, 2][-1]
        )  ## scale height so it is correctly inserted in the membrane
        ## hardcoded to be -1 but should index of lowest inserted membrane bead.

        x_list = [float(round(num, 1)) for num in x]
        y_list = [float(round(num, 1)) for num in y]
        z_list = [float(round(num, 1)) for num in z]

        name_string = " ".join(names)

        return JinxDef(resname, name_string, x_list, y_list, z_list, moltype)

    @staticmethod
    def assert_non_empty_file(file, stage=""):
        if not (file.is_file() and file.stat().st_size > 0):
            raise InsaneBuilderError(f"{stage}: tmp file '{file}' is missing")

    @classmethod
    def clean_dir(cls):
        """
        proc = subprocess.call(
            f"rm rel.* min.* box.* mdout.mdp watered.gro posres.itp restraints.gro index.ndx \\#*",
            shell=True,
        )"""
        print(f"I should clean {cls.temp_dir}")

    """
    subprocess.call(
            f"gmx solvate -cp box.gro -cs {partition_tools_base}/solvents/water.gro -o watered.gro -p topol.top",
            shell=True,
            stdout=output_file,
            stderr=subprocess.STDOUT,
        )
        subprocess.call(
            f"gmx grompp -f {mdps}/min.mdp -c watered.gro -p topol.top -o min.tpr -maxwarn 5 -r restraints.gro",
            shell=True,
            stdout=output_file,
            stderr=subprocess.STDOUT,
        )
        subprocess.call(
            f"gmx mdrun -deffnm min -v -nt 5 -pin on -pinoffset 0",
            shell=True,
            stdout=output_file,
            stderr=subprocess.STDOUT,
        )
        subprocess.call(
            f"gmx grompp -f {mdps}/rel.mdp -c min.gro -p topol.top -o rel.tpr -maxwarn 5 -r restraints.gro",
            shell=True,
            stdout=output_file,
            stderr=subprocess.STDOUT,
        )
        subprocess.call(
            f"gmx mdrun -deffnm rel -v -nt 5 -pin on -pinoffset 0",
            shell=True,
            stdout=output_file,
            stderr=subprocess.STDOUT,
        )
     """
