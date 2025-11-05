import rich_click as click
from .luis import InsaneBuilder
from .utils import file_to_bytesIO, FileJSON, json_write
import sys
from pathlib import Path
from ...loggers.mda import redirect_mda_logger

DEFAULT_GMX = Path(__file__).parent / "../../data/"
DEFAULT_GMX = DEFAULT_GMX.resolve()


@click.command()
@click.argument(
    "itp_file",
    type=click.Path(readable=True),
    help="Molecule ITP file",
)
@click.argument(
    "json_output",
    type=FileJSON,
    help="Output file for jinxane definition",
)
@click.option(
    "--ff",
    type=click.Path(readable=True),
    help="Forcefield parameter files directory",
    required=True,
)
@click.option(
    "--gmx",
    type=click.Path(readable=True),
    help="GMX scripts directory",
    default=DEFAULT_GMX,
    show_default=True,
    required=False,
)
@click.option(
    "--pdb",
    type=click.Path(readable=True),
    help="A PDB file ready to be converted into insane definition",
    required=False,
)
@click.option(
    "--wdir",
    type=click.Path(readable=True),
    help="Temporary files directory",
    show_default=False,
    default="/tmp",
)
@click.option(
    "--old-lt",
    is_flag=True,
    help="Disable Kasper Lipid Tail model definitions (use old martini3 instead)",
    default=False,
    show_default=True,
)
@click.option(
    "--max-try",
    type=click.IntRange(1, 10),
    help="Maximum number of dynamic relaxation attempts",
    show_default=True,
    default=5,
)
def main(itp_file, json_output, ff, gmx, pdb, wdir, old_lt, max_try):
    redirect_mda_logger(Path.cwd() / "ibuild_mda.log")

    InsaneBuilder.setup(ff, gmx, wdir, not old_lt)

    run_count = 0
    errors: list[Exception] = []
    while run_count < max_try:
        if run_count > 0:
            sys.stderr.write(f"MainEror::Attemptin retry number {run_count}")
        run_count += 1

        try:
            if pdb is None:
                random_struct = InsaneBuilder.create_random_structure_from_itp(itp_file)
                # print(random_struct.getvalue().decode("utf-8"))

                proj_struct = InsaneBuilder.get_starting_structure(random_struct)
            else:
                proj_struct = file_to_bytesIO(pdb)

            jxdef = InsaneBuilder.jinxanize(proj_struct)
        except Exception as e:
            errors.append(e)
            continue

        print(jxdef)
        print(jxdef.as_plain)
        print(jxdef.as_dict)
        json_write(jxdef.as_dict, json_output)
        exit(0)

    sys.stderr.write(
        f"FatalError::Giving up after {max_try} attempts. Errors stacks:\n"
    )
    sys.stderr.write(f"\n####\n".join([str(_) for _ in errors]))
    sys.exit(1)
