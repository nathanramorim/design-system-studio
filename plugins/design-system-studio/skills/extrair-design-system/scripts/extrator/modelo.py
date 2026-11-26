"""Modelo: o resultado completo de uma extração, lido pelos geradores de `saida/`."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .componentes import Componente
from .cores import Paleta
from .marca import Ativo
from .medidas import Medidas
from .tipografia import Tipografia


@dataclass
class Extracao:
    url: str
    nome: str
    data: dt.date
    paleta: Paleta
    tipografia: Tipografia
    medidas: Medidas
    componentes: list[Componente]
    ativos: list[Ativo]
    folhas: int
    por_import: int
    regras: int
    captura: str | None = None
    avisos: list[str] = field(default_factory=list)

    def ativo(self, papel: str) -> Ativo | None:
        return next((a for a in self.ativos if a.papel == papel), None)
