import shutil
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pikepdf
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTPage
from podder_task_foundation.objects.object import Object


class PDF(Object):
    supported_extensions = [".pdf"]
    type = "pdf"
    default_extension = ".pdf"

    def __init__(self,
                 data: Optional[Union[Path, pikepdf.Pdf]] = None,
                 path: Optional[Path] = None,
                 name: Optional[str] = None,
                 *args):

        if isinstance(data, Path) and path:
            path = data
            data = None

        self._temporary_directory_object = tempfile.TemporaryDirectory(
            prefix=name)
        copied_file_path = Path(
            self._temporary_directory_object.name).joinpath(path.name)
        shutil.copy(path, copied_file_path)

        self._single_page_files: Dict[int, Path] = {}
        self._partial_page_files: Dict[Tuple[int], Path] = {}
        self._pdfminer_pages: Dict[int, LTPage] = {}
        self._page_count = -1
        self._laparams = None
        super().__init__(data, copied_file_path, name)

    def __del__(self):
        if self._temporary_directory_object is not None:
            self._temporary_directory_object.cleanup()

    def __repr__(self):
        return "<PDF: {}>".format(str(self.path))

    def __str__(self):
        return "<PDF: {}>".format(str(self.path))

    def _lazy_load(self):
        self._data = pikepdf.Pdf.open(self.path)

    def get_laparams(self) -> Optional[LAParams]:
        return self._laparams

    def set_laparams(self, laparams=Optional[LAParams]):
        self._laparams = laparams

    @property
    def page_count(self) -> int:
        if self._page_count >= 0:
            return self._page_count

        self._page_count = len(self.data.pages)
        return self._page_count

    def save(self,
             path: Path,
             encoding: Optional[str] = 'utf-8',
             indent: Optional[int] = None) -> bool:
        shutil.copy(self.path, path)
        return True

    def save_single_page(self, index: int) -> Path:
        if index in self._single_page_files:
            return self._single_page_files[index]

        if len(self.data.pages) == 1 and index == 0:
            return self.path

        path = Path(self._temporary_directory_object.name).joinpath(
            "single_page_{}.pdf".format(index))
        new_pdf = pikepdf.new()
        new_pdf.pages.append(self.data.pages[index])
        new_pdf.save(path)
        self._single_page_files[index] = path
        return path

    def save_multiple_pages(self, indices: List[int]) -> Optional[Path]:
        if len(indices) == 0:
            return None
        if len(indices) == 1:
            return self.save_single_page(indices[0])

        key = tuple(indices)
        if key in self._partial_page_files:
            return self._partial_page_files[key]

        new_pdf = pikepdf.new()
        for index in indices:
            new_pdf.pages.append(self.data.pages[index])

        path = Path(self._temporary_directory_object.name).joinpath(
            "multi_page_{}.pdf".format(",".join(
                [str(index) for index in indices])))
        new_pdf.save(path)

        self._partial_page_files[key] = path
        return path

    def get_pdfminer_objects_from_path(self, path: Path) -> [LTPage]:
        return list(extract_pages(path, laparams=self._laparams))

    def get_all_pdfminer_pages(self) -> Dict[int, LTPage]:
        if len(self._pdfminer_pages) == 0:
            pages = self.get_pdfminer_objects_from_path(self._path)
            for index, page in pages:
                self._pdfminer_pages[index] = page
            return deepcopy(self._pdfminer_pages)

        result: Dict[int, LTPage] = {}
        unprocessed_indices: List[int] = []
        for index in range(0, self.page_count):
            if index in self._pdfminer_pages:
                result[index] = deepcopy(self._pdfminer_pages[index])
            else:
                unprocessed_indices.append(index)

        if len(unprocessed_indices) > 0:
            pages = self.get_multiple_pdfminer_pages(unprocessed_indices)
            result.update(pages)

        return result

    def get_multiple_pdfminer_pages(self,
                                    indices: List[int]) -> Dict[int, LTPage]:
        result: Dict[int, LTPage] = {}
        unprocessed_indices = []
        for index in indices:
            if index in self._pdfminer_pages:
                result[index] = deepcopy(self._pdfminer_pages[index])
            else:
                unprocessed_indices.append(index)

        path = self.save_multiple_pages(unprocessed_indices)
        pages = self.get_pdfminer_objects_from_path(path)
        for index, page in enumerate(pages):
            result[unprocessed_indices[index]] = deepcopy(page)
            self._pdfminer_pages[unprocessed_indices[index]] = page

        return result

    def get_pdfminer_single_page(self, index: int) -> LTPage:
        if index in self._pdfminer_pages:
            return deepcopy(self._pdfminer_pages[index])

        path = self.save_single_page(index)
        page = self.get_pdfminer_objects_from_path(path)
        self._pdfminer_pages[index] = page[0]
        return deepcopy(page[0])
