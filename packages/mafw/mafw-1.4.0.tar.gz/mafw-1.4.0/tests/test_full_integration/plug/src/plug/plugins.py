#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
This is the module that will be exposed via the entry point declaration.

Make sure to have all processors that you need to export in the list.
"""

from plug.db_model import Detector
from plug.plug_processor import Analyser, GenerateDataFiles, PlugImporter, PlugPlotter

import mafw


@mafw.mafw_hookimpl
def register_processors() -> list[mafw.processor.Processor]:
    return [GenerateDataFiles, PlugImporter, Analyser, PlugPlotter]


@mafw.mafw_hookimpl
def register_standard_tables() -> list[mafw.db.std_tables.StandardTable]:
    return [Detector]
