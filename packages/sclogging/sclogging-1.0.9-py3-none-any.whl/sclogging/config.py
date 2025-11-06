"""Settings config"""

# *****************************************************************************
#  MIT License                                                                *
#                                                                             *
#  Copyright (c) 2025 sshimek42                                               *
#                                                                             *
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#  The above copyright notice and this permission notice (including the next paragraph) shall be included in all copies or substantial portions of the Software.
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# *****************************************************************************

from os.path import dirname, exists, join

from dynaconf import Dynaconf, Validator, loaders
from dynaconf.utils.boxing import DynaBox

module_path = dirname(__file__)

settings_file = join(module_path, "settings.toml")

if exists(settings_file):
    settings = Dynaconf(envvar_prefix="DYNACONF", settings_file=settings_file)

    settings.validators.register(
        Validator(
            "logging_auto_create_dir",
            "logging_log_to_file",
            is_type_of=bool,
        ),
        Validator(
            "logging_path",
            "logging_ext",
            "spacer",
            "spacer_color",
            is_type_of=str,
        ),
        Validator(
            "specific_loggers",
            is_type_of=dict,
        ),
    )
    settings.validators.validate()

else:
    settings = ""


def write_config(config_data: dict) -> None:
    """Writes config to file"""
    loaders.write(settings_file, DynaBox(config_data).to_dict())
