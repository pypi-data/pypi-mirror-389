from modules import forms
from ptlibs import ptprinthelper
from ptlibs.ptprinthelper import get_colored_text

def print_result(list_of_results: list, args):
    """
    Prints or writes processed results in a structured format based on provided arguments.

    The function handles:
        - Conditional printing of logs (including errors)
        - Grouped or complete summary views
        - Filtering and formatting of different result types (internal URLs, metadata, forms, comments, Google keys, etc.)
        - Writing output to files, including separate files per data type if specified

    Parameters:
        list_of_results (list): A list of result objects, each containing 'data' and 'logs' attributes.
        args: An object (typically argparse.Namespace) containing configuration flags such as:
            - json (bool): Whether to suppress console output for JSON output.
            - grouping (bool): Whether to print results grouped by URL.
            - grouping_complete (bool): Whether to print a merged summary of all results.
            - output (str or None): Path to the output file.
            - output_parts (bool): Whether to write separate files for each data type.
            - file_handle: Internal handle for writing to files.

    Returns:
        None: Results are printed to the console or written to files based on arguments.
    """

    handlers = {
        "internal_urls_with_parameters": _print_parsed_urls,
        "metadata": _print_metadata,
        "forms": _print_forms,
        "comments": _print_comments,
        "google_keys": _print_google_keys,
    }

    if not len(list_of_results) > 1:
        for r in list_of_results:
            ptprinthelper.ptprint(" ", "TEXT", condition=not args.json)
            for log, msg_type in r.logs:
                ptprinthelper.ptprint(log, msg_type, condition=not args.json)
                if msg_type.upper() == "ERROR":
                    pass
    else:
        if args.grouping_complete:
            ptprinthelper.ptprint("\n", "TEXT", condition=not args.json)
            ptprinthelper.ptprint(get_colored_text(f"SUMMARY (UNIQUE VALUES)\n", color="TITLE") + f"{'='*len('Summary (unique values)')}", "TEXT", condition=not args.json, newline_above=True)

    list_of_results = [l.data for l in list_of_results]
    titles = [i for i in {k: v for k, v in list_of_results[0].items() if v is not None}.keys()]

    args.file_handle = None
    if args.output and not args.output_parts:
        args.file_handle = open(args.output, "w")

    for index, title in enumerate(titles):
        if title in ["url", "abs_urls"]:
            continue

        if args.output_parts:
            args.file_handle = _get_handle(title, args)

        if args.grouping_complete:
            merged_result = _get_data_type(title)

        _print_title(title, args, index)
        for index, result_dictionary in enumerate(list_of_results):

            if args.grouping:
                _print_current_url(list_of_results, index, args)

            if args.grouping_complete:
                merged_result = _fill_merged_result(merged_result, list_of_results, index, title)

            # if not grouping complete
            else:
                if title == "internal_urls_with_parameters":
                    _print_parsed_urls(list_of_results, index, args)
                elif title == "metadata":
                    _print_metadata(list_of_results, index, args)
                elif title == "forms":
                    _print_forms(list_of_results, index, args)
                elif title == "comments":
                    _print_comments(list_of_results, index, args)
                elif title == "google_keys":
                    _print_google_keys(list_of_results, index, args)
                elif result_dictionary.get(title):
                    ptprinthelper.ptprint("\n".join(result_dictionary[title]), filehandle=args.file_handle, condition=not args.json)
                else:
                    ptprinthelper.ptprint("Not found", "", filehandle=args.file_handle, condition=not args.json)
                _get_endl(list_of_results, index, args)

        if args.grouping_complete:
            # if -gc provided
            if title == "internal_urls_with_parameters":
                merged_result["internal_urls_with_parameters"] = sorted(merged_result["internal_urls_with_parameters"], key=lambda k: k['url'])
                _print_parsed_urls([merged_result], index=0, args=args)
            elif title == "metadata":
                _print_metadata([merged_result], index=0, args=args)
            elif title == "forms":
                _print_forms([merged_result], index=0, args=args)
            elif title == "comments":
                _print_comments([merged_result], index=0, args=args)
            elif title == "google_keys":
                _print_google_keys([merged_result], index=0, args=args)
            elif title == "regex":

                # ----
                if not merged_result["regex"].keys():
                    ptprinthelper.ptprint("Not found", "", filehandle=args.file_handle, condition=not args.json)
                for text, urls in merged_result["regex"].items():
                    if len(list_of_results) > 1 and args.very_verbose:
                        max_len = max(len(text) for text in merged_result["regex"].keys())
                        padding = " " if (max_len - len(text)) > 50 else " " * (max_len - len(text) +1)
                        ptprinthelper.ptprint(f"{text.strip()}{padding}", "", condition=not args.json, end="\n" if not args.very_verbose else "")
                        if args.very_verbose:
                            ptprinthelper.ptprint(ptprinthelper.get_colored_text(f"({', '.join(sorted(urls))})", color="ADDITIONS"), "", condition=not args.json)
                    else:
                        ptprinthelper.ptprint(f"{text}", "", condition=not args.json)

                # print dynamic title with unique urls
                if len(list_of_results) > 1:
                    ptprinthelper.ptprint(f"{ptprinthelper.get_colored_text('REGEX URLS', color="TITLE")}\n{'-'*len('REGEX URLS')}", "TEXT", condition=not args.json, newline_above=True)
                    _all_urls = set().union(*merged_result["regex"].values())
                    ptprinthelper.ptprint("\n".join(sorted(_all_urls)), "", condition=not args.json)
            elif merged_result:
                ptprinthelper.ptprint("\n".join(sorted(set(merged_result))), "", end=_check_if_next(list_of_results, index)+"\n", filehandle=args.file_handle, condition=not args.json)
            else:
                ptprinthelper.ptprint("Not found", "", filehandle=args.file_handle, condition=not args.json)

        if args.output_parts:
            args.file_handle.close()

    if args.file_handle:
        args.file_handle.close()


def _get_handle(title, args):
    parsed_file_name = args.output.rsplit(".", 1)
    file_extension = "." + parsed_file_name[-1] if len(parsed_file_name) > 1 else ""
    handle = open(f"{parsed_file_name[0]}_{title.upper()}{file_extension}", "w")
    return handle



def _print_google_keys(list_of_results, index, args):
    result_dict = list_of_results[index].get("google_keys")
    if result_dict:
        for key, value in result_dict.items():
            ptprinthelper.ptprint(f"{key}:", "TEXT", condition=not args.json, indent=0)
            ptprinthelper.ptprint("\n    ".join(value), "TEXT", condition=not args.json, indent=4)
            ptprinthelper.ptprint(f" ", "TEXT", condition=not args.json)#
    else:
        ptprinthelper.ptprint("Not found", "TEXT", not args.json, filehandle=args.file_handle)

def _print_title(title, args, index=0):
    if title == "regex":
        title = "REGEX SEARCH"
    if args.file_handle and index > 0:
        args.file_handle.write("\n")
    #ptprinthelper.ptprint(f'\n{ptprinthelper.get_colored_text(title.upper().replace("_", " "), color="TITLE")}{"" * len(title)}', "", filehandle=args.file_handle, condition=not args.json)
    ptprinthelper.ptprint(f'\n{ptprinthelper.get_colored_text(title.upper().replace("_", " "), color="TITLE")}\n{"-" * len(title)}', "", filehandle=args.file_handle, condition=not args.json)
    #ptprinthelper.ptprint(f'{ptprinthelper.get_colored_text(title.upper().replace("_", " "), color="TITLE")}', "TITLE", filehandle=args.file_handle, condition=not args.json, newline_above=True)


def _get_endl(list_of_results, index, args):
    """Add space if not last record"""
    if args.grouping and list_of_results[index] != list_of_results[-1]:
        ptprinthelper.ptprint(f" ", "", filehandle=args.file_handle, condition=not args.json)


def _check_if_next(list_of_results, index):
    try:
        endl = "\n" if list_of_results[index+1] else ""
    except Exception:
        endl = ""
    return endl


def _print_parsed_urls(list_of_results, index, args):
    if not list_of_results[index]["internal_urls_with_parameters"]:
        ptprinthelper.ptprint("Not found", "", not args.json, filehandle=args.file_handle)
    elif type(list_of_results[index]["internal_urls_with_parameters"]) == str: # If error msg (eg. cannot search file)
        ptprinthelper.ptprint(list_of_results[index]["internal_urls_with_parameters"], "", filehandle=args.file_handle, condition=not args.json)
    else:
        for url in list_of_results[index]["internal_urls_with_parameters"] or []:
            ptprinthelper.ptprint(f"URL: {url['url']}", "", filehandle=args.file_handle, condition=not args.json,)
            ptprinthelper.ptprint(f"Parameters:", "", filehandle=args.file_handle, condition=not args.json)
            for parameter in url['parameters']:
                ptprinthelper.ptprint(f'          {parameter}', "", condition=not args.json, filehandle=args.file_handle, end="\n")
            if url != list_of_results[index]["internal_urls_with_parameters"][-1]: # Add space if not last
                ptprinthelper.ptprint(f" ", "", filehandle=args.file_handle, condition=not args.json)


def _print_comments(list_of_results, index, args):
    if not any(list_of_results[index]["comments"].values()):
        ptprinthelper.ptprint(f"Not found", "", filehandle=args.file_handle, condition=not args.json)
    else:
        for key in list_of_results[index]["comments"].keys():
            if list_of_results[index]["comments"][key]:
                #ptprinthelper.ptprint(ptprinthelper.get_colored_text(key.upper(), "TITLE"), filehandle=args.file_handle, condition=not args.json)
                ptprinthelper.ptprint('\n'.join(list_of_results[index]["comments"][key]), "", filehandle=args.file_handle, condition=not args.json)


def _print_metadata(list_of_results, index, args):
    longest_key, _ = max(list_of_results[index]["metadata"].items(), key=lambda x: len(x[0]))
    for key, value in list_of_results[index]["metadata"].items():
        if type(value) is list:
            value = ', '.join(map(str, value))
        else:
            value = str(value).replace("\n", "\\n")
        ptprinthelper.ptprint(f"{key}{' '*(len(longest_key)-len(key))}: {', '.join(value) if type(value) is list else value}", "", filehandle=args.file_handle, condition=not args.json)


def _print_forms(list_of_results, index, args):
    if args.grouping_complete:
        if not list_of_results[0]["forms"]:
            ptprinthelper.ptprint("Not found", "", filehandle=args.file_handle, condition=not args.json)
        else:
            _pretty_print_forms(list_of_results, index, args)
    else:
        if not list_of_results[index]["forms"]:
            ptprinthelper.ptprint("Not found", "", filehandle=args.file_handle, condition=not args.json)
        elif type(list_of_results[index]["forms"]) == str:
            ptprinthelper.ptprint(list_of_results[index]["forms"], "", filehandle=args.file_handle, condition=not args.json)
        else:
            _pretty_print_forms(list_of_results, index, args)


def _print_current_url(list_of_results, index, args):
    ptprinthelper.ptprint(ptprinthelper.get_colored_text(f"{list_of_results[index]['url']}", 'INFO'), "", not args.json, filehandle=args.file_handle)


def _get_data_type(title: str):
    """
    Returns an empty data structure appropriate for the given title/type.

    Parameters:
        title (str): The type of data (e.g., 'metadata', 'forms', 'comments', 'google_keys', etc.)

    Returns:
        dict or set: An empty data structure for aggregating results of this type.
            - 'metadata' -> {'metadata': {}}
            - 'internal_urls_with_parameters' -> {'internal_urls_with_parameters': []}
            - 'forms' -> {'forms': []}
            - 'comments' -> {'comments': {'html': [], 'js': [], 'css': []}}
            - 'google_keys' -> {'google_keys': {}}
            - Any other title -> set()
    """
    if title == "metadata":
        merged_result = {"metadata": {}}
    elif title == "internal_urls_with_parameters":
        merged_result = {"internal_urls_with_parameters": []}
    elif title == "forms":
        merged_result = {"forms": list()}
    elif title == "comments":
        merged_result = {"comments": {"html": [], "js": [], "css": []}}
    elif title == "google_keys":
        merged_result = {"google_keys": {}}
    elif title == "regex":
        merged_result = {"regex": {}}
    else:
        merged_result = set()
    return merged_result


def _pretty_print_forms(list_of_results, index, args):
    for idx, form in enumerate(list_of_results[index]["forms"]):
        for key, value in form.items():
            space = 0 if key == "form_name" else 9
            if value == '':
                value = "''"
            if key in ["inputs", "selects"]:
                if form[key]:
                    ptprinthelper.ptprint(" ", "", filehandle=args.file_handle, condition=not args.json)
                if not form[key]:
                    continue
                ptprinthelper.ptprint(f"{' '*space}{key.title()}:", "", filehandle=args.file_handle, condition=not args.json)
                space += len(key)
                for idx2, dictionary in enumerate(form[key]):
                    for key2, value2 in dictionary.items():
                        if not value2 and value2 is not None:
                            value2 = "''"
                        if key2 == "options":
                            ptprinthelper.ptprint(f"{' '*space}{key2.title()}:", "", filehandle=args.file_handle, condition=not args.json)

                            space += len(key)
                            for option in dictionary[key2]:
                                if not option and option is not None:
                                    option = "''"
                                ptprinthelper.ptprint(f"{' '*space}{option}", "", filehandle=args.file_handle, condition=not args.json)
                            if args.grouping_complete and form != list_of_results[index]["forms"][-1]:
                                ptprinthelper.ptprint(" ", "", filehandle=args.file_handle, condition=not args.json)
                        else:
                            ptprinthelper.ptprint(f"{' '*space}{key2.title()}: {value2}", "", filehandle=args.file_handle, condition=not args.json)
                    if idx2+1 != len(form[key]):
                        ptprinthelper.ptprint(" ", "", filehandle=args.file_handle, condition=not args.json)
            else:
                ptprinthelper.ptprint(f"{' '*space}{key.title().replace('_',' ')}: {value}", "", filehandle=args.file_handle, condition=not args.json)
        if idx+1 != len(list_of_results[index]["forms"]):
            ptprinthelper.ptprint(" ", "", filehandle=args.file_handle, condition=not args.json)


def _fill_merged_result(merged_result, list_of_results, index, title):
    """
    Merges the data from a single result into the cumulative merged_result based on the title/type.

    Parameters:
        merged_result (dict or set): The current aggregated data structure for the title.
        list_of_results (list): List of all results (each is a dict or BaseResult.data) to merge from.
        index (int): Index of the current result in list_of_results to merge.
        title (str): The type/key of data to merge (e.g., 'metadata', 'forms', 'comments', etc.).

    Returns:
        dict or set: Updated merged_result containing merged values from the current result.

    Notes:
        - For 'metadata', it merges keys and lists without duplicates.
        - For 'forms', 'internal_urls_with_parameters', 'comments', and 'google_keys',
          it extends or appends the corresponding lists/dictionaries.
        - For all other titles, it assumes a set and adds new items.
        - This function does not modify the original list_of_results.
    """
    if title == "internal_urls_with_parameters":
        for result_dict in list_of_results[index]["internal_urls_with_parameters"] or []:
            if result_dict not in merged_result["internal_urls_with_parameters"]:
                merged_result["internal_urls_with_parameters"].append(result_dict)

    elif title == "metadata":
        if list_of_results[index].get("metadata"):
            for key, value in list_of_results[index]["metadata"].items():
                if key not in merged_result["metadata"]:
                    merged_result["metadata"][key] = value

                elif isinstance(merged_result["metadata"][key], list):
                    if isinstance(value, list):
                        merged_result["metadata"][key].extend([val for val in value if val not in merged_result["metadata"][key]])
                    else:
                        if value not in merged_result["metadata"][key]: merged_result["metadata"][key].append(value)
                else:
                    if isinstance(value, list):
                        merged_result["metadata"][key] = [merged_result["metadata"][key]]
                        merged_result["metadata"][key].extend([val for val in value if val not in merged_result["metadata"][key]])
                    else:
                        merged_result["metadata"][key] = [merged_result["metadata"][key]]
                        if value not in merged_result["metadata"][key]: merged_result["metadata"][key].append(value)

    elif title == "forms":
        for form in list_of_results[index]["forms"] or []:
            form_without_value_keys = forms.pop_value_key_from_form(form)
            if form_without_value_keys not in merged_result["forms"]:
                merged_result["forms"].append(form_without_value_keys)

    elif title == "comments":
        for key, value_list in (list_of_results[index].get("comments") or {}).items():
            merged_result["comments"][key].extend(value_list)
            merged_result["comments"][key] = list(set(merged_result["comments"][key]))

    elif title == "google_keys":
        merged_result.setdefault("google_keys", {})
        for key, value_list in (list_of_results[index].get("google_keys") or {}).items():
            merged_result["google_keys"].setdefault(key, []).extend(value_list)

    elif title == "regex":
        found_texts = list_of_results[index].get("regex", [])
        url = list_of_results[index].get("url", "Unknown URL")
        for text in found_texts:
            if text not in merged_result["regex"]:
                merged_result["regex"][text] = set()
            merged_result["regex"][text].add(url)

    else:
        if list_of_results[index].get(title):
            for i in list_of_results[index][title]:
                merged_result.add(i)

    return merged_result
