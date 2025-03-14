import os

import numpy as np
import scipy.io as sio

from happy.data import HappyData
from ._happydata_writer import HappyDataWriterWithOutputPattern, PH_BASEDIR, PH_SAMPLEID, PH_REPEAT
from seppl.placeholders import expand_placeholders


class MatlabWriter(HappyDataWriterWithOutputPattern):

    def name(self) -> str:
        return "matlab-writer"

    def description(self) -> str:
        return "Writes data in HAPPy's Matlab format. "\
               "'normcube': spectral data, 'lambda': wave numbers, "\
               "'FinalMask': the pixel annotation mask, "\
               "'FinalMaskLabels': the mask pixel index -> label relation table"

    def _get_default_output(self):
        return PH_BASEDIR + "/" + PH_SAMPLEID + "." + PH_REPEAT + ".mat"

    def _write_item(self, happy_data, datatype_mapping=None):
        sample_id = happy_data.sample_id
        region_id = happy_data.region_id
        base_dir = expand_placeholders(self.base_dir)
        if not os.path.exists(base_dir):
            self.logger().info("Creating dir: %s" % base_dir)
            os.makedirs(base_dir, exist_ok=True)
        filepath = self._expand_output(self._output, sample_id, region_id)
        self.logger().info("Writing: %s" % filepath)
        save_dic = dict()
        save_dic["normcube"] = happy_data.data
        if happy_data.wavenumbers is not None:
            save_dic["lambda"] = happy_data.wavenumbers
        if "mask" in happy_data.metadata_dict:
            save_dic["FinalMask"] = np.squeeze(happy_data.metadata_dict["mask"]["data"])
            # store label mapping: pixel index -> label
            if "mapping" in happy_data.metadata_dict["mask"]:
                mapping_list = []
                for k in happy_data.metadata_dict["mask"]["mapping"]:
                    mapping_list.append([k, happy_data.metadata_dict["mask"]["mapping"][k]])
                save_dic["FinalMaskLabels"] = mapping_list
        sio.savemat(filepath, save_dic)

    def _write_data(self, happy_data_or_list, datatype_mapping=None):
        if isinstance(happy_data_or_list, list):
            for happy_data in happy_data_or_list:
                self._write_data(happy_data, datatype_mapping=datatype_mapping)
        elif isinstance(happy_data_or_list, HappyData):
            self._write_item(happy_data_or_list)

