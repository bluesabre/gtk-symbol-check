# C GTK/GDK Symbol Versions Check

import os
import urllib.request

import argparse

MIN_GTK_VERSION = "3.12.0"
gtk_major_version = 3
gtk_minor_version = 12
hide_not_found = False


class GtkSymbol():
    """GtkSymbol class that stores name, min, and max versions."""
    def __init__(self, name, min_version=(3, 0),
                max_version=(3, 12)):
        self.symbol_name = name
        self.minimum_gtk_version = min_version
        self.maximum_gtk_version = max_version

    def check_version(self, major_version, minor_version):
        """Compare request version with symbols limits. Return -1 if symbol
        is too new, 1 if too old, 0 if just right."""
        major, minor = self.minimum_gtk_version
        if (major > major_version) or (major == major_version and
                                       minor > minor_version):
            return -1

        major, minor = self.maximum_gtk_version
        if (major < major_version) or (minor < minor_version):
            return 1

        return 0

    def get_min(self):
        return self.minimum_gtk_version

    def get_max(self):
        return self.maximum_gtk_version

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.symbol_name == other.symbol_name)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "%s (MIN: %s, MAX: %s)" % (self.symbol_name,
                                            str(self.minimum_gtk_version),
                                            str(self.maximum_gtk_version))


class GtkSymbolListing():
    def __init__(self):
        self.source_dir = os.getcwd()
        while True:
            major, minor = self.check_api_versions()
            if minor > 12:
                break
            else:
                if not self.get_api_documents(major, minor):
                    break
        self.symbols = self.get_symbols()

    def check_api_versions(self):
        """Check if API documentation has been downloaded.
        Return earliest needed version."""
        version_major = 3
        version_minor = 0
        while version_minor <= 12:
            for filename in ['api-index-full.html',
                             'api-index-deprecated.html',
                             'gtkobjects.html']:
                if not os.path.exists(os.path.join(self.source_dir,
                                      'developer.gnome.org', 'gtk3', '%i.%i' %
                                      (version_major, version_minor),
                                      filename)):
                    return (version_major, version_minor)
            version_minor += 2
        return (version_major, version_minor)

    def get_api_documents(self, version_major, version_minor):
        print(("Getting API documents for GTK %i.%i ..." % (version_major,
                                                            version_minor)))
        for filename in ['api-index-full.html',
                         'api-index-deprecated.html',
                         'gtkobjects.html']:
            if not os.path.exists(os.path.join(self.source_dir,
                                  'developer.gnome.org', 'gtk3', '%i.%i' %
                                  (version_major, version_minor), filename)):
                download = "https://developer.gnome.org/gtk3/%i.%i/%s" % \
                            (version_major, version_minor, filename)
                download_dir = os.path.join(self.source_dir,
                            "developer.gnome.org/gtk3/%i.%i" %
                            (version_major, version_minor))
                if not os.path.isdir(download_dir):
                    os.makedirs(download_dir)
                local_filename = os.path.join(download_dir, filename)
                try:
                    urllib.request.urlretrieve(download,
                        filename=os.path.join(self.source_dir, local_filename))
                except Exception:
                    return False
        return True

    def parse_object_html(self, filename):
        deprecated = False
        available_objects = list()
        deprecated_objects = list()
        with open(filename, 'r') as open_file:
            for line in open_file.readlines():
                if "chapter" in line and "DeprecatedObjects.html" in line:
                    deprecated = True
                if 'class="refentrytitle' in line:
                    line = line.split('html">')[1].split('<')[0]
                    if line.startswith("Gtk"):
                        symbol = line.split()[0]
                        if deprecated:
                            deprecated_objects.append(symbol)
                        else:
                            available_objects.append(symbol)
        return available_objects, deprecated_objects

    def parse_symbol_html(self, filename):
        symbols = list()
        with open(filename, 'r') as open_file:
            for line in open_file.readlines():
                if 'title=' in line:
                    line = line.split('title=')[1].split('>')[0]
                    line = line.replace('\xc2\xa0', ' ')
                    if "()" in line:
                        symbol = line.split()[0][1:].strip()
                        symbols.append(symbol)
        return symbols

    def get_available_symbols(self):
        version_major = 3
        version_minor = 0
        symbol_dict = dict()
        while version_minor <= 12:
            version_key = "%i.%i" % (version_major, version_minor)
            filename = os.path.join(self.source_dir,
                                    "developer.gnome.org/gtk3/%s/%s" %
                                    (version_key, 'api-index-full.html'))
            symbol_dict[version_key] = self.parse_symbol_html(filename)
            filename = os.path.join(self.source_dir,
                                    "developer.gnome.org/gtk3/%s/%s" %
                                    (version_key, 'gtkobjects.html'))
            symbol_dict[version_key] += self.parse_object_html(filename)[0]
            version_minor += 2
        return symbol_dict

    def get_deprecated_symbols(self):
        version_major = 3
        version_minor = 0
        symbol_dict = dict()
        while version_minor <= 12:
            version_key = "%i.%i" % (version_major, version_minor)
            filename = os.path.join(self.source_dir,
                                    "developer.gnome.org/gtk3/%s/%s" %
                                    (version_key, 'api-index-deprecated.html'))
            symbol_dict[version_key] = self.parse_symbol_html(filename)
            filename = os.path.join(self.source_dir,
                                    "developer.gnome.org/gtk3/%s/%s" %
                                    (version_key, 'gtkobjects.html'))
            symbol_dict[version_key] += self.parse_object_html(filename)[1]
            version_minor += 2
        return symbol_dict

    def get_symbols(self):
        available = self.get_available_symbols()
        deprecated = self.get_deprecated_symbols()
        symbols = dict()

        version_major = 3
        version_minor = 0
        while version_minor <= 12:
            version_key = "%i.%i" % (version_major, version_minor)
            for symbol in available[version_key]:
                if symbol not in list(symbols.keys()):
                    symbols[symbol] = GtkSymbol(symbol,
                                        (version_major, version_minor),
                                        (3, 12))
            version_minor += 2

        version_major = 3
        version_minor = 12
        while version_minor <= 12 and version_minor >= 0:
            version_key = "%i.%i" % (version_major, version_minor)
            for symbol in deprecated[version_key]:
                if symbol in list(symbols.keys()):
                    symbols[symbol].maximum_gtk_version = (version_major,
                                                           version_minor)
                else:
                    symbols[symbol] = GtkSymbol(symbol,
                                        (gtk_major_version, 0),
                                        (version_major, version_minor))
            version_minor -= 2

        return symbols

    def check_available_symbol(self, symbol_name, major_version, minor_version):
        """Return True if symbol matches provided constraints"""
        try:
            symbol = self.symbols[symbol_name]
            # Check if available.
            result = symbol.check_version(major_version, minor_version)
            if result == -1:
                print (("Symbol [%s] was introduced in GTK %s" %
                        (symbol_name, str(symbol.get_min()))))
                return False

            # Check if deprecated
            elif result == 1:
                print(("Symbol [%s] has been deprecated since GTK %s" %
                       (symbol_name, str(symbol.get_max()))))
                return False

            return True
        except Exception:
            if hide_not_found:
                return False
            print(("Symbol [%s] was not found in the API documents" %
                    symbol_name))
            return False


class AnotherGtkSymbol():
    """GtkSymbol class used for storage and comparison."""
    def __init__(self, symbol, min_version):
        self.symbol = symbol
        self.min_version = min_version

    def __str__(self):
        return "%s (%s)" % (self.symbol, self.min_version)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.symbol == other.symbol and
                self.min_version == other.min_version)

    def __ne__(self, other):
        return not self.__eq__(other)


def get_filenames(source_dir):
    """Return a list of the source filenames from the source directory."""
    source_files = list()
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            if filename.endswith(".c") or filename.endswith(".h") \
                    or filename.endswith('.glade') or filename.endswith('.ui'):
                source_files.append(os.path.join(root, filename))
    return source_files


def parse_c_file(filename):
    """Parse a C source or header file and return a list of the found
    symbols."""
    #print(("Processing: %s" % filename))
    symbols = list()
    with open(filename, 'r') as open_file:
        for line in open_file.readlines():
            line = line.strip()
            if line.startswith("#if") or \
                    line.startswith("#else") or \
                    line.startswith("endif") or \
                    line.startswith("#include") or \
                    line.startswith("#define"):
                pass
            else:
                #for library in ['gtk', 'gdk', ' g_']:
                for library in ['gtk', 'Gtk']:
                    #if library in lowercase:
                    if library in line:
                        line = line.replace('(', ' ')
                        line = line.replace(')', ' ')
                        line = line.replace(':', ' ')
                        line = line.replace("!", "")
                        line = line.replace(",", " ")
                        line = line.replace("#", " ")
                        line = line.replace(".", " ")
                        line = line.replace("*", " ")
                        items = line.split()
                        for item in items:
                            if item.startswith(library):
                                symbol = item
                                if symbol not in symbols:
                                    symbols.append(symbol)
    #print(("... found %i symbols." % len(symbols)))
    return symbols


def parse_glade_file(filename):
    """Parse a glade file and return a list of the found symbols."""
    symbols = list()
    with open(filename, 'r') as open_file:
        for line in open_file.readlines():
            if "object class" in line:
                symbol = line.split('"')[1].split('"')[0]
                if symbol not in symbols:
                    symbols.append(symbol)
    return symbols


def get_symbols(source_dir):
    """Retrieve the list of symbols from the source directory."""
    symbols = list()
    for filename in get_filenames(source_dir):
        if filename.endswith('.c') or filename.endswith('.h'):
            for symbol in parse_c_file(filename):
                if symbol not in symbols:
                    symbols.append(symbol)
        elif filename.endswith('.glade') or filename.endswith('.ui'):
            for symbol in parse_glade_file(filename):
                if symbol not in symbols:
                    symbols.append(symbol)
    return symbols


def configure_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir",
            help="Source directory where project files are stored.")
    parser.add_argument("--gtk_version",
                        help="Specify GTK version to validate.")
    parser.add_argument("--hide-not-found", action="store_true",
                        help="Do not display undocumented symbols.")
    return parser

if __name__ == "__main__":
    parser = configure_parser()

    args = parser.parse_args()
    if args.gtk_version is not None:
        gtk_major_version, gtk_minor_version = args.gtk_version.split('.')
        gtk_major_version = int(gtk_major_version)
        gtk_minor_version = int(gtk_minor_version)

    if args.hide_not_found is not None:
        hide_not_found = args.hide_not_found

    listing = GtkSymbolListing()

    for symbol in get_symbols(args.source_dir):
        listing.check_available_symbol(symbol,
                                       gtk_major_version, gtk_minor_version)