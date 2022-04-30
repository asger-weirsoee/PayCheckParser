import logging
import pathlib
import re

import camelot

import kodekatalog
from util_functions import get_float

logger = logging.getLogger(__name__)


def special_cases_for_beloeb(code: str, index: int, columns: dict) -> (bool, bool):
    """
    Shitty generated tables, require shitty special cases.
    Sometimes we don't really know if we should insert an empty value or not
    Thus we have an "uncertain bool" that can be set
    and then later remove the value if it was not correct to remove it (by comparing the size to the size of art)

    :param code: our current art number
    :param index: the current index number
    :param columns: all of the colums
    :return: (bool, bool) first bool "insert empty" second bool "uncertain value"
     this should be handled manually in the code
    """
    regex = r".*Skat af (.*)"

    if code == "8906":
        logger.info("Try'n see if special case for 8906 is applicable")
        # The pay can have zero in beløb if there is no income
        matches = re.search(regex, columns["Specifikation"][index])
        if matches:
            # Sometimes the table generates weirdly and Fradrag is actually AFTER Skat af.
            # To combat this (I've only seen it once) so to combat this we are just checking if that is the case
            fml = matches.group(1)
            reee = r"(.*) Fradrag:.*"
            if 'Fradrag' in fml:
                fml = re.sub(reee, r"\1", fml, 0)

            if get_float(fml) == 0.0:
                logger.info("Special case for 8906 is applicable, but uncertain")
                return True, True
        else:
            # I hope that this does not happen. It can be literally cancer to info
            raise Exception(
                "There is trouble with the match this might be because the index of kodekataloget is not correct. I "
                "tried to look into [{}]".format(
                    columns["Specifikation"][index]))

    if code == "9993":
        logger.info("Try'n see if special case for 9993 is applicable")
        # Overført til konto can have nothing in beløb if there is an amount that has not been payed yet
        # But sometimes it is okay
        if "9990" in columns.get("Art"):
            logger.info("Special case for 9993 is applicable, but uncertain")
            return True, True
    return False, False


def parse(file: pathlib.Path) -> dict:
    """
    Parse the file and return a list of dictionaries
    :param file: file location
    :return: dictionary with article numbers and there corresponding amounts
    """
    # Open PDF file and extract tables
    tables = camelot.read_pdf(file.absolute().__str__())
    columns = {
        "Art": [],
        "Specifikation": [],
        "Antal": [],
        "Sats": [],
        "Beløb": []
    }
    # There is 2 tables. But we are only interested in the first one
    table = tables[0].df

    [columns["Art"].append(x) for x in table[0][1].split("\n")]
    [columns["Specifikation"].append(x.strip()) for x in table[1][1].split("\n") if
     x.strip() != "" and x.strip() != "-"]
    [columns["Antal"].append(x) for x in table[2][1].split("\n")]
    [columns["Sats"].append(x) for x in table[3][1].split("\n")]
    [columns["Beløb"].append(x) for x in table[4][1].split("\n")]
    perhaps = -1

    logger.info("Parsing table with {} rows".format(len(columns["Art"])))

    # There is always an Art, or article number for each value. So we'll use this as the base for the rest of the values
    for i, code in enumerate(columns["Art"]):

        # There is the possiblity for 10.000 different codes (probably they can just add more if needed)
        # I have not covered all of them.
        # If this exception happens. Then you need to check the code in kodekataloget and add the code if needed
        if code not in kodekatalog.kode:
            raise Exception("Kode {} ikke fundet i kodekatalog.".format(code))

        ko = kodekatalog.kode[code]
        # The following code is made to "equalize" the columns.
        # There needs to be an empty value in the rest of the columns for each value
        # when that is specified in the kodekatalog
        # Sometimes there are exceptions to this and that is handled manually in the code.

        # Some of the rows have "extra" information. This is seens as a \n in the field.
        # Thus we need to handle this case, and this is done by joining specified on the spec_amount
        # ex. Orlov u/løn og feriedage looks like
        # Orlov u/løn og feriedage      06/04-2020     06/04-2020
        # When we split by \n, then that is seen as 3 rows.
        # This is cobatted manually in the kodekatalog by specifying that its length is 3
        if ko.get("spec_amount") > 1:
            logger.info("Joining {} rows for {}".format(ko.get("spec_amount"), code))
            # Join the rows that is in spec_amount for specification
            # Firstly we create a temporary object ss by joining the elements on a space
            # Between our current index and + the spec_amount
            ss = " ".join(columns["Specifikation"][i:i + ko["spec_amount"]])
            # Then we delete the elements in the list
            del columns["Specifikation"][i:i + ko["spec_amount"]]
            # And we add the joined string to the list on the index
            columns["Specifikation"].insert(i, ss)

        if not ko.get("hasAntal"):
            logger.info("Inserting blank value for antal with code {}".format(code))
            # Add a blank value for the i into the exsisting list
            columns["Antal"].insert(i, "")

        if not ko.get("hasSats") or (code == "8721" and columns["Art"][:i + 1].count("8721") > 1) \
                or (code == "8720" and columns["Art"][:i + 1].count("8720") > 1):
            logger.info("Inserting blank value for sats with code {}".format(code))
            # Add a blank value for the i into the exsisting list
            columns["Sats"].insert(i, "")
        special_cases, pp = special_cases_for_beloeb(code, i, columns)
        if not ko.get("hasBeløb") or special_cases:
            logger.info("Inserting blank value for beløb with code {}".format(code))
            if pp:
                perhaps = i
            # Add a blank value for the i into the exsisting list
            columns["Beløb"].insert(i, "")
        # If not all all objects of the columns are the same length something went wrong

    if len(columns["Art"]) != len(columns["Specifikation"]):
        raise Exception(
            "Art [{}] og Specifikation [{}] ikke ens".format(len(columns["Art"]),
                                                             len(columns["Specifikation"])))
    if len(columns["Art"]) != len(columns["Antal"]):
        raise Exception("Art [{}] og Antal [{}] ikke ens".format(len(columns["Art"]),
                                                                 len(columns["Antal"])))
    if len(columns["Art"]) != len(columns["Sats"]):
        raise Exception("Art [{}] og Sats [{}] ikke ens".format(len(columns["Art"]),
                                                                len(columns["Sats"])))
    if len(columns["Art"]) != len(columns["Beløb"]):
        logger.info("Different length for Art [{}] og Beløb [{}]".format(len(columns["Art"]),
                                                                         len(columns["Beløb"])))
        if perhaps != 0:
            logger.info("There is a chance that the difference in sizes in beløb and art is due to a "
                        "missing bad table generation. So we'll try'n remove it again, and see if "
                        "that helps")
            del columns["Beløb"][perhaps]
            if len(columns["Art"]) != len(columns["Beløb"]):
                raise Exception(
                    "Art [{}] og Beløb [{}] ikke ens".format(len(columns["Art"]),
                                                             len(columns["Beløb"])))
            logger.info("It helped.")
        else:
            raise Exception("Art [{}] og Beløb [{}] ikke ens".format(len(columns["Art"]),
                                                                     len(columns["Beløb"])))

    return columns
