import argparse
import logging
import pathlib
import re

from outtu import *
from parser import parse
from util_functions import get_float, get_month

logger = logging.getLogger(__name__)
args = argparse.ArgumentParser("Get all information from sallery pdfs")
args.add_argument("-i", "--input", help="The root directory of the pdfs", type=str, default=".")
args.add_argument("-o", "--output", help="The output file", type=str, default="output")
args.add_argument("-f", "--output_format",
                  nargs=1, choices=out_functions, action=SelectOutAction,
                  help="The output format")
args.add_argument("-s", "--simple", help="Only output the stocks", action="store_true")
args.add_argument("-v", "--verbose", help="Verbose output", choices=["info", "INFO", "WARNING", "ERROR", "CRITICAL"],
                  default="ERROR")
args.add_argument("-n", "--number_format", help="The number format", choices=["dk", "en"], default="dk")
argz = args.parse_args()

log = logging.getLogger()
logging.getLogger()
log.setLevel(argz.verbose)
# create a console handler
ch = logging.StreamHandler()
ch.setLevel(argz.verbose)
# create a formatter
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(ch)


def yoink_all_pdfs(root_dir: pathlib.Path) -> dict:
    logger.info("Yoinking all pdfs from %s", root_dir)
    regex = r"Lønseddel - loenseddel([a-z]+)(\d{4}).*.PDF"
    res: dict = {}
    for pdf in root_dir.glob("*"):
        if not pdf.name.lower().endswith("pdf"):
            logger.info("Skipping %s, as not pdf", pdf.name)
            continue
        try:
            logger.info("Parsing %s", pdf.name)
            parsed = parse(pdf)
        except Exception as e:
            raise Exception("{} {}".format(pdf.name, e))
        logger.info("Parsed %s", pdf.name)
        matches = re.search(regex, pdf.name)
        if not matches:
            logger.info("Please do not change the name of the pdf files.")
            logger.info("I've found the following file: {}".format(pdf.name))
            month = input("What is the month of this file? (YYYY-MM) ex: 2019-01: ")
        else:
            month = matches.group(2) + "-" + str(get_month(matches.group(1))).zfill(2)
            logger.info("Found month: {}".format(month))
        res[month] = {}
        emp = sum(
            [get_float(parsed["Antal"][i]) for i, x in enumerate(parsed["Art"]) if
             x == "5092"])
        addit = -1 * sum(get_float(parsed["Beløb"][i]) for i, x in
                         enumerate(parsed["Art"]) if x == "9221")
        logger.info(
            "Finished calculating stocks for emp and addit: Employer matched (up to 2.5% of salary): [{}], additional stocks: [{}]".format(
                emp, addit))

        if not argz.simple:
            logger.info("Adding everything to result")
            for i, x in enumerate(parsed["Art"]):
                s = parsed["Specifikation"][i] if parsed["Specifikation"][i] else ""
                b = get_float(parsed["Beløb"][i]) if parsed["Beløb"][i] else None
                a = get_float(parsed["Antal"][i]) if parsed["Antal"][i] else None
                sa = get_float(parsed["Sats"][i]) if parsed["Sats"][i] else None

                res[month][x] = {"Specifikation": s, "Beløb": b, "Antal": a, "Sats": sa}
        logger.info("Adding stocks to result")
        res[month]["Employers_Matched_Contribution"] = emp
        res[month]["Additional_contribution"] = addit
        res[month]["Stocks_total"] = emp + addit
    return res


def main():
    root_dir = pathlib.Path(argz.input)
    if not root_dir.exists():
        raise Exception("The root directory does not exist")
    res = yoink_all_pdfs(root_dir)
    logger.info("Finished yoinking all pdfs")

    if argz.output:
        logger.info("Writing to file: %s", argz.output)
        # use format located in argz.output_format
        if argz.output_format is not None:
            for out in argz.output_format:
                outname = argz.output
                if pathlib.Path(argz.output).suffix == "":
                    outname = argz.output + "." + out._get_name()
                out(argz.number_format).save(res, outname)


if __name__ == '__main__':
    main()
