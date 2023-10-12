import argparse
import os
import json
import numpy as np
from ._happydata_reader import HappyDataReader
from ._envi_reader import EnviReader
from happy.data import HappyData
import spectral.io.envi as envi

from typing import List, Optional, Tuple, Dict

# ENVI header file identifier for the wavelengths
WAVELENGTH = "wavelength="

ENVI_DTYPE_TO_NUMPY = {
    1: 'uint8',
    2: 'int16',
    3: 'int32',
    4: 'float32',
    5: 'float64',
    12: 'uint16',
    13: 'uint32',
    14: 'complex64',
    15: 'complex128'
}


class HappyReader(HappyDataReader):

    def __init__(self, base_dir: str = None, restrict_metadata: Optional[List] = None,
                 wavelength_override: Optional[List[float]] = None, wavelength_override_file: str = None):
        super().__init__(base_dir=base_dir)
        self.restrict_metadata = restrict_metadata
        self.wavelength_override = wavelength_override
        self.wavelength_override_file = wavelength_override_file

    def name(self) -> str:
        return "happy-reader"

    def description(self) -> str:
        return "Reads data in HAPPy format."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-r", "--restrict_metadata", metavar="FILENAME", type=str, help="The meta-data files to restrict to, omit to use all", required=False, nargs="*")
        parser.add_argument("-w", "--wavelength_override_file", metavar="FILE", type=str, help="A file with the wavelengths to use instead of the ones read from the actual ENVI files, can be either an ENVI-like file or a text file with one wavelength per line.", required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.base_dir = ns.base_dir
        if (ns.restrict_metadata is not None) and (len(ns.restrict_metadata) == 0):
            self.restrict_metadata = None
        else:
            self.restrict_metadata = ns.restrict_metadata
        self.wavelength_override_file = ns.wavelength_override_file

    def _initialize(self):
        super()._initialize()
        if self.wavelength_override_file is not None:
            if not os.path.exists(self.wavelength_override_file):
                raise Exception("Wavelength override file does not exist: %s" % self.wavelength_override_file)
            if not os.path.isdir(self.wavelength_override_file):
                self.wavelength_override = self._read_wavelength_file()

    def _read_wavelength_file(self) -> List[float]:
        result = []
        with open(self.wavelength_override_file, "r") as fp:
            lines = fp.readlines()

        if len(lines) > 0:
            # check whether envi header file
            is_envi = False
            for line in lines:
                line = line.strip().replace(" ", "")
                if line.startswith(WAVELENGTH):
                    is_envi = True
                    break
            # parse file
            if is_envi:
                wavelength_str = ""
                is_wavelengths = False
                for line in lines:
                    line = line.strip().replace(" ", "")
                    if line.startswith(WAVELENGTH):
                        is_wavelengths = True
                        if not line.endswith("{"):
                            wavelength_str += line[len(WAVELENGTH)+1:]
                        continue
                    if line.endswith("}"):
                        if len(line) > 1:
                            wavelength_str += line[:-1]
                        if not is_wavelengths:
                            raise Exception("No wavelengths stored?")
                        break
                    if is_wavelengths:
                        wavelength_str += line
                wavelengths = wavelength_str.split(",")
                for line in wavelengths:
                    line = line.strip()
                    if len(line) > 0:
                        try:
                            result.append(float(line))
                        except:
                            pass
            else:
                for line in lines:
                    line = line.strip()
                    if len(line) > 0:
                        try:
                            result.append(float(line))
                        except:
                            pass

        return result

    def _get_sample_ids(self) -> List[str]:
        sample_ids = []
        for sample_id in os.listdir(self.base_dir):
            sample_path = os.path.join(self.base_dir, sample_id)
            if os.path.isdir(sample_path):
                sample_ids.append(sample_id)
        return sample_ids
        
    def _split_sample_id(self, sample_id: str) -> Tuple[str, Optional[str]]:
        parts = sample_id.split(":")
        if len(parts) == 1:
            return parts[0], None
        elif len(parts) == 2:
            if len(parts[1]) == 0:
                return parts[0], None
            else:
                return parts[0], parts[1]
        else:
            raise ValueError(f"Invalid sample_id format: {sample_id}")

    def _load_data(self, sample_id: str) -> List[HappyData]:
        sample_id, region_dir = self._split_sample_id(sample_id)

        if region_dir is not None:
            return [self.load_region(sample_id, region_dir)]

        happy_data_list = []
        for region_dir in self._get_regions(sample_id):
            happy_data = self.load_region(sample_id, region_dir)
            happy_data_list.append(happy_data)

        return happy_data_list

    def _load_region(self, sample_id: str, region_name: str) -> HappyData:
        hyperspec_file_path = os.path.join(self.base_dir, sample_id, region_name, f'{sample_id}'+".hdr")
        print(f"{sample_id}:{region_name}")
        base_path = os.path.join(self.base_dir, sample_id, region_name)

        if os.path.exists(hyperspec_file_path):
            envi_reader = EnviReader(base_path)
            envi_reader.load_data(sample_id)
            hyperspec_data = envi_reader.get_numpy()

            # Load hyperspec metadata and mappings
            hyperspec_metadata = self._load_json(hyperspec_file_path.replace(".hdr", "_global.json"))
            metadata_dict = {}
            for metadata_file_path in self._get_metadata_file_paths(base_path):
                target_name = os.path.splitext(os.path.basename(metadata_file_path))[0]
                if target_name == sample_id:
                    continue
                metadata = self._load_target_metadata(base_path, target_name)
                json_mapping_path = metadata_file_path.replace(".hdr", ".json")
                mapping = self._load_json(json_mapping_path)
                metadata_dict[target_name] = {"data": metadata, "mapping": mapping}

            # apply wavelength_override if present
            if self.wavelength_override is not None:
                wavelengths = self.wavelength_override
            else:
                wavelengths = envi_reader.get_wavelengths()

            # Create HappyData object for this region
            happy_data = HappyData(sample_id, region_name, hyperspec_data, hyperspec_metadata, metadata_dict, wavelengths)

            return happy_data
        else:
            raise ValueError(f"Hyperspectral ENVI file not found for sample_id: {sample_id}")

    def _load_target_metadata(self, base_dir: str, target: str) -> np.ndarray:
        filename = os.path.join(base_dir, f'{target}' + ".hdr")
        header = envi.read_envi_header(filename)
        data_type = header['data type']  
        open = envi.open(filename)
        data = open.load()
        return np.asarray(data, dtype=ENVI_DTYPE_TO_NUMPY[int(data_type)])
        
    def _load_json(self, json_mapping_path) -> Dict:
        if os.path.exists(json_mapping_path):
            with open(json_mapping_path, 'r') as f:
                return json.load(f)
        else:
            return {}

    def _get_metadata_file_paths(self, base_path: str) -> List[str]:
        metadata_file_paths = []
        
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".hdr"):
                    if self.restrict_metadata is None or os.path.splitext(file)[0] in self.restrict_metadata:
                        metadata_file_paths.append(os.path.join(root, file))
        
        return metadata_file_paths

    def _get_regions(self, sample_id: str) -> List[str]:
        sample_dir = os.path.join(self.base_dir, sample_id)
        if os.path.isdir(sample_dir):
            region_dirs = [name for name in os.listdir(sample_dir) if os.path.isdir(os.path.join(sample_dir, name))]
        else:
            region_dirs = []
        return region_dirs
