from dataclasses import dataclass
from typing import TypedDict

import pandas as pd
import pooch

newline = "\n"


class _File(TypedDict):
    filename: str
    known_hash: str
    note: str


class _PRIMAPHIST_2_Release(dict):

    def __init__(
        self,
        name: str,
        version: str,
        published: str,
        doi: str,
        citation: str,
        doi_article: str,
        citation_article: str,
        files: dict[str, _File],
        license: str = "CC BY 4.0",
    ):
        self.name = name
        self.version = version
        self.published = published
        self.doi = doi
        self.citation = citation
        self.doi_article = doi_article
        self.citation_article = citation_article
        self.files = files
        self.license = license

        for key, datafile in files.items():
            self[key] = PRIMAPHIST_2_File(
                filename=datafile["filename"],
                known_hash=datafile["known_hash"],
                note=datafile["note"],
                release=self,
            )

    def __repr__(self):
        return f"""{self.name}

License: {self.license}

https://doi.org/{self.doi}

Recommended citation:

{self.citation_article}

{self.citation}

Files:

{newline.join([f"{k} - {f['filename']}" for k, f in self.files.items()])}
        """


@dataclass
class PRIMAPHIST_2_File:
    filename: str
    known_hash: str
    note: str
    release: object

    def __repr__(self):
        return f"""{self.release.name}

License: {self.release.license}

https://doi.org/{self.release.doi}

Recommended citation:

{self.release.citation_article}

{self.release.citation}

File: {self.filename}

{self.note}"""

    def to_dataframe(self):
        full_path = pooch.retrieve(
            path=pooch.os_cache("openclimatedata/primap-hist"),
            url=f"doi:{self.release.doi}/{self.filename}",
            known_hash=self.known_hash,
            progressbar=True,
        )
        if self.release.version >= "2.3":
            dtypes = {
                "source": "category",
                "scenario (PRIMAP-hist)": "category",
                "provenance": "category",
                "area (ISO3)": "category",
                "entity": "category",
                "unit": "category",
                "category (IPCC2006_PRIMAP)": "category",
            }
        else:
            dtypes = {
                "source": "category",
                "scenario": "category",
                "provenance": "category",
                "area": "category",
                "entity": "category",
                "unit": "category",
                "category": "category",
            }
        return pd.read_csv(full_path, dtype=dtypes)

    def to_long_dataframe(self):
        df = self.to_dataframe()

        # Pre 2.5 provenance not included.
        if "provenance" not in df.columns:
            df["provenance"] = pd.Series(dtype="category")
        # Changed column names in 2.3
        if self.release.version >= "2.3":
            id_vars = [
                "source",
                "scenario (PRIMAP-hist)",
                "provenance",
                "area (ISO3)",
                "entity",
                "unit",
                "category (IPCC2006_PRIMAP)",
            ]
        else:
            id_vars = [
                "scenario",
                "provenance",
                "country",
                "category",
                "entity",
                "unit",
            ]

        df = df.melt(
            id_vars=id_vars,
            var_name="year",
            value_name="value",
        )
        df.year = df.year.astype("int32")
        return df

    def to_ocd(self):
        """Long DataFrame with all column names shortened."""
        df = self.to_long_dataframe()
        if self.release.version >= "2.3":
            df = df.rename(
                columns={
                    "scenario (PRIMAP-hist)": "scenario",
                    "area (ISO3)": "code",
                    "category (IPCC2006_PRIMAP)": "category",
                }
            )
        else:
            df = df.rename(columns={"country": "code"})
        if self.release.version <= "2.2":
            # df.category = df.category.astype(str)
            df.category = df.category.cat.rename_categories(
                {
                    "IPCM0EL": "M.0.EL",
                    "IPCMAG": "M.AG",
                    "IPCMAGELV": "M.AG.ELV",
                    "IPC1": "1",
                    "IPC1A": "1.A",
                    "IPC1B": "1.B",
                    "IPC1B1": "1.B.1",
                    "IPC1B2": "1.B.2",
                    "IPC1B3": "1.B.3",
                    "IPC1C": "1.C",
                    "IPC2": "2",
                    "IPC2A": "2.A",
                    "IPC2B": "2.B",
                    "IPC2C": "2.C",
                    "IPC2D": "2.D",
                    "IPC2E": "2.E",
                    "IPC2F": "2.F",
                    "IPC2G": "2.G",
                    "IPC2H": "2.H",
                    "IPC3A": "3.A",
                    "IPC4": "4",
                    "IPC5": "5",
                }
            )

            # Use entity style of >=2.3
            df.entity = df.entity.cat.rename_categories(
                {
                    "FGASES": "FGASES (SARGWP100)",
                    "FGASESAR4": "FGASES (AR4GWP100)",
                    "HFCS": "HFCS (SARGWP100)",
                    "HFCSAR4": "HFCS (AR4GWP100)",
                    "PFCS": "PFCS (SARGWP100)",
                    "PFCSAR4": "PFCS (AR4GWP100)",
                    "KYOTOGHG": "KYOTOGHG (SARGWP100)",
                    "KYOTOGHGAR4": "KYOTOGHG (AR4GWP100)",
                }
            )
        return df
