from abc import ABC
from argparse import Action
from collections import OrderedDict


class OutFunctionsBase(ABC):
    name = None

    def __init__(self, number_format):
        self.name = self._get_name()
        self.number_format = number_format

    def save(self, data: OrderedDict, filename: str):
        raise NotImplemented("This needs to be implemented.")

    def __str__(self):
        return self._get_name()

    @staticmethod
    def _get_name():
        raise NotImplemented("This needs to be implemented.")


# Sort yyyy-mm formatted dates, where it is split up into yyyy and mm. The
# oldest should be first.


class CSV(OutFunctionsBase):
    headers = [
        "yyyy-mm",
        "Employers_Matched_Contribution",
        "Additional_contribution",
        "Stocks_total"
    ]

    def save(self, data: OrderedDict, filename: str):
        import csv
        with open(filename, 'w', newline='') as csvfile:
            dict_writer = csv.DictWriter(csvfile, fieldnames=self.headers)
            dict_writer.writeheader()

            for key, values in data.items():
                if key == "key":
                    continue
                dict_writer.writerow({
                    "yyyy-mm": key,
                    "Employers_Matched_Contribution": values[
                        "Employers_Matched_Contribution"] if self.number_format == "en" else str(
                        values["Employers_Matched_Contribution"]).replace(".", ","),
                    "Additional_contribution": values["Additional_contribution"] if self.number_format == "en" else str(
                        values["Additional_contribution"]).replace(".", ","),
                    "Stocks_total": values["Stocks_total"] if self.number_format == "en" else str(
                        values["Stocks_total"]).replace(".", ",")
                })

    @staticmethod
    def _get_name():
        return "CSV"


class JSON(OutFunctionsBase):
    def save(self, data: OrderedDict, filename: str):
        import json
        with open(filename, 'w') as f:
            json.dump(data, f)

    @staticmethod
    def _get_name():
        return "JSON"


class XML(OutFunctionsBase):
    def save(self, data: OrderedDict, filename: str):
        import xml.etree.ElementTree as ET
        raise NotImplemented("This needs to be implemented.")

    @staticmethod
    def _get_name():
        return "XML"


class YAML(OutFunctionsBase):
    def save(self, data: OrderedDict, filename):
        import yaml
        with open(filename, 'w') as f:
            yaml.dump(data, f)

    @staticmethod
    def _get_name():
        return "YAML"


class Pickle(OutFunctionsBase):
    def save(self, data: OrderedDict, filename):
        import pickle
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    @staticmethod
    def _get_name():
        return "Pickle"


class SelectOutAction(Action):
    """
        Argparse action for handeling a list of classes with OutFunctionsBase type.
    """

    def __init__(self, **kwargs):
        choices: [OutFunctionsBase] = kwargs.pop("choices", None)
        choices: list
        # Ensure an Enum subclass is provided
        if choices is None:
            raise ValueError("choices must have something in it")
        if len([x for x in choices if not issubclass(x, OutFunctionsBase)]) > 0:
            raise ValueError("Not all choices are of type Feature")
        kwargs.setdefault("choices", tuple(e._get_name() for e in choices))

        super(SelectOutAction, self).__init__(**kwargs)
        self._choices = choices

    def __call__(self, parser, namespace, values, option_string=None):
        chosen = [x for x in self._choices if x._get_name() in values]
        setattr(namespace, self.dest, chosen)


out_functions: [OutFunctionsBase] = [CSV, JSON, XML, YAML, Pickle]
