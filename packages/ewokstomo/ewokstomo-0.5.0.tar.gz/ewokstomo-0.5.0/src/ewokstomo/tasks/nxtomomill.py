from pathlib import Path

from ewokscore import Task
from nxtomomill.converter import from_h5_to_nx, from_blissfluo_to_nx
from nxtomomill.io.config import TomoHDF5Config
from nxtomomill.models.blissfluo2nx import BlissFluo2nxModel


class H5ToNx(
    Task, input_names=["bliss_hdf5_path", "nx_path"], output_names=["nx_path"]
):
    def run(self):
        """
        Convert an .h5 scan into .nx format using the nxtomomill API.

        Outputs:
            nx_path: Path to the created .nx file.
        """
        hdf5_path = Path(self.inputs.bliss_hdf5_path)
        nx_path_input = Path(self.inputs.nx_path)

        if not hdf5_path.is_file():
            raise FileNotFoundError(f"Input file not found: {hdf5_path}")

        output_file = nx_path_input
        output_file.parent.mkdir(parents=True, exist_ok=True)

        config = TomoHDF5Config()
        config.input_file = str(hdf5_path)
        config.output_file = str(output_file)
        config.single_file = True
        config.overwrite = True

        from_h5_to_nx(configuration=config)

        self.outputs.nx_path = str(output_file)


class FluoToNx(
    Task, input_names=["bliss_hdf5_path", "nx_path"], output_names=["nx_path"]
):
    def run(self):
        """
        Converts a .h5 XRFCT scan into .nx format using the nxtomomill API.
        :return: The path to the created .nx file
        """
        hdf5_path = Path(self.inputs.bliss_hdf5_path)
        nx_path_input = Path(self.inputs.nx_path)

        if not hdf5_path.is_file():
            raise FileNotFoundError(f"Input file not found: {hdf5_path}")

        output_file = nx_path_input
        output_file.parent.mkdir(parents=True, exist_ok=True)

        config = BlissFluo2nxModel()
        config.general_section.ewoksfluo_filename = str(hdf5_path)
        config.general_section.output_file = str(output_file)
        config.general_section.file_extension = ".nx"

        from_blissfluo_to_nx(configuration=config, progress=None)

        self.outputs.nx_path = str(output_file)
