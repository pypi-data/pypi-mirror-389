# SPDX-FileCopyrightText: 2025-present Krys Lawrence <aquarion.5.krystopher@spamgourmet.org>
# SPDX-License-Identifier: AGPL-3.0-only

# Part of the aquarion-libtts library of the Aquarion AI project.
# Copyright (C) 2025-present Krys Lawrence <aquarion.5.krystopher@spamgourmet.org>
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free Software
# Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>.

from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Final

import torch
from kokoro.model import KModel

ALIASES: Final[dict[str, str]]

class KPipeline:
    model: KModel | None
    def __init__(
        self,
        lang_code: str,
        repo_id: str | None = None,
        model: KModel | bool = True,
        trf: bool = False,
        en_callable: Callable[[str], str] | None = None,
        device: str | None = None,
    ) -> None: ...
    def load_voice(
        self, voice: str | torch.FloatTensor, delimiter: str = ","
    ) -> torch.FloatTensor: ...
    @dataclass
    class Result:
        @property
        def audio(self) -> torch.FloatTensor | None: ...

    def __call__(
        self,
        text: str | list[str],
        voice: str | None = None,
        speed: float | Callable[[int], float] = 1,
        split_pattern: str | None = r"\n+",
        model: KModel | None = None,
    ) -> Generator[KPipeline.Result, None, None]: ...
