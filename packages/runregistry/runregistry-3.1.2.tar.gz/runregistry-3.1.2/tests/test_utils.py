import sys

import pytest
import requests

from runregistry.attributes import (
    dataset_attributes,
    run_oms_attributes,
    run_triplet_attributes,
)
from runregistry.runregistry import (
    __parse_runs_arg as _parse_runs_arg,
)
from runregistry.runregistry import (
    __version__,
    _get_headers,
    _get_target,
    _get_token,
    _get_user_agent,
    setup,
)
from runregistry.utils import (
    dataset_triplet_attributes,
    run_rr_attributes,
    transform_to_rr_dataset_filter,
    transform_to_rr_run_filter,
)


class TestRunRegistryFilterCreation:
    def test_get_run(self):
        run_number = 323434
        assert transform_to_rr_run_filter(run_filter={"run_number": run_number}) == {"run_number": {"=": run_number}}

    def test_transform_triplets(self):
        valid_values = ["GOOD", "BAD", "STANDBY", "EXCLUDED", "NOTSET", "EMPTY"]
        for attribute in run_triplet_attributes:
            for value in valid_values:
                result = transform_to_rr_run_filter(run_filter={attribute: {"=": value}})
                assert f"triplet_summary.{attribute}.{value}" in result
        with pytest.raises(Exception):  # noqa: B017
            transform_to_rr_run_filter(run_filter={"ecal-ecal": {"=": "HEHEHE"}})

    def test_transform_invalid_attribute(self):
        with pytest.raises(Exception):  # noqa: B017
            transform_to_rr_run_filter(run_filter={"BRE KAKOS MPELAS": {"=": "HEHEHE"}})
        assert not transform_to_rr_run_filter(None)
        assert not transform_to_rr_run_filter("")
        assert not transform_to_rr_run_filter("SDF")
        assert not transform_to_rr_run_filter(15)

    def test_transform_attributes(self):
        valid_attributes = [
            "rr_attributes",
            "oms_attributes",
            "triplet_summary",
            "triplet_summaryalksjdflkajsd",  # Unsure why this should be supported
        ]
        filter_ = {"=": "aaa"}
        for attribute in valid_attributes:
            result = transform_to_rr_run_filter(run_filter={attribute: filter_})
            assert attribute in result and result[attribute] == filter_

    def test_transform_run_oms_attributes(self):
        filter_ = {"=": "test"}
        for attribute in run_oms_attributes:
            if attribute == "run_number":
                print(
                    "run_number seems to exist on both run_oms_attributes and "
                    + "run_triplet_attributes, meaning that run_number cannot "
                    + "be used with run_oms_attributes, only triplets"
                )
                continue
            result = transform_to_rr_run_filter(run_filter={attribute: filter_})
            assert f"oms_attributes.{attribute}" in result and result[f"oms_attributes.{attribute}"] == filter_

    def test_transform_run_rr_attributes(self):
        filter_ = {"=": "test"}
        for attribute in run_rr_attributes:
            result = transform_to_rr_run_filter(run_filter={attribute: filter_})
            assert f"rr_attributes.{attribute}" in result and result[f"rr_attributes.{attribute}"] == filter_

    def test_get_multiple_run_using_or(self):
        run_number1 = 323555
        run_number2 = 323444
        run_number3 = 343222
        run_number4 = 333333
        user_input = {"run_number": {"or": [run_number1, run_number2, run_number3, {"=": run_number4}]}}
        desired_output = {
            "run_number": {
                "or": [
                    {"=": run_number1},
                    {"=": run_number2},
                    {"=": run_number3},
                    {"=": run_number4},
                ]
            }
        }

        assert transform_to_rr_run_filter(run_filter=user_input) == desired_output


class TestDatasetFilterCreation:
    def test_dataset_attributes(self):
        filter_ = {"=": "aaa"}
        for attribute in dataset_attributes:
            result = transform_to_rr_dataset_filter(dataset_filter={attribute: filter_})
            assert f"dataset_attributes.{attribute}" in result and result[f"dataset_attributes.{attribute}"] == filter_

    def test_dataset_triplet_attributes_valid(self):
        valid_values = ["GOOD", "BAD", "STANDBY", "EXCLUDED", "NOTSET", "EMPTY"]
        for value in valid_values:
            for attribute in dataset_triplet_attributes:
                result = transform_to_rr_dataset_filter(dataset_filter={attribute: {"=": value}})
                assert f"triplet_summary.{attribute}.{value}" in result

    def test_dataset_triplet_attributes_invalid(self):
        with pytest.raises(Exception):  # noqa: B017
            transform_to_rr_dataset_filter(dataset_filter={dataset_triplet_attributes[0]: {"=": "ZE MALESI :("}})

    def test_transform_run_oms_attributes(self):
        filter_ = {"=": "test"}
        for attribute in run_oms_attributes:
            if attribute == "run_number":
                print(
                    "run_number seems to exist on both run_oms_attributes and "
                    + "run_triplet_attributes, meaning that run_number cannot "
                    + "be used with run_oms_attributes, only triplets"
                )
                continue
            result = transform_to_rr_dataset_filter(dataset_filter={attribute: filter_})
            assert f"oms_attributes.{attribute}" in result and result[f"oms_attributes.{attribute}"] == filter_

    def test_transform_run_rr_attributes(self):
        filter_ = {"=": "test"}
        for attribute in run_rr_attributes:
            result = transform_to_rr_dataset_filter(dataset_filter={attribute: filter_})
            assert f"rr_attributes.{attribute}" in result and result[f"rr_attributes.{attribute}"] == filter_

    def test_transform_invalid_attribute(self):
        with pytest.raises(Exception):  # noqa: B017
            transform_to_rr_dataset_filter(dataset_filter={"BRE KAKOS MPELAS": {"=": "HEHEHE"}})
        assert not transform_to_rr_dataset_filter(None)
        assert not transform_to_rr_dataset_filter("")
        assert not transform_to_rr_dataset_filter("SDF")
        assert not transform_to_rr_dataset_filter(15)


class TestUtils:
    MAGIC_RUN = 255525

    def test_user_agent(self):
        ua = _get_user_agent()
        assert (
            __version__ in ua
            and "runregistry_api_client" in ua
            and f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}" in ua
            and requests.__version__ in ua
            and "zodiac sign" not in ua
        )

    def test_runregistry_setup(self):
        for target in ["development", "local", "production"]:
            setup(target)

            assert _get_target() == target

        with pytest.raises(Exception):  # noqa: B017
            setup("HAHAHAHA >:)")

    def test_headers(self):
        headers = _get_headers(token="WHATEVER :/")
        assert all([key in headers for key in ["User-Agent", "Authorization", "Content-type"]])

    def test_get_token(self):
        setup("local")
        assert _get_token() == ""

    def test_parse_runs_int(self):
        runs = _parse_runs_arg(self.MAGIC_RUN)
        assert isinstance(runs, list) and runs[0] == self.MAGIC_RUN

    def test_parse_runs_str_int(self):
        runs = _parse_runs_arg(str(self.MAGIC_RUN))
        assert isinstance(runs, list) and runs[0] == self.MAGIC_RUN

    def test_parse_runs_str_str(self):
        runs = _parse_runs_arg("LMAO ://////////")
        assert isinstance(runs, list) and len(runs) == 0

    def test_parse_runs_list_int(self):
        runs = _parse_runs_arg([self.MAGIC_RUN, self.MAGIC_RUN + 1])
        assert isinstance(runs, list) and len(runs) == 2

    def test_parse_runs_list_str(self):
        # This case should probably be fixed to only accept list of ints
        runs = _parse_runs_arg([str(self.MAGIC_RUN), str(self.MAGIC_RUN + 1)])
        assert isinstance(runs, list) and len(runs) == 2

    def test_parse_runs_dict(self):
        runs = _parse_runs_arg({self.MAGIC_RUN})
        assert isinstance(runs, list) and len(runs) == 0
