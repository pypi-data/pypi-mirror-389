#!/usr/bin/env python
# coding: UTF-8

import os
from pathlib import Path
import re
from typing import Optional, Sequence, cast

import pydicom
from pydicom.encaps import generate_frames

from .utils import read_json, write_json, write_binary
from . import multipart_related


class StaticDICOMWebCreator:
    def __init__(self, output_path: str | Path,
                 root_uri="/",
                 bulkdata_dirname="bulkdata",
                 bulkdata_threshold=1024 * 50,  # 50KB
                 write_bulkdata_pixeldata=False,
                 included_fields_for_study: Sequence[str] = [],
                 included_fields_for_series: Sequence[str] = [],
                 write_json_fmt=True,
                 write_gzip_fmt=False,
                 write_sorted_json_keys=True,
                 verbose=False
                 ):
        self.output_path = Path(output_path)
        self.root_uri = str(root_uri)
        self.bulk_data_dirname = str(bulkdata_dirname)
        self.bulk_data_threshold = int(bulkdata_threshold)
        self.write_bulkdata_pixeldata = write_bulkdata_pixeldata
        self.write_json_fmt = write_json_fmt
        self.write_gzip_fmt = write_gzip_fmt
        self.write_sorted_json_keys = write_sorted_json_keys
        self.verbose = verbose

        self.included_fields_for_study = list(included_fields_for_study)
        self.included_fields_for_series = list(included_fields_for_series)

        self.tags_study_level_mandatory = [
            "StudyDate",
            "StudyTime",
            "AccessionNumber",
            "InstanceAvailability",
            # "ModalitiesInStudy",
            "ReferringPhysicianName",
            "PatientName",
            "PatientID",
            "PatientBirthDate",
            "PatientSex",
            "StudyInstanceUID",
            "StudyID",
            # "NumberOfStudyRelatedSeries",
            # "NumberOfStudyRelatedInstances",
        ]
        self.tags_study_level_optional = [
            "SpecificCharacterSet",
            "TimezoneOffsetFromUTC",
        ]

        self.tags_series_level_mandatory = [
            "Modality",
            "SeriesInstanceUID",
            "SeriesNumber",
            "NumberOfSeriesRelatedInstances",
        ]
        self.tags_series_level_optional = [
            "SpecificCharacterSet",
            "TimezoneOffsetFromUTC",
            "SeriesDescription",
            "PerformedProcedureStepStartDate",
            "PerformedProcedureStepStartTime",
            "RequestAttributeSequence",
        ]

    def add_dcm_instance(self, dcm: pydicom.Dataset):
        assert isinstance(dcm, pydicom.Dataset), f"Expected pydicom.Dataset, got {type(dcm)}"
        # Process pixel data frames
        if 'PixelData' in dcm:
            self.write_pixel_frames(dcm)

        # Process the header and bulkdata elements
        json_dict, bulkdata_elem_list = self.dcm_to_json_dict(dcm)

        # Write bulk data
        for elem in bulkdata_elem_list:
            # In case of pixel data
            if elem.tag == 0x7FE00010 and not self.write_bulkdata_pixeldata:
                del json_dict["7FE00010"]
            else:
                json_dict[f"{elem.tag:08X}"] = self.write_bulkdata_element(dcm, elem)

        # Write metadata
        instance_metadata_path = self.build_path_instance_metadata(dcm)
        self.write_json(instance_metadata_path, json_dict)

    def write_pixel_frames(self, dcm: pydicom.Dataset):
        number_of_frames = dcm.get('NumberOfFrames', 1)
        transfer_syntax_uid = str(dcm.file_meta.TransferSyntaxUID)

        for i, frame in enumerate(generate_frames(dcm.PixelData)):
            frame_path = self.build_path_instance_frame(dcm, i + 1)

            if self.verbose:
                print(f"Writing frame {i + 1}/{number_of_frames} to {frame_path}")

            self.write_binary(frame_path, frame, transfer_syntax_uid)

    def write_bulkdata_element(self, dcm: pydicom.Dataset, elem: pydicom.DataElement):
        bulkdata_path = self.build_path_instance_bulk(dcm, elem)
        bulk_data = elem.value

        if self.verbose:
            print(f"Writing bulk data for element {elem.tag} to {bulkdata_path}")

        self.write_binary(bulkdata_path, bulk_data)

        bulkdata_uri = self.build_uri_instance_bulk(dcm, elem)
        return {
            "vr": "OB",
            "BulkDataURI": bulkdata_uri
        }

    def create_json(self, create_studies_json_for_study_iter: bool = False,
                    create_studies_json_for_series_iter: bool = False):
        for study_dir_path in self.list_study_dirs():
            if self.verbose:
                print("Study:", study_dir_path)

            for series_dir_path in self.list_series_dirs(study_dir_path):
                if self.verbose:
                    print("  Series:", series_dir_path)

                self.create_series_json(series_dir_path)
                self.create_series_metadata_json(series_dir_path)

                if create_studies_json_for_series_iter:
                    self.create_all_series_json(study_dir_path)
                    self.create_study_json(study_dir_path)
                    self.create_all_studies_json()

            self.create_all_series_json(study_dir_path)
            self.create_study_json(study_dir_path)

            if create_studies_json_for_study_iter:
                self.create_all_studies_json()

        self.create_all_studies_json()

    def create_series_metadata_json(self, series_dir_path: str | Path):
        """Includes metadata of all instances
        """
        series_dir_path = Path(series_dir_path)

        series_metadata_list: list[dict] = []
        for instance_metadata_dir_path in self.list_instance_metadata_dirs(series_dir_path):
            json_dict = self.read_json(instance_metadata_dir_path / "index.json")
            json_dict = cast(dict, json_dict)
            series_metadata_list.append(json_dict)

        if len(series_metadata_list) > 0:
            dcm = pydicom.Dataset.from_json(series_metadata_list[0])
            series_metadata_path = self.build_path_series_metadata_json(dcm)
            self.write_json(series_metadata_path, series_metadata_list)

    def create_series_json(self, series_dir_path: str | Path):
        '''
        # References

        - https://dicom.nema.org/dicom/2013/output/chtml/part18/sect_6.7.html#sect_6.7.1.2.2.2
        '''
        series_dir_path = Path(series_dir_path)

        # List instance metadata dirs
        instance_metadata_dir_path_list = self.list_instance_metadata_dirs(series_dir_path)

        # If no instance metadata, return
        if len(instance_metadata_dir_path_list) == 0:
            return

        # Read first instance metadata
        json_dict = self.read_json(instance_metadata_dir_path_list[0] / "index.json")
        json_dict = cast(dict, json_dict)
        dcm_instance = pydicom.Dataset.from_json(json_dict)

        # Set values for dicomweb standard tags
        dcm = pydicom.Dataset()
        for tag_keyword in self.tags_series_level_mandatory:
            setattr(dcm, tag_keyword, dcm_instance.get(tag_keyword, ""))

        tags_optional = self.tags_series_level_optional + self.included_fields_for_series
        for tag_keyword in tags_optional:
            if hasattr(dcm_instance, tag_keyword):
                setattr(dcm, tag_keyword, dcm_instance.get(tag_keyword, ""))

        dcm.NumberOfSeriesRelatedInstances = len(instance_metadata_dir_path_list)

        # Write series JSON
        series_json_path = series_dir_path / "index.json"
        self.write_json(series_json_path, dcm.to_json_dict())

    def create_all_series_json(self, study_dir_path: str | Path):
        '''
        Gather series-level metadata for all series in the study.
        '''
        study_dir_path = Path(study_dir_path)

        all_series_json_dict_list = []

        for series_dir_path in self.list_series_dirs(study_dir_path):
            series_json_path = series_dir_path / "index.json"

            if not series_json_path.is_file() and not series_json_path.with_suffix(".gz").is_file():
                continue

            series_json_dict = self.read_json(series_json_path)
            series_json_dict = cast(dict, series_json_dict)
            all_series_json_dict_list.append(series_json_dict)

        if len(all_series_json_dict_list) == 0:
            return

        dcm = pydicom.Dataset()
        dcm.StudyInstanceUID = study_dir_path.name
        all_series_json_path = self.build_path_all_series_json(dcm)
        self.write_json(all_series_json_path, all_series_json_dict_list)

    def create_study_json(self, study_dir_path: str | Path):
        '''
        Create study-level metadata JSON for a single study.
        '''
        study_dir_path = Path(study_dir_path)

        # Take one instance for making template
        dcm_template = self.take_an_instance_from_study(study_dir_path)
        if dcm_template is None:
            return

        dcm = pydicom.Dataset()

        # Set values for dicomweb standard tags
        for tag_keyword in self.tags_study_level_mandatory:
            setattr(dcm, tag_keyword, dcm_template.get(tag_keyword, ""))

        for tag_keyword in self.tags_study_level_optional:
            if hasattr(dcm_template, tag_keyword):
                setattr(dcm, tag_keyword, dcm_template.get(tag_keyword, ""))

        # Set some complicated values
        modalities_in_study = set()
        number_of_study_related_series = 0
        number_of_study_related_instances = 0

        dcm_tmp = pydicom.Dataset()
        dcm_tmp.StudyInstanceUID = study_dir_path.name
        all_series_json_path = self.build_path_all_series_json(dcm_tmp)
        all_series_json = self.read_json(all_series_json_path)

        if all_series_json is None:
            return

        for series_json_dict in cast(list, all_series_json):
            dcm_se = pydicom.Dataset.from_json(series_json_dict)
            modalities_in_study.add(dcm_se.Modality)
            number_of_study_related_series += 1
            number_of_study_related_instances += dcm_se.get("NumberOfSeriesRelatedInstances", 0)

        dcm.ModalitiesInStudy = list(modalities_in_study)
        dcm.NumberOfStudyRelatedSeries = number_of_study_related_series
        dcm.NumberOfStudyRelatedInstances = number_of_study_related_instances

        # Write study JSON
        study_json_path = study_dir_path / "index.json"
        self.write_json(study_json_path, dcm.to_json_dict())

    def create_all_studies_json(self):
        '''Gather study-level metadata for all studies.'''
        all_studies_json_dict_list = []

        for study_dir_path in self.list_study_dirs():
            study_json_path = study_dir_path / "index.json"
            study_json = self.read_json(study_json_path)

            if study_json is None:
                continue

            all_studies_json_dict_list.append(study_json)

        all_studies_json_path = self.build_path_all_studies_json()
        self.write_json(all_studies_json_path, all_studies_json_dict_list)

    def dcm_to_json_dict(self, dcm: pydicom.Dataset) -> tuple[dict, list[pydicom.DataElement]]:
        bulkdata_list: list[pydicom.DataElement] = []

        def handler(elem: pydicom.DataElement) -> str:
            bulkdata_list.append(elem)
            return ""

        json_dict = dcm.to_json_dict(bulk_data_threshold=self.bulk_data_threshold,
                                     bulk_data_element_handler=handler)

        return json_dict, bulkdata_list

    def read_json(self, filepath: Path) -> list[dict] | dict | None:
        filepath_gz = Path(str(filepath) + ".gz")

        if filepath.is_file() and filepath.stat().st_size > 0:
            ret = read_json(filepath)
        elif filepath_gz.is_file():
            ret = read_json(filepath, is_gzip=True)
        else:
            ret = None

        return ret

    def write_json(self, path: Path, json_dict: list[dict] | dict):
        if self.write_sorted_json_keys:
            if isinstance(json_dict, dict):
                json_dict = dict(sorted(json_dict.items()))
            else:
                json_dict = [dict(sorted(item.items())) for item in json_dict]

        if self.write_json_fmt:
            write_json(path, json_dict, write_json_fmt=True, write_gzip_fmt=False)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

        if self.write_gzip_fmt:
            write_json(path, json_dict, write_json_fmt=False, write_gzip_fmt=True)

    def write_binary(self, path: Path, data: bytes, transfer_syntax_uid=""):
        data_to_write = bytes()
        data_to_write += multipart_related.create_part_header_for_multipart_related(transfer_syntax_uid).encode(encoding="ascii")
        data_to_write += data
        data_to_write += f"\r\n--{multipart_related.DEFAULT_BOUNDARY}".encode("ascii")

        write_binary(path, data_to_write)

    def is_dicom_uid_format(self, s: str) -> bool:
        return re.match(r"^[1-9]+(\.[0-9]+)*$", s) is not None

    def list_study_dirs(self) -> list[Path]:
        study_dir_path_list = []

        for dir_path in (self.output_path / "studies").glob("*"):
            if dir_path.is_dir() and self.is_dicom_uid_format(dir_path.name):
                study_dir_path_list.append(dir_path)

        return study_dir_path_list

    def list_series_dirs(self, study_dir_path: str | Path) -> list[Path]:
        study_dir_path = Path(study_dir_path)
        series_dir_path_list = []

        for dir_path in study_dir_path.glob("series/*"):
            if dir_path.is_dir() and self.is_dicom_uid_format(dir_path.name):
                series_dir_path_list.append(dir_path)

        return series_dir_path_list

    def list_instance_metadata_dirs(self, series_dir_path: str | Path) -> list[Path]:
        series_dir_path = Path(series_dir_path)
        instance_metadata_dir_path_list = []

        for dir_path in series_dir_path.glob("instances/*/metadata"):
            if dir_path.is_dir() and self.is_dicom_uid_format(dir_path.parent.name):
                instance_metadata_dir_path_list.append(dir_path)

        return instance_metadata_dir_path_list

    def take_an_instance_from_study(self, study_dir_path: str | Path) -> pydicom.Dataset | None:
        study_dir_path = Path(study_dir_path)

        for series_dir_path in self.list_series_dirs(study_dir_path):
            for instance_metadata_dir_path in self.list_instance_metadata_dirs(series_dir_path):
                json_dict = self.read_json(instance_metadata_dir_path / "index.json")
                json_dict = cast(dict, json_dict)
                dcm = pydicom.Dataset.from_json(json_dict)
                return dcm

        return None

    def build_path_study(self, dcm: pydicom.Dataset) -> Path:
        return self.output_path / "studies" / dcm.StudyInstanceUID

    def build_path_all_studies_json(self) -> Path:
        return self.output_path / "studies" / "index.json"

    def build_path_all_series_json(self, dcm: pydicom.Dataset) -> Path:
        return self.build_path_study(dcm) / "series" / "index.json"

    def build_path_series(self, dcm: pydicom.Dataset) -> Path:
        return self.build_path_study(dcm) / "series" / dcm.SeriesInstanceUID

    def build_path_series_json(self, dcm: pydicom.Dataset) -> Path:
        return self.build_path_series(dcm) / "index.json"

    def build_path_series_metadata_json(self, dcm: pydicom.Dataset) -> Path:
        return self.build_path_series(dcm) / "metadata" / "index.json"

    def build_path_instance(self, dcm: pydicom.Dataset) -> Path:
        return self.build_path_series(dcm) / "instances" / dcm.SOPInstanceUID

    def build_path_instance_metadata(self, dcm: pydicom.Dataset) -> Path:
        return self.build_path_instance(dcm) / "metadata" / "index.json"

    def build_path_instance_frame(self, dcm: pydicom.Dataset, frame_number: Optional[int] = None) -> Path:
        dir_path = self.build_path_instance(dcm) / "frames"
        if frame_number is None:
            frame_number = dcm.get('FrameNumber', 1)
        return dir_path / str(frame_number) / "index.bin"

    def build_uri_instance_frame(self, dcm: pydicom.Dataset, frame_number: Optional[int] = None) -> str:
        filepath = self.build_path_instance_frame(dcm, frame_number)
        uri = os.path.join(self.root_uri, filepath.relative_to(self.output_path))
        return uri

    def build_path_instance_bulk(self, dcm: pydicom.Dataset, elem: pydicom.DataElement) -> Path:
        return self.build_path_instance(dcm) / self.bulk_data_dirname / f"{int(elem.tag):08X}" / "index.bin"

    def build_uri_instance_bulk(self, dcm: pydicom.Dataset, elem: pydicom.DataElement) -> str:
        filepath = self.build_path_instance_bulk(dcm, elem)
        uri = os.path.join(self.root_uri, filepath.relative_to(self.output_path))
        return uri


class StaticDICOMWebCreatorForOHIFViewer(StaticDICOMWebCreator):
    def __init__(self, output_path: str | Path,
                 root_uri="/",
                 bulkdata_dirname="bulkdata",
                 bulkdata_threshold=1024 * 50,  # 50KB
                 write_bulkdata_pixeldata=False,
                 included_fields_for_study: Sequence[str] = [],
                 included_fields_for_series: Sequence[str] = [],
                 write_json_fmt=True,
                 write_gzip_fmt=True,
                 write_sorted_json_keys=True,
                 verbose=False
                 ):
        included_fields_for_series = [
            "SeriesDate",  # 0x00080021
            "SeriesTime",  # 0x00080031
            "SeriesDescription",  # 0x0008103E
        ]
        included_fields_for_study = [
            "StudyDescription",  # 0x00081030
        ]

        super().__init__(output_path,
                         root_uri,
                         bulkdata_dirname,
                         bulkdata_threshold,
                         write_bulkdata_pixeldata,
                         included_fields_for_study,
                         included_fields_for_series,
                         write_json_fmt,
                         write_gzip_fmt,
                         write_sorted_json_keys,
                         verbose)
