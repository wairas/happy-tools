from typing import List, Dict


def list_classes() -> Dict[str, List[str]]:
    return {
        "happy.data.black_ref._core.AbstractBlackReferenceMethod": [
            "happy.data.black_ref",
        ],
        "happy.data.white_ref._core.AbstractWhiteReferenceMethod": [
            "happy.data.white_ref",
        ],
        "happy.data.ref_locator._core.AbstractReferenceLocator": [
            "happy.data.ref_locator",
        ],
        "happy.data.normalization._core.AbstractNormalization": [
            "happy.data.normalization",
        ],
        "happy.readers._happydata_reader.HappyDataReader": [
            "happy.readers",
        ],
        "happy.preprocessors._preprocessor.Preprocessor": [
            "happy.preprocessors",
        ],
        "happy.writers._happydata_writer.HappyDataWriter": [
            "happy.writers",
        ],
        "happy.pixel_selectors._pixel_selector.PixelSelector": [
            "happy.pixel_selectors",
        ],
        "happy.region_extractors._region_extractor.RegionExtractor": [
            "happy.region_extractors",
        ],
    }
