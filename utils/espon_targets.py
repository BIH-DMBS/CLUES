import re

# Names of the folders and files of the ESPON indicators.
#
# This module is used by the snakefile (to know which files will be created) and by the download
# (utils/espon.py), so that both always agree. It has no dependencies on purpose.


def sanitize_filename(filename):
    # remove everything that is not a letter, digit, dot, blank, underscore or minus, blanks become underscores
    sanitized_filename = re.sub(r'[^a-zA-Z0-9. _-]', '', filename)
    return sanitized_filename.replace(' ', '_')


def espon_targets(parameters, filename_length):
    """
    One entry per indicator of the ESPON configuration:
        folder     name of the folder (from the dimension of the indicator)
        name       name of the csv file without '.csv' (from the name of the indicator)
        feature    the entry of the indicator in the configuration (id, name, urls)
        dimension  the dimension as given in the configuration

    Folder and file names are shortened to filename_length characters. Different indicators can have the
    same name (e.g. 'Deaths - age group 0-4' exists with two ids). The first one keeps the plain name,
    the following ones get the id of the indicator appended ('..._id97'), so no indicator is lost.
    """
    targets = []
    used = set()
    for variable in parameters['variables']:
        folder = sanitize_filename(str(variable['dimension']))[0:filename_length]
        for feature in variable['features']:
            name = sanitize_filename(feature['name'])[0:filename_length]
            if (folder, name) in used:
                suffix = f"_id{feature['id']}"
                name = name[0:filename_length - len(suffix)] + suffix
            used.add((folder, name))
            targets.append({'folder': folder, 'name': name, 'feature': feature, 'dimension': variable['dimension']})
    return targets


def find_target(parameters, filename_length, folder, name):
    # the entry of espon_targets for a folder and file name, None if there is none
    for target in espon_targets(parameters, filename_length):
        if target['folder'] == folder and target['name'] == name:
            return target
    return None
